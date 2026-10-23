from datetime import date
import pytest
from backend.app.models import (
    LoyaltyAccount, AlertProposal, BalanceSnapshot, CheckRun, NotificationEvent
)
from backend.app.services.check_runner import run_account_check
from backend.app.mock_portal.router import scenario_overrides, custom_payload_overrides


def test_boundary_window_inclusion_and_exclusion(db_session, test_user, client, frozen_clock):
    """
    Boundary test:
    - Today: 2026-10-21
    - Exactly 0 days away (2026-10-21): INCLUDED
    - Exactly 7 days away (2026-10-28): INCLUDED
    - 8 days away (2026-10-29): EXCLUDED
    - -1 days away (already expired 2026-10-20): EXCLUDED
    """
    custom_payload_overrides["shop_rewards:boundary_acc"] = {
        "account_id": "boundary_acc",
        "provider": "shop_rewards",
        "unit": "points",
        "total_balance": 1000.0,
        "batches": [
            {"batch_id": "b_expired", "amount_remaining": 100.0, "expires_at": "2026-10-20"}, # -1 day
            {"batch_id": "b_day_0", "amount_remaining": 200.0, "expires_at": "2026-10-21"},   # 0 days
            {"batch_id": "b_day_7", "amount_remaining": 300.0, "expires_at": "2026-10-28"},   # 7 days
            {"batch_id": "b_day_8", "amount_remaining": 400.0, "expires_at": "2026-10-29"}    # 8 days
        ]
    }

    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="boundary_acc",
        display_name="Boundary Test Account",
        status="unchecked"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    try:
        check_run = run_account_check(db=db_session, account_id=account.id, client=client)
        assert check_run.outcome == "success"

        proposals = db_session.query(AlertProposal).filter(
            AlertProposal.loyalty_account_id == account.id
        ).order_by(AlertProposal.amount).all()

        # Only Day 0 (200.0) and Day 7 (300.0) must be included
        assert len(proposals) == 2
        batch_amounts = [p.amount for p in proposals]
        assert 200.0 in batch_amounts
        assert 300.0 in batch_amounts
        assert 100.0 not in batch_amounts  # Expired excluded
        assert 400.0 not in batch_amounts  # Day 8 excluded
    finally:
        custom_payload_overrides.pop("shop_rewards:boundary_acc", None)


def test_malformed_negative_amount_fails_validation(db_session, test_user, client, frozen_clock):
    """
    Negative amount => validation error and account marked unchecked.
    """
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="malformed_acc",
        display_name="Negative Amount Account",
        status="verified"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    scenario_overrides["shop_rewards:malformed_acc"] = "malformed"

    try:
        check_run = run_account_check(db=db_session, account_id=account.id, client=client)
        assert check_run.outcome == "failed"
        assert account.status == "unchecked"
        assert "VALIDATION" in account.last_error
    finally:
        scenario_overrides.pop("shop_rewards:malformed_acc", None)


def test_mixed_units_rejected(db_session, test_user, client, frozen_clock):
    """
    Hard Rule 7: Mixed units never combined or accepted.
    Payload with points and INR mixed together => validation error and unchecked.
    """
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="mixed_acc",
        display_name="Mixed Units Account",
        status="verified"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    scenario_overrides["shop_rewards:mixed_acc"] = "mixed_units"

    try:
        check_run = run_account_check(db=db_session, account_id=account.id, client=client)
        assert check_run.outcome == "failed"
        assert account.status == "unchecked"
        assert "MIXED_UNITS" in check_run.error_code or "VALIDATION" in account.last_error
    finally:
        scenario_overrides.pop("shop_rewards:mixed_acc", None)


def test_verification_re_read_failure(db_session, test_user, client, frozen_clock, monkeypatch):
    """
    Verification re-read failure clearly marked; no false success.
    """
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="tc1_account",
        display_name="ShopRewards Verify Fail",
        status="unchecked"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # Allow first fetch to succeed, but simulate re-read failing (e.g. portal goes down right after check)
    call_count = {"count": 0}
    original_get = client.get

    def patched_get(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] > 1:
            # Re-read step fails with 504
            from fastapi import Response
            resp = Response(content="Gateway Timeout", status_code=504)
            resp.status_code = 504
            return resp
        return original_get(*args, **kwargs)

    monkeypatch.setattr(client, "get", patched_get)

    check_run = run_account_check(db=db_session, account_id=account.id, client=client)
    assert check_run.verification_status == "verification_failed"
    assert check_run.verification_status != "verified"


