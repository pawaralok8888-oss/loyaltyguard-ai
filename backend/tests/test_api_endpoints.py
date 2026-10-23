from datetime import date
import pytest
from backend.app.config import settings
from backend.app.models import LoyaltyAccount, RewardBatch, BalanceSnapshot


def test_api_check_and_runs_endpoints(db_session, test_user, client, frozen_clock):
    """
    Tests:
    - POST /api/accounts/{id}/check
    - GET /api/runs
    - GET /api/traces
    """
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="tc1_account",
        display_name="API Check Account",
        status="unchecked"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # 1. Trigger single check via API
    resp = client.post(f"/api/accounts/{account.id}/check")
    assert resp.status_code == 200
    run_data = resp.json()
    assert run_data["outcome"] == "success"
    check_run_id = run_data["id"]

    # 2. Query check runs
    runs_resp = client.get("/api/runs")
    assert runs_resp.status_code == 200
    runs = runs_resp.json()
    assert len(runs) >= 1
    assert runs[0]["id"] == check_run_id

    # 3. Query agent traces
    traces_resp = client.get(f"/api/traces?check_run_id={check_run_id}")
    assert traces_resp.status_code == 200
    traces = traces_resp.json()
    assert len(traces) >= 3  # plan_check, fetch_portal, validate_payload, etc.
    tool_names = [t["tool_name"] for t in traces]
    assert "fetch_portal" in tool_names


def test_api_bulk_check_shared_secret(db_session, test_user, client, frozen_clock):
    """
    Tests:
    - POST /api/checks/run rejects unauthorized requests without shared secret
    - Accepts valid shared secret header
    """
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="tc1_account",
        display_name="Bulk Check Account",
        status="unchecked"
    )
    db_session.add(account)
    db_session.commit()

    # 1. Reject without header
    unauth_resp = client.post("/api/checks/run")
    assert unauth_resp.status_code == 401

    # 2. Reject with wrong secret
    wrong_resp = client.post("/api/checks/run", headers={"X-Shared-Secret": "wrong_key"})
    assert wrong_resp.status_code == 401

    # 3. Accept with correct secret
    auth_resp = client.post("/api/checks/run", headers={"X-Shared-Secret": settings.N8N_SHARED_SECRET})
    assert auth_resp.status_code == 200
    results = auth_resp.json()
    assert len(results) >= 1


def test_api_expiries_and_calendar_endpoints(db_session, test_user, client, frozen_clock):
    """
    Tests:
    - GET /api/expiries?days=7
    - GET /api/calendar
    """
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="tc1_account",
        display_name="Calendar Test Account",
        status="verified"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    batch_1 = RewardBatch(
        loyalty_account_id=account.id,
        external_batch_id="cal_batch_1",
        reward_type="points",
        amount_remaining=250.0,
        unit="points",
        expires_at=date(2026, 10, 25)  # 4 days away
    )
    batch_2 = RewardBatch(
        loyalty_account_id=account.id,
        external_batch_id="cal_batch_2",
        reward_type="points",
        amount_remaining=500.0,
        unit="points",
        expires_at=date(2026, 11, 15)  # 25 days away
    )
    db_session.add_all([batch_1, batch_2])
    db_session.commit()

    # Query 7-day expiries
    exp_resp = client.get("/api/expiries?days=7")
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()
    assert len(exp_data) == 1
    assert exp_data[0]["external_batch_id"] == "cal_batch_1"

    # Query calendar
    cal_resp = client.get("/api/calendar")
    assert cal_resp.status_code == 200
    cal_data = cal_resp.json()
    assert len(cal_data) == 2
    # Verify days_left computed correctly (Oct 21 -> Oct 25 = 4 days)
    assert cal_data[0]["days_left"] == 4
