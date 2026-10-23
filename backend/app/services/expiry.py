from datetime import date
from typing import List, Dict, Any, Optional
from backend.app.clock import Clock
from backend.app.schemas import MockRewardBatch


class ExpiringBatchItem:
    def __init__(
        self,
        batch_id: str,
        amount: float,
        unit: str,
        expiry_date: date,
        days_left: int,
        threshold_days: int = 7
    ):
        self.batch_id = batch_id
        self.amount = amount
        self.unit = unit
        self.expiry_date = expiry_date
        self.days_left = days_left
        self.threshold_days = threshold_days


def compute_expiring_batches(
    batches: List[MockRewardBatch],
    account_unit: str,
    threshold_days: int = 7,
    today_override: Optional[date] = None
) -> List[ExpiringBatchItem]:
    """
    Computes expiring batches within the threshold window deterministically.
    Rule 9: 'expiry_date - today between 0 and 7 days inclusive; already expired is excluded.'
    - 0 <= (expiry_date - today) <= threshold_days => INCLUDED
    - (expiry_date - today) < 0 => EXCLUDED (already expired)
    - (expiry_date - today) > threshold_days => EXCLUDED (future batch retained, not expiring soon)
    """
    today = today_override or Clock.today_local()
    expiring_items: List[ExpiringBatchItem] = []

    for batch in batches:
        delta = (batch.expires_at - today).days
        if 0 <= delta <= threshold_days:
            unit = batch.unit or account_unit
            expiring_items.append(
                ExpiringBatchItem(
                    batch_id=batch.batch_id,
                    amount=batch.amount_remaining,
                    unit=unit,
                    expiry_date=batch.expires_at,
                    days_left=delta,
                    threshold_days=threshold_days
                )
            )

    return expiring_items