def test_pending_alert_cannot_send(db_session, test_user, test_account, client, frozen_clock):
    """
    Hard Rule 5: Pending alerts NEVER send without human approval.
    """
    proposal = AlertProposal(
        user_id=test_user.id,
        loyalty_account_id=test_account.id,
        threshold_days=7,
        expiry_date=date(2026, 10, 28),
        amount=250.0,
        unit="points",
        status="pending",
        dedupe_key="test_pending_key"
    )
    db_session.add(proposal)
    db_session.commit()
    db_session.refresh(proposal)

    # Attempt to send directly without approval
    resp = client.post(f"/api/alerts/{proposal.id}/send")
    assert resp.status_code == 400
    assert "pending explicit human approval" in resp.json()["detail"]

    # Verify no notification event was created
    events = db_session.query(NotificationEvent).filter(
        NotificationEvent.alert_proposal_id == proposal.id
    ).all()
    assert len(events) == 0


def test_rejected_alert_cannot_send(db_session, test_user, test_account, client, frozen_clock):
    """
    Hard Rule 5: Rejected alerts NEVER send.
    """
    proposal = AlertProposal(
        user_id=test_user.id,
        loyalty_account_id=test_account.id,
        threshold_days=7,
        expiry_date=date(2026, 10, 28),
        amount=250.0,
        unit="points",
        status="pending",
        dedupe_key="test_reject_key"
    )
    db_session.add(proposal)
    db_session.commit()
    db_session.refresh(proposal)

    # 1. Reject the proposal
    reject_resp = client.post(f"/api/alerts/{proposal.id}/reject")
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    # 2. Attempt to send rejected proposal
    send_resp = client.post(f"/api/alerts/{proposal.id}/send")
    assert send_resp.status_code == 400
    assert "rejected by operator" in send_resp.json()["detail"]

    # Verify no notification event was created
    events = db_session.query(NotificationEvent).filter(
        NotificationEvent.alert_proposal_id == proposal.id
    ).all()
    assert len(events) == 0


def test_approved_alert_sends_idempotently(db_session, test_user, test_account, client, frozen_clock):
    """
    Section 11 requirement:
    Approved => one send even if the endpoint is retried.
    """
    proposal = AlertProposal(
        user_id=test_user.id,
        loyalty_account_id=test_account.id,
        threshold_days=7,
        expiry_date=date(2026, 10, 28),
        amount=250.0,
        unit="points",
        status="pending",
        dedupe_key="test_approved_key"
    )
    db_session.add(proposal)
    db_session.commit()
    db_session.refresh(proposal)

    # 1. Approve proposal
    appr_resp = client.post(f"/api/alerts/{proposal.id}/approve")
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "approved"

    # 2. First send call
    send_1 = client.post(f"/api/alerts/{proposal.id}/send")
    assert send_1.status_code == 200
    data_1 = send_1.json()
    assert data_1["status"] == "success"
    assert data_1["is_newly_sent"] is True
    assert data_1["proposal"]["status"] == "sent"
    event_id_1 = data_1["notification_event"]["id"]

    # 3. Second send call (retry)
    send_2 = client.post(f"/api/alerts/{proposal.id}/send")
    assert send_2.status_code == 200
    data_2 = send_2.json()
    assert data_2["status"] == "success"
    assert data_2["is_newly_sent"] is False  # Idempotent repeat!
    event_id_2 = data_2["notification_event"]["id"]
    assert event_id_1 == event_id_2

    # Verify database constraint: exactly 1 notification event exists
    events = db_session.query(NotificationEvent).filter(
        NotificationEvent.alert_proposal_id == proposal.id
    ).all()
    assert len(events) == 1
    assert events[0].outcome == "sent"
