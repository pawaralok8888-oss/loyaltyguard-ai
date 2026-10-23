from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.config import settings
from backend.app.models import LoyaltyAccount, CheckRun
from backend.app.schemas import CheckRunResponse
from backend.app.services.check_runner import run_account_check

router = APIRouter(tags=["checks"])


@router.post("/api/accounts/{id}/check", response_model=CheckRunResponse)
def trigger_account_check(id: int, db: Session = Depends(get_db)):
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.id == id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {id} not found"
        )
    check_run = run_account_check(db=db, account_id=id)
    return check_run


@router.post("/api/checks/run", response_model=List[CheckRunResponse])
def trigger_bulk_checks(
    x_shared_secret: Optional[str] = Header(None, alias="X-Shared-Secret"),
    db: Session = Depends(get_db)
):
    """
    Bulk check run intended for automated scheduled monitors (e.g. n8n).
    Protected by a server-side shared secret header.
    """
    if not x_shared_secret or x_shared_secret != settings.N8N_SHARED_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Shared-Secret header"
        )

    accounts = db.query(LoyaltyAccount).all()
    results = []
    for acc in accounts:
        check_run = run_account_check(db=db, account_id=acc.id)
        results.append(check_run)

    return results
