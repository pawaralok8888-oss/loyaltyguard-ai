import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import httpx

from backend.app.models import (
    LoyaltyAccount, RewardBatch, BalanceSnapshot,
    CheckRun, AlertProposal, AgentTrace
)
from backend.app.clock import Clock
from backend.app.agent.planner import (
    AgentRunState, LLMPlanner, DeterministicPlanner, PlannerDecision
)
from backend.app.agent.traces import record_agent_trace
from backend.app.services.retrieval import fetch_from_portal, RetrievalResult
from backend.app.services.validation import validate_portal_payload, ValidationResult
from backend.app.services.expiry import compute_expiring_batches
from backend.app.services.alerts import create_alert_proposals_for_account
from backend.app.services.verify import verify_post_run, VerificationResult


def log_trace(
    db: Session,
    check_run_id: Optional[int],
    tool_name: str,
    decision_type: str,
    explanation: str,
    input_data: Optional[Dict[str, Any]] = None,
    output_data: Optional[Dict[str, Any]] = None
) -> AgentTrace:
    return record_agent_trace(
        db=db,
        check_run_id=check_run_id,
        tool_name=tool_name,
        decision_type=decision_type,
        explanation=explanation,
        input_data=input_data,
        output_data=output_data
    )


def run_account_check(
    db: Session,
    account_id: int,
    client: Optional[httpx.Client] = None,
    scenario: Optional[str] = None,
    mock_llm_response: Optional[str] = None
) -> CheckRun:
    """
    Executes the agentic check flow via the planner loop (Section 8).
    Supports policy=fallback and policy=llm with full trace persistence.
    """
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.id == account_id).first()
    if not account:
        raise ValueError(f"LoyaltyAccount with ID {account_id} not found")

    started_at = Clock.now_utc()
    check_run = CheckRun(
        loyalty_account_id=account.id,
        started_at=started_at,
        outcome="started",
        evidence_json=None
    )
    db.add(check_run)
    db.commit()
    db.refresh(check_run)

    state = AgentRunState(
        account_id=account.id,
        provider_code=account.provider_code,
        external_mock_id=account.external_mock_id
    )

    # Maximum iterations to prevent infinite loops
    max_steps = 10
    step_count = 0

    while not state.terminated and step_count < max_steps:
        step_count += 1
        decision: Optional[PlannerDecision] = LLMPlanner.plan_next_tool(
            state=state,
            mock_llm_response=mock_llm_response
        )

        if not decision:
            break

        tool = decision.tool
        policy = decision.decision_type
        explanation = decision.explanation

        # 1. TOOL: fetch_portal or retry_fetch
        if tool in ["fetch_portal", "retry_fetch"]:
            if tool == "retry_fetch":
                state.retry_count += 1

            log_trace(
                db=db,
                check_run_id=check_run.id,
                tool_name=tool,
                decision_type=policy,
                explanation=explanation,
                input_data={
                    "provider": account.provider_code,
                    "external_id": account.external_mock_id,
                    "retry_count": state.retry_count,
                    "scenario": scenario
                }
            )

            retrieval: RetrievalResult = fetch_from_portal(
                provider_code=account.provider_code,
                external_mock_id=account.external_mock_id,
                client=client,
                scenario=scenario
            )
            state.fetch_result = retrieval

        # 2. TOOL: validate_payload
        elif tool == "validate_payload":
            log_trace(
                db=db,
                check_run_id=check_run.id,
                tool_name=tool,
                decision_type=policy,
                explanation=explanation,
                input_data={"raw_payload": state.fetch_result.data if state.fetch_result else None}
            )

            val_res: ValidationResult = validate_portal_payload(state.fetch_result.data)
            state.validation_result = val_res

        # 3. TOOL: mark_unchecked (Error handling path)
        elif tool == "mark_unchecked":
            error_code = "UNKNOWN_ERROR"
            error_msg = "Execution terminated with errors"

            if state.validation_result and not state.validation_result.is_valid:
                error_code = state.validation_result.error_code or "VALIDATION_ERROR"
                error_msg = state.validation_result.error_message or "Validation failed"
            elif state.fetch_result and not state.fetch_result.success:
                error_code = state.fetch_result.error_code or "FETCH_ERROR"
                error_msg = state.fetch_result.error_message or f"HTTP {state.fetch_result.status_code}"

            account.status = "unchecked"
            account.last_checked_at = Clock.now_utc()
            if state.validation_result and not state.validation_result.is_valid:
                account.last_error = f"VALIDATION_ERROR: {error_code}: {error_msg}"
            else:
                account.last_error = f"{error_code}: {error_msg}"

            # Mark all existing snapshots stale
            db.query(BalanceSnapshot).filter(
                BalanceSnapshot.loyalty_account_id == account.id
            ).update({"is_stale": True})

            check_run.finished_at = Clock.now_utc()
            check_run.outcome = "failed"
            check_run.error_code = error_code
            check_run.evidence_json = json.dumps({
                "status_code": state.fetch_result.status_code if state.fetch_result else 500,
                "error": error_msg,
                "retry_count": state.retry_count
            })
            db.commit()

            log_trace(
                db=db,
                check_run_id=check_run.id,
                tool_name=tool,
                decision_type=policy,
                explanation=explanation,
                output_data={"error_code": error_code, "status": "unchecked"}
            )
            state.terminated = True

        # 4. TOOL: compute_expiries
        elif tool == "compute_expiries":
            payload = state.validation_result.payload

            # Snapshot and batches persistence
            db.query(BalanceSnapshot).filter(
                BalanceSnapshot.loyalty_account_id == account.id
            ).update({"is_stale": True})

            new_snapshot = BalanceSnapshot(
                loyalty_account_id=account.id,
                total_balance=payload.total_balance,
                unit=payload.unit,
                retrieved_at=state.fetch_result.retrieved_at,
                source_reference=state.fetch_result.source_reference,
                check_run_id=check_run.id,
                is_stale=False
            )
            db.add(new_snapshot)

            # Upsert batches
            for b in payload.batches:
                existing_batch = db.query(RewardBatch).filter(
                    RewardBatch.loyalty_account_id == account.id,
                    RewardBatch.external_batch_id == b.batch_id
                ).first()

                batch_unit = b.unit or payload.unit
                reward_type = "currency" if batch_unit == "INR" else "points"

                if existing_batch:
                    existing_batch.amount_remaining = b.amount_remaining
                    existing_batch.unit = batch_unit
                    existing_batch.reward_type = reward_type
                    existing_batch.expires_at = b.expires_at
                    existing_batch.last_verified_at = state.fetch_result.retrieved_at
                else:
                    new_batch = RewardBatch(
                        loyalty_account_id=account.id,
                        external_batch_id=b.batch_id,
                        reward_type=reward_type,
                        amount_remaining=b.amount_remaining,
                        unit=batch_unit,
                        expires_at=b.expires_at,
                        last_verified_at=state.fetch_result.retrieved_at
                    )
                    db.add(new_batch)

            account.status = "verified"
            account.last_checked_at = state.fetch_result.retrieved_at
            account.last_error = None
            db.commit()

            expiring = compute_expiring_batches(
                batches=payload.batches,
                account_unit=payload.unit,
                threshold_days=7
            )
            state.expiring_items = expiring

            log_trace(
                db=db,
                check_run_id=check_run.id,
                tool_name=tool,
                decision_type=policy,
                explanation=explanation,
                output_data={"expiring_count": len(expiring)}
            )

        # 5. TOOL: propose_alert
        elif tool == "propose_alert":
            created_proposals = create_alert_proposals_for_account(
                db=db,
                user_id=account.user_id,
                loyalty_account_id=account.id,
                expiring_items=state.expiring_items
            )
            state.proposals_created = len(created_proposals)

            log_trace(
                db=db,
                check_run_id=check_run.id,
                tool_name=tool,
                decision_type=policy,
                explanation=explanation,
                output_data={"created_proposals_count": len(created_proposals)}
            )

        # 6. TOOL: verify_recheck
        elif tool == "verify_recheck":
            payload = state.validation_result.payload
            verif_res: VerificationResult = verify_post_run(
                provider_code=account.provider_code,
                external_mock_id=account.external_mock_id,
                expected_total=payload.total_balance,
                expected_batches=payload.batches,
                client=client,
                scenario=scenario
            )

            state.verification_status = verif_res.status
            check_run.verification_status = verif_res.status
            db.commit()

            log_trace(
                db=db,
                check_run_id=check_run.id,
                tool_name=tool,
                decision_type=policy,
                explanation=explanation,
                output_data={"verification_status": verif_res.status}
            )

        # 7. TOOL: explain
        elif tool == "explain":
            state.explained = True
            check_run.finished_at = Clock.now_utc()
            check_run.outcome = "success"
            check_run.evidence_json = json.dumps({
                "snapshot_balance": state.validation_result.payload.total_balance,
                "unit": state.validation_result.payload.unit,
                "batches_count": len(state.validation_result.payload.batches),
                "expiring_count": len(state.expiring_items or []),
                "proposals_created": state.proposals_created or 0,
                "verification_status": check_run.verification_status,
                "policy_used": policy
            })
            db.commit()

            log_trace(
                db=db,
                check_run_id=check_run.id,
                tool_name=tool,
                decision_type=policy,
                explanation=explanation,
                output_data={"final_outcome": "success", "verification_status": check_run.verification_status}
            )
            state.terminated = True

    return check_run
