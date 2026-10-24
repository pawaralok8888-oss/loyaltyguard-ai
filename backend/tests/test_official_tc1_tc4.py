from datetime import date
import pytest
from backend.app.models import (
    User, LoyaltyAccount, AlertProposal, BalanceSnapshot,
    RewardBatch, CheckRun
)
from backend.app.services.check_runner import run_account_check
from backend.app.mock_portal.router import scenario_overrides


def test_tc1_seven_day_expiry(db_session, test_user, client, frozen_clock):
    """
    TC1 7-day expiry:
    250 points expire 2026-10-28, check on Oct 21 =>
    exactly one pending proposal, amount 250, correct date, not auto-sent.
    """
    # 1. Create account configured for tc1_account
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="tc1_account",
        display_name="ShopRewards TC1",
        status="unchecked"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # 2. Run the check flow
    check_run = run_account_check(db=db_session, account_id=account.id, client=client)

    # 3. Assertions
    assert check_run.outcome == "success"
    assert account.status == "verified"

    proposals = db_session.query(AlertProposal).filter(
        AlertProposal.loyalty_account_id == account.id
    ).all()

    # Exactly one proposal
    assert len(proposals) == 1
    p = proposals[0]

    # Verify amount and date
    assert p.amount == 250.0
    assert p.expiry_date == date(2026, 10, 28)
    assert p.unit == "points"
    assert p.threshold_days == 7

    # Critical rule: Status must be pending and NOT auto-sent
    assert p.status == "pending"
    assert p.sent_at is None
    assert p.approved_at is None


def test_tc2_unchanged_balance_deduplication(db_session, test_user, client, frozen_clock):
    """
    TC2 unchanged balance:
    Run the same check twice (also after simulated restart) =>
    no second proposal or notification.
    """
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="tc1_account",
        display_name="ShopRewards TC2",
        status="unchecked"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # First check run
    run_1 = run_account_check(db=db_session, account_id=account.id, client=client)
    assert run_1.outcome == "success"

    initial_proposals = db_session.query(AlertProposal).filter(
        AlertProposal.loyalty_account_id == account.id
    ).all()
    assert len(initial_proposals) == 1

    # Second check run (simulating recurring check or system restart)
    run_2 = run_account_check(db=db_session, account_id=account.id, client=client)
    assert run_2.outcome == "success"

    proposals_after_second_run = db_session.query(AlertProposal).filter(
        AlertProposal.loyalty_account_id == account.id
    ).all()

    # Must still be exactly 1 proposal, no duplicates created
    assert len(proposals_after_second_run) == 1
    assert proposals_after_second_run[0].id == initial_proposals[0].id


def test_tc2_dedupe_survives_real_process_restart(tmp_path, client, frozen_clock):
    """
    TC2 Hard Rule 6 test:
    Explicitly proves deduplication survives a real application restart using a
    file-backed SQLite database. Replaces engine and session completely between checks.
    """
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.app.db import Base

    db_file = tmp_path / "test_restart_survives.db"
    db_url = f"sqlite:///{db_file}"

    # --- PROCESS 1: First boot & run ---
    engine_1 = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine_1)
    Session_1 = sessionmaker(autocommit=False, autoflush=False, bind=engine_1)
    s1 = Session_1()

    u = User(display_name="Restart User", email="restart@synthetic.local")
    s1.add(u)
    s1.commit()
    s1.refresh(u)

    acc = LoyaltyAccount(
        user_id=u.id,
        provider_code="shop_rewards",
        external_mock_id="tc1_account",
        display_name="ShopRewards Restart Check",
        status="unchecked"
    )
    s1.add(acc)
    s1.commit()
    s1.refresh(acc)

    run_account_check(db=s1, account_id=acc.id, client=client)
    p1 = s1.query(AlertProposal).filter(AlertProposal.loyalty_account_id == acc.id).all()
    assert len(p1) == 1
    saved_key = p1[0].dedupe_key

    # Completely terminate/close process 1
    s1.close()
    engine_1.dispose()

    # --- PROCESS 2: Fresh application boot after restart ---
    engine_2 = create_engine(db_url, connect_args={"check_same_thread": False})
    Session_2 = sessionmaker(autocommit=False, autoflush=False, bind=engine_2)
    s2 = Session_2()

    # Run check again after simulated restart
    run_account_check(db=s2, account_id=acc.id, client=client)

    p2 = s2.query(AlertProposal).filter(AlertProposal.loyalty_account_id == acc.id).all()
    # Deduplication MUST survive restart due to the persistent DB UNIQUE constraint
    assert len(p2) == 1
    assert p2[0].dedupe_key == saved_key

    s2.close()
    engine_2.dispose()


