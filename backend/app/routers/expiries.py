from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.clock import Clock
from backend.app.models import RewardBatch, LoyaltyAccount, BalanceSnapshot
from backend.app.schemas import RewardBatchResponse, CalendarItemResponse

router = APIRouter(prefix="/api", tags=["expiries_and_calendar"])


@router.get("/expiries", response_model=List[RewardBatchResponse])
def get_expiring_batches(
    days: int = Query(7, ge=0),
    db: Session = Depends(get_db)
):
    today = Clock.today_local()
    all_batches = db.query(RewardBatch).all()
    expiring = []
    for b in all_batches:
        delta = (b.expires_at - today).days
        if 0 <= delta <= days:
            expiring.append(b)
    return expiring


@router.get("/calendar", response_model=List[CalendarItemResponse])
def get_points_calendar(db: Session = Depends(get_db)):
    today = Clock.today_local()
    batches = db.query(RewardBatch).join(LoyaltyAccount).all()

    calendar_items = []
    for b in batches:
        acc = b.loyalty_account
        delta = (b.expires_at - today).days

        # Check if latest snapshot is stale
        latest_snapshot = db.query(BalanceSnapshot).filter(
            BalanceSnapshot.loyalty_account_id == acc.id
        ).order_by(BalanceSnapshot.retrieved_at.desc()).first()

        is_stale = latest_snapshot.is_stale if latest_snapshot else True
        source_ref = latest_snapshot.source_reference if latest_snapshot else ""

        calendar_items.append(
            CalendarItemResponse(
                account_id=acc.id,
                account_display_name=acc.display_name,
                provider_code=acc.provider_code,
                batch_id=b.external_batch_id,
                amount=b.amount_remaining,
                unit=b.unit,
                expiry_date=b.expires_at,
                days_left=delta,
                status=acc.status,
                is_stale=is_stale,
                source_reference=source_ref
            )
        )

    # Sort by expiry_date ascending
    calendar_items.sort(key=lambda item: item.expiry_date)
    return calendar_items
