from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.models import AlertProposal, RewardBatch
from backend.app.services.expiry import ExpiringBatchItem
from backend.app.clock import Clock


def generate_dedupe_key(
    user_id: int,
    account_id: int,
    batch_id: str,
    expiry_date: date,
    threshold_days: int,
    amount: float
) -> str:
    """
    Constructs the canonical dedupe key:
    user_id|account_id|batch_id|expiry_date|threshold_days|amount
    A genuinely changed amount or expiry creates a new key (and so a new alert);
    an unchanged batch never does.
    """
    # Format amount cleanly to avoid float representation drift (e.g. 250 vs 250.0)
    formatted_amount = f"{amount:g}"
    return f"{user_id}|{account_id}|{batch_id}|{expiry_date.isoformat()}|{threshold_days}|{formatted_amount}"


def create_alert_proposals_for_account(
    db: Session,
    user_id: int,
    loyalty_account_id: int,
    expiring_items: List[ExpiringBatchItem]
) -> List[AlertProposal]:
    """
    Creates pending alert proposals in the database.
    Enforces deduplication via UNIQUE database constraint on dedupe_key.
    Skips existing keys without error.
    """
    created_proposals: List[AlertProposal] = []

    for item in expiring_items:
        dedupe_key = generate_dedupe_key(
            user_id=user_id,
            account_id=loyalty_account_id,
            batch_id=item.batch_id,
            expiry_date=item.expiry_date,
            threshold_days=item.threshold_days,
            amount=item.amount
        )

        # Check if already exists in DB
        existing = db.query(AlertProposal).filter(AlertProposal.dedupe_key == dedupe_key).first()
        if existing:
            continue

        # Find reward_batch_id if exists
        reward_batch = db.query(RewardBatch).filter(
            RewardBatch.loyalty_account_id == loyalty_account_id,
            RewardBatch.external_batch_id == item.batch_id
        ).first()

        proposal = AlertProposal(
            user_id=user_id,
            loyalty_account_id=loyalty_account_id,
            reward_batch_id=reward_batch.id if reward_batch else None,
            threshold_days=item.threshold_days,
            expiry_date=item.expiry_date,
            amount=item.amount,
            unit=item.unit,
            status="pending",
            dedupe_key=dedupe_key,
            created_at=Clock.now_utc()
        )

        try:
            db.add(proposal)
            db.commit()
            db.refresh(proposal)
            created_proposals.append(proposal)
        except IntegrityError:
            # UNIQUE constraint triggered (e.g. concurrent insert)
            db.rollback()
            continue

    return created_proposals
