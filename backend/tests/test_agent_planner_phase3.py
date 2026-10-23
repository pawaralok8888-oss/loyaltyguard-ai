from datetime import date
import pytest
from backend.app.models import (
    LoyaltyAccount, CheckRun, AgentTrace, AlertProposal, RewardBatch
)
from backend.app.schemas import MockRewardBatch
from backend.app.services.verify import verify_post_run
from backend.app.services.check_runner import run_account_check
from backend.app.mock_portal.router import scenario_overrides, custom_payload_overrides
from backend.app.config import settings


def test_verify_post_run_verified_and_mismatch_outcomes(client, frozen_clock):
    """
    Requirement (2): Test verified and mismatch outcomes of verify_post_run.
    """
    # 1. Test verified outcome
    # demo_shop_01 has total 1200 with 2 batches (300 and 900)
    expected_batches = [
        MockRewardBatch(batch_id="batch_A", amount_remaining=300.0, expires_at=date(2026, 10, 25)),
        MockRewardBatch(batch_id="batch_B", amount_remaining=900.0, expires_at=date(2026, 12, 31))
    ]
    res_verified = verify_post_run(
        provider_code="shop_rewards",
        external_mock_id="demo_shop_01",
        expected_total=1200.0,
        expected_batches=expected_batches,
        client=client
    )
    assert res_verified.status == "verified"
    assert res_verified.details["total_balance"] == 1200.0

    # 2. Test mismatch outcome (total mismatch)
    res_mismatch_total = verify_post_run(
        provider_code="shop_rewards",
        external_mock_id="demo_shop_01",
        expected_total=9999.0,  # Mismatch!
        expected_batches=expected_batches,
        client=client
    )
    assert res_mismatch_total.status == "mismatch"
    assert res_mismatch_total.details["expected_total"] == 9999.0
    assert res_mismatch_total.details["observed_total"] == 1200.0

    # 3. Test mismatch outcome (batch count mismatch)
    res_mismatch_batches = verify_post_run(
        provider_code="shop_rewards",
        external_mock_id="demo_shop_01",
        expected_total=1200.0,
        expected_batches=[expected_batches[0]],  # Only 1 batch expected, 2 observed
        client=client
    )
    assert res_mismatch_batches.status == "mismatch"
    assert res_mismatch_batches.details["expected_batch_count"] == 1
    assert res_mismatch_batches.details["observed_batch_count"] == 2


def test_verification_status_stored_on_check_run(db_session, test_user, test_account, client, frozen_clock):
    """
    Requirement (5): Make sure verification status is stored on the check run record.
    """
    check_run = run_account_check(db=db_session, account_id=test_account.id, client=client)

    # Fetch fresh record from DB
    db_record = db_session.query(CheckRun).filter(CheckRun.id == check_run.id).first()
    assert db_record is not None
    assert db_record.verification_status == "verified"
    assert db_record.outcome == "success"


def test_api_approval_state_transitions(db_session, test_user, test_account, client, frozen_clock):
    """
    Requirement (3): API-level tests for approve/reject/send:
    - Send on pending returns 4xx
    - Invalid state transitions refused (e.g. approving already approved, rejecting approved)
    """
    proposal = AlertProposal(
        user_id=test_user.id,
        loyalty_account_id=test_account.id,
        threshold_days=7,
        expiry_date=date(2026, 10, 28),
        amount=250.0,
        unit="points",
        status="pending",
        dedupe_key="transition_test_key"
    )
    db_session.add(proposal)
    db_session.commit()
    db_session.refresh(proposal)

    # 1. Sending on pending must return 400
    resp_send_pending = client.post(f"/api/alerts/{proposal.id}/send")
    assert resp_send_pending.status_code == 400
    assert "pending explicit human approval" in resp_send_pending.json()["detail"]

    # 2. Approve proposal -> status is approved
    resp_approve = client.post(f"/api/alerts/{proposal.id}/approve")
    assert resp_approve.status_code == 200
    assert resp_approve.json()["status"] == "approved"

    # 3. Invalid transition: Cannot approve already approved proposal
    resp_re_approve = client.post(f"/api/alerts/{proposal.id}/approve")
    assert resp_re_approve.status_code == 400
    assert "Invalid transition" in resp_re_approve.json()["detail"]

    # 4. Invalid transition: Cannot reject an approved proposal
    resp_reject_approved = client.post(f"/api/alerts/{proposal.id}/reject")
    assert resp_reject_approved.status_code == 400
    assert "Invalid transition" in resp_reject_approved.json()["detail"]


