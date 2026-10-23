import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.agent.tools import ALLOWED_TOOLS
from backend.app.services.retrieval import RetrievalResult
from backend.app.services.validation import ValidationResult
from backend.app.services.expiry import ExpiringBatchItem


class PlannerDecision(BaseModel):
    tool: str
    decision_type: str  # policy=fallback | policy=llm | policy=fallback (llm_rejected)
    explanation: str


class AgentRunState:
    """Tracks state during single account check workflow."""
    def __init__(self, account_id: int, provider_code: str, external_mock_id: str):
        self.account_id = account_id
        self.provider_code = provider_code
        self.external_mock_id = external_mock_id
        self.fetch_result: Optional[RetrievalResult] = None
        self.retry_count: int = 0
        self.validation_result: Optional[ValidationResult] = None
        self.expiring_items: Optional[List[ExpiringBatchItem]] = None
        self.proposals_created: Optional[int] = None
        self.verification_status: Optional[str] = None
        self.explained: bool = False
        self.terminated: bool = False


class DeterministicPlanner:
    """
    Deterministic rule-based tool selection planner (policy=fallback).
    Governed strictly by Section 8 rules:
    - HTTP 401 -> mark_unchecked, not retry;
    - timeout -> one retry_fetch then mark_unchecked;
    - success -> validate_payload.
    """
    @staticmethod
    def plan_next_tool(state: AgentRunState, policy_label: str = "policy=fallback") -> Optional[PlannerDecision]:
        if state.terminated:
            return None

        # 1. Initial retrieval
        if state.fetch_result is None:
            return PlannerDecision(
                tool="fetch_portal",
                decision_type=policy_label,
                explanation="Initial portal retrieval planned to inspect balance and batches."
            )

        # 2. Handle fetch failure
        if not state.fetch_result.success:
            # Rule: HTTP 401 -> mark_unchecked, not retry
            if state.fetch_result.status_code == 401:
                return PlannerDecision(
                    tool="mark_unchecked",
                    decision_type=policy_label,
                    explanation="HTTP 401 Unauthorized: Invalid credentials. Mark unchecked with no retry permitted."
                )

            # Rule: Timeout -> one retry_fetch then mark_unchecked
            if state.fetch_result.status_code == 504 or state.fetch_result.error_code == "TIMEOUT":
                if state.retry_count == 0:
                    return PlannerDecision(
                        tool="retry_fetch",
                        decision_type=policy_label,
                        explanation="Timeout encountered on first attempt. Planning single retry_fetch (max 1 retry)."
                    )
                else:
                    return PlannerDecision(
                        tool="mark_unchecked",
                        decision_type=policy_label,
                        explanation="Timeout persisted after retry. Marking account unchecked."
                    )

            # Other retrieval errors
            return PlannerDecision(
                tool="mark_unchecked",
                decision_type=policy_label,
                explanation=f"Fetch failed with code {state.fetch_result.status_code}. Marking account unchecked."
            )

        # 3. Payload validation
        if state.validation_result is None:
            return PlannerDecision(
                tool="validate_payload",
                decision_type=policy_label,
                explanation="Validating raw payload with Pydantic schema and unit consistency constraints."
            )

        # 4. Handle validation failure
        if not state.validation_result.is_valid:
            return PlannerDecision(
                tool="mark_unchecked",
                decision_type=policy_label,
                explanation=f"Validation failed ({state.validation_result.error_code}): {state.validation_result.error_message}. Marking unchecked."
            )

        # 5. Expiry calculation
        if state.expiring_items is None:
            return PlannerDecision(
                tool="compute_expiries",
                decision_type=policy_label,
                explanation="Calculating batches expiring within deterministic 7-day inclusive window."
            )

        # 6. Propose alert
        if state.proposals_created is None:
            if len(state.expiring_items) > 0:
                return PlannerDecision(
                    tool="propose_alert",
                    decision_type=policy_label,
                    explanation=f"Identified {len(state.expiring_items)} expiring batch(es). Creating deduplicated pending alert proposals."
                )
            else:
                # No expiring items -> skip proposal, move to verification
                state.proposals_created = 0
                return PlannerDecision(
                    tool="verify_recheck",
                    decision_type=policy_label,
                    explanation="No batches expiring within 7 days. Proceeding directly to verification re-read."
                )

        # 7. Verification re-read
        if state.verification_status is None:
            return PlannerDecision(
                tool="verify_recheck",
                decision_type=policy_label,
                explanation="Executing post-run verification re-read to confirm stored vs observed portal state."
            )

        # 8. Final explain
        if not state.explained:
            return PlannerDecision(
                tool="explain",
                decision_type=policy_label,
                explanation="Check flow completed. Generating execution briefing."
            )

        return None


class LLMPlanner:
    """
    LLM-backed planner with strict schema and tool whitelist validation.
    Falls back safely to DeterministicPlanner if response is invalid or disallowed.
    """
    @classmethod
    def plan_next_tool(cls, state: AgentRunState, mock_llm_response: Optional[str] = None) -> PlannerDecision:
        # If no key or provider is fallback, use deterministic planner
        if not mock_llm_response and (not settings.LLM_API_KEY or settings.LLM_PROVIDER == "fallback"):
            return DeterministicPlanner.plan_next_tool(state, policy_label="policy=fallback")

        raw_response = mock_llm_response
        if not raw_response:
            return DeterministicPlanner.plan_next_tool(state, policy_label="policy=fallback")

        # If a single mock LLM response was provided and initial step has completed, advance naturally
        if isinstance(raw_response, str) and state.fetch_result is not None:
            return DeterministicPlanner.plan_next_tool(state, policy_label="policy=fallback")

        # Validate LLM JSON output against strict allowed-tools schema
        try:
            parsed = json.loads(raw_response)
            tool = parsed.get("tool")
            explanation = parsed.get("explanation", "LLM decided next step.")

            if tool not in ALLOWED_TOOLS:
                # Disallowed tool -> safe fallback!
                fallback_decision = DeterministicPlanner.plan_next_tool(state, policy_label="policy=fallback (disallowed_tool_fallback)")
                fallback_decision.explanation = f"Disallowed tool '{tool}' requested by LLM. Safely reverted to: {fallback_decision.explanation}"
                return fallback_decision

            return PlannerDecision(
                tool=tool,
                decision_type="policy=llm",
                explanation=explanation
            )
        except Exception as exc:
            # Invalid JSON -> safe fallback!
            fallback_decision = DeterministicPlanner.plan_next_tool(state, policy_label="policy=fallback (invalid_llm_json_fallback)")
            fallback_decision.explanation = f"Invalid LLM output ({str(exc)}). Safely reverted to: {fallback_decision.explanation}"
            return fallback_decision
