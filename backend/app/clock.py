from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
from typing import Optional
from contextlib import contextmanager

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
UTC_TZ = timezone.utc


class Clock:
    """Injectable clock for deterministic testing and consistent internal UTC handling."""
    _frozen_dt: Optional[datetime] = None

    @classmethod
    def set_frozen(cls, dt: Optional[datetime]) -> None:
        """Sets the frozen datetime. If naive, assumes Asia/Kolkata."""
        if dt is None:
            cls._frozen_dt = None
            return

        if dt.tzinfo is None:
            cls._frozen_dt = dt.replace(tzinfo=KOLKATA_TZ)
        else:
            cls._frozen_dt = dt

    @classmethod
    def reset(cls) -> None:
        cls._frozen_dt = None

    @classmethod
    @contextmanager
    def freeze(cls, dt: datetime):
        previous = cls._frozen_dt
        try:
            cls.set_frozen(dt)
            yield
        finally:
            cls._frozen_dt = previous

    @classmethod
    def now_utc(cls) -> datetime:
        """Returns current time in UTC (internal storage)."""
        if cls._frozen_dt is not None:
            return cls._frozen_dt.astimezone(UTC_TZ)
        return datetime.now(UTC_TZ)

    @classmethod
    def now_local(cls) -> datetime:
        """Returns current time in Asia/Kolkata (display/user timezone)."""
        if cls._frozen_dt is not None:
            return cls._frozen_dt.astimezone(KOLKATA_TZ)
        return datetime.now(KOLKATA_TZ)

    @classmethod
    def today_local(cls) -> date:
        """Returns current date in Asia/Kolkata for business day calculations."""
        return cls.now_local().date()