def test_agent_timeout_one_retry_then_unchecked(db_session, test_user, client, frozen_clock):
    """
    Phase 3 test: Timeout scenario:
    One retry_fetch, then mark_unchecked on persistent timeout.
    """
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="timeout_acc",
        display_name="Timeout Test Account",
        status="verified"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    scenario_overrides["shop_rewards:timeout_acc"] = "timeout"

    try:
        check_run = run_account_check(db=db_session, account_id=account.id, client=client)

        assert check_run.outcome == "failed"
        assert account.status == "unchecked"

        # Check recorded traces
        traces = db_session.query(AgentTrace).filter(
            AgentTrace.check_run_id == check_run.id
        ).order_by(AgentTrace.id.asc()).all()

        tool_sequence = [t.tool_name for t in traces]
        # Must execute: fetch_portal -> retry_fetch -> mark_unchecked
        assert tool_sequence == ["fetch_portal", "retry_fetch", "mark_unchecked"]

        # Confirm policy=fallback was recorded
        for t in traces:
            assert "policy=fallback" in t.decision_type
    finally:
        scenario_overrides.pop("shop_rewards:timeout_acc", None)


def test_agent_401_no_retry_mark_unchecked(db_session, test_user, client, frozen_clock):
    """
    Phase 3 test: 401 scenario:
    No retry allowed; immediately marks unchecked.
    """
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="auth_fail_acc",
        display_name="401 Test Account",
        status="verified"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    scenario_overrides["shop_rewards:auth_fail_acc"] = "login_fail"

    try:
        check_run = run_account_check(db=db_session, account_id=account.id, client=client)

        assert check_run.outcome == "failed"
        assert account.status == "unchecked"

        # Check recorded traces
        traces = db_session.query(AgentTrace).filter(
            AgentTrace.check_run_id == check_run.id
        ).order_by(AgentTrace.id.asc()).all()

        tool_sequence = [t.tool_name for t in traces]
        # Must execute: fetch_portal -> mark_unchecked (NO retry_fetch!)
        assert tool_sequence == ["fetch_portal", "mark_unchecked"]
        assert "retry_fetch" not in tool_sequence

        for t in traces:
            assert "policy=fallback" in t.decision_type
    finally:
        scenario_overrides.pop("shop_rewards:auth_fail_acc", None)


def test_agent_llm_disallowed_tool_safe_fallback(db_session, test_user, test_account, client, frozen_clock):
    """
    Phase 3 test: An LLM planner returning an invalid or disallowed tool falls back safely.
    """
    # Simulate LLM returning a disallowed or hallucinated tool
    malicious_llm_output = '{"tool": "delete_all_database_records", "explanation": "Hallucinated dangerous action"}'

    check_run = run_account_check(
        db=db_session,
        account_id=test_account.id,
        client=client,
        mock_llm_response=malicious_llm_output
    )

    # Check run must NOT crash, but succeed using the safe fallback tool
    assert check_run.outcome == "success"
    assert test_account.status == "verified"

    # Check recorded traces to verify fallback flag
    traces = db_session.query(AgentTrace).filter(
        AgentTrace.check_run_id == check_run.id
    ).all()

    first_trace = traces[0]
    # Disallowed tool must have been intercepted and safe fallback recorded
    assert "disallowed_tool_fallback" in first_trace.decision_type or "policy=fallback" in first_trace.decision_type
    assert first_trace.tool_name == "fetch_portal"


