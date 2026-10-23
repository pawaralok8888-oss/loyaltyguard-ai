from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models import LoyaltyAccount, User
from backend.app.schemas import LoyaltyAccountCreate, LoyaltyAccountResponse

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=List[LoyaltyAccountResponse])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(LoyaltyAccount).all()


@router.post("", response_model=LoyaltyAccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(account_in: LoyaltyAccountCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == account_in.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {account_in.user_id} not found"
        )

    account = LoyaltyAccount(
        user_id=account_in.user_id,
        provider_code=account_in.provider_code,
        external_mock_id=account_in.external_mock_id,
        display_name=account_in.display_name,
        status="unchecked"
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