def test_tc3_login_failure(db_session, test_user, client, frozen_clock):
    """
    TC3 login failure:
    Portal 401 => account unchecked, error recorded, old snapshot labelled stale,
    no new verified balance.
    """
    # 1. Setup account with an existing valid snapshot
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="tc3_account",
        display_name="ShopRewards TC3",
        status="verified"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    old_snapshot = BalanceSnapshot(
        loyalty_account_id=account.id,
        total_balance=500.0,
        unit="points",
        source_reference="/mock/providers/shop_rewards/accounts/tc3_account",
        is_stale=False
    )
    db_session.add(old_snapshot)
    db_session.commit()

    # 2. Trigger login failure scenario (HTTP 401)
    scenario_overrides["shop_rewards:tc3_account"] = "login_fail"

    try:
        check_run = run_account_check(db=db_session, account_id=account.id, client=client)

        # 3. Assertions
        assert check_run.outcome == "failed"
        assert check_run.error_code == "LOGIN_FAILED"

        # Account must be marked unchecked
        assert account.status == "unchecked"
        assert account.last_error is not None
        assert "LOGIN_FAILED" in account.last_error

        # Old snapshot must be labelled stale
        db_session.refresh(old_snapshot)
        assert old_snapshot.is_stale is True

        # No new snapshot created
        all_snapshots = db_session.query(BalanceSnapshot).filter(
            BalanceSnapshot.loyalty_account_id == account.id
        ).all()
        assert len(all_snapshots) == 1
        assert all_snapshots[0].id == old_snapshot.id
    finally:
        scenario_overrides.pop("shop_rewards:tc3_account", None)


def test_tc4_partial_expiry(db_session, test_user, client, frozen_clock):
    """
    TC4 partial expiry:
    Total 1200; 300 expire Oct 25, 900 expire Dec 31 =>
    expiring-soon amount is 300 (not 1200); future batch retained.
    """
    # demo_shop_01 has 300 expiring Oct 25 (4 days from Oct 21) and 900 expiring Dec 31
    account = LoyaltyAccount(
        user_id=test_user.id,
        provider_code="shop_rewards",
        external_mock_id="demo_shop_01",
        display_name="ShopRewards TC4 Partial",
        status="unchecked"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    check_run = run_account_check(db=db_session, account_id=account.id, client=client)

    assert check_run.outcome == "success"

    # Verify both batches are retained in reward_batches
    batches = db_session.query(RewardBatch).filter(
        RewardBatch.loyalty_account_id == account.id
    ).order_by(RewardBatch.amount_remaining).all()

    assert len(batches) == 2
    assert batches[0].amount_remaining == 300.0
    assert batches[0].expires_at == date(2026, 10, 25)
    assert batches[1].amount_remaining == 900.0
    assert batches[1].expires_at == date(2026, 12, 31)

    # Verify that only the 300 points batch was proposed for alert
    proposals = db_session.query(AlertProposal).filter(
        AlertProposal.loyalty_account_id == account.id
    ).all()

    assert len(proposals) == 1
    assert proposals[0].amount == 300.0  # NOT 1200.0!
    assert proposals[0].expiry_date == date(2026, 10, 25)
    assert proposals[0].status == "pending"

    # Verify total balance snapshot retains 1200.0
    snapshot = db_session.query(BalanceSnapshot).filter(
        BalanceSnapshot.loyalty_account_id == account.id,
        BalanceSnapshot.is_stale == False
    ).first()
    assert snapshot is not None
    assert snapshot.total_balance == 1200.0


def test_tc1_seed_creates_account_exactly_once_when_run_twice(db_session):
    """
    Verifies that seed() creates tc1_account with expected attributes
    and does so idempotently (exactly once when run twice).
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    import backend.scripts.seed_demo as seed_module

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    from backend.app.db import Base
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    original_session = seed_module.SessionLocal
    original_engine = seed_module.engine

    try:
        seed_module.SessionLocal = Session
        seed_module.engine = engine

        # First run
        seed_module.seed()
        # Second run (idempotency check)
        seed_module.seed()

        session = Session()
        tc1_accounts = session.query(LoyaltyAccount).filter(
            LoyaltyAccount.provider_code == "shop_rewards",
            LoyaltyAccount.external_mock_id == "tc1_account"
        ).all()
        session.close()

        assert len(tc1_accounts) == 1, f"Expected exactly 1 tc1_account, got {len(tc1_accounts)}"
        acc = tc1_accounts[0]
        assert acc.display_name == "TC1 Seven-Day Expiry Demo"
        assert acc.status == "unchecked"
    finally:
        seed_module.SessionLocal = original_session
        seed_module.engine = original_engine