def test_planner_decision_alters_execution_flow(db_session, test_user, test_account, client, frozen_clock, monkeypatch):
    """
    Check (1): Proves that check_runner executes the tool the planner returns step by step,
    and a different planner decision directly alters the actual execution flow.
    """
    from backend.app.agent.planner import LLMPlanner, PlannerDecision

    # Force planner to choose 'mark_unchecked' immediately at step 1
    def mock_plan_mark_unchecked(*args, **kwargs):
        return PlannerDecision(
            tool="mark_unchecked",
            decision_type="policy=test_override",
            explanation="Override planner directly commanded mark_unchecked."
        )

    monkeypatch.setattr(LLMPlanner, "plan_next_tool", mock_plan_mark_unchecked)

    check_run = run_account_check(db=db_session, account_id=test_account.id, client=client)

    # Outcome must be failed immediately, without fetch_portal or validate_payload being called
    assert check_run.outcome == "failed"
    assert test_account.status == "unchecked"

    traces = db_session.query(AgentTrace).filter(
        AgentTrace.check_run_id == check_run.id
    ).all()
    assert len(traces) == 1
    assert traces[0].tool_name == "mark_unchecked"
    assert traces[0].decision_type == "policy=test_override"


def test_valid_llm_planner_path(db_session, test_user, test_account, client, frozen_clock):
    """
    Check (2): Fake LLM client returns valid tool choices, covering the valid policy=llm path.
    Also confirms LLM is off by default behind env vars.
    """
    # 1. Confirm default is fallback
    assert settings.LLM_PROVIDER == "fallback"

    # 2. Fake LLM output with valid tool
    valid_llm_response = '{"tool": "fetch_portal", "explanation": "Valid LLM planned fetch_portal step."}'

    check_run = run_account_check(
        db=db_session,
        account_id=test_account.id,
        client=client,
        mock_llm_response=valid_llm_response
    )

    assert check_run.outcome == "success"
    traces = db_session.query(AgentTrace).filter(
        AgentTrace.check_run_id == check_run.id
    ).order_by(AgentTrace.id.asc()).all()

    # Step 1 must have policy=llm recorded
    assert traces[0].decision_type == "policy=llm"
    assert traces[0].tool_name == "fetch_portal"
    assert "Valid LLM planned fetch_portal" in traces[0].explanation


def test_failed_send_can_be_retried(db_session, test_user, test_account, client, frozen_clock):
    """
    Check (4): When a send attempt fails, proposal is marked failed and can be retried successfully.
    """
    from backend.app.models import NotificationEvent
    from backend.app.services.notify import send_alert_notification

    proposal = AlertProposal(
        user_id=test_user.id,
        loyalty_account_id=test_account.id,
        threshold_days=7,
        expiry_date=date(2026, 10, 28),
        amount=250.0,
        unit="points",
        status="approved",
        dedupe_key="retry_send_test_key"
    )
    db_session.add(proposal)
    db_session.commit()
    db_session.refresh(proposal)

    # 1. Simulate initial failure
    event_fail = NotificationEvent(
        alert_proposal_id=proposal.id,
        channel="simulated_in_app",
        outcome="failed",
        error_message="Simulated temporary gateway drop"
    )
    proposal.status = "failed"
    db_session.add(event_fail)
    db_session.commit()

    # 2. Send endpoint is retried
    resp = client.post(f"/api/alerts/{proposal.id}/send")
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "success"
    assert res_data["proposal"]["status"] == "sent"

    # 3. Confirm only 1 NotificationEvent exists in DB (updated from failed to sent)
    events = db_session.query(NotificationEvent).filter(
        NotificationEvent.alert_proposal_id == proposal.id
    ).all()
    assert len(events) == 1
    assert events[0].outcome == "sent"
