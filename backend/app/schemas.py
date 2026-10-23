from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


# --- Mock Portal Schemas ---

class MockRewardBatch(BaseModel):
    batch_id: str = Field(..., min_length=1)
    amount_remaining: float
    expires_at: date
    unit: Optional[str] = None

    @field_validator("amount_remaining")
    @classmethod
    def amount_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Amount remaining cannot be negative")
        return v


class MockPortalPayload(BaseModel):
    account_id: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    unit: str = Field(..., min_length=1)
    total_balance: float
    batches: List[MockRewardBatch] = Field(default_factory=list)

    @field_validator("total_balance")
    @classmethod
    def total_balance_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Total balance cannot be negative")
        return v


# --- API Request & Response Schemas ---

class UserCreate(BaseModel):
    display_name: str
    email: str


class UserResponse(BaseModel):
    id: int
    display_name: str
    email: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LoyaltyAccountCreate(BaseModel):
    user_id: int
    provider_code: str
    external_mock_id: str
    display_name: str


class LoyaltyAccountResponse(BaseModel):
    id: int
    user_id: int
    provider_code: str
    external_mock_id: str
    display_name: str
    status: str
    last_checked_at: Optional[datetime] = None
    last_error: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class RewardBatchResponse(BaseModel):
    id: int
    loyalty_account_id: int
    external_batch_id: str
    reward_type: str
    amount_remaining: float
    unit: str
    expires_at: date
    last_verified_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class BalanceSnapshotResponse(BaseModel):
    id: int
    loyalty_account_id: int
    total_balance: float
    unit: str
    retrieved_at: datetime
    source_reference: str
    check_run_id: Optional[int] = None
    is_stale: bool
    model_config = ConfigDict(from_attributes=True)


class AlertProposalResponse(BaseModel):
    id: int
    user_id: int
    loyalty_account_id: int
    reward_batch_id: Optional[int] = None
    threshold_days: int
    expiry_date: date
    amount: float
    unit: str
    status: str
    dedupe_key: str
    created_at: datetime
    approved_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class NotificationEventResponse(BaseModel):
    id: int
    alert_proposal_id: int
    channel: str
    outcome: str
    attempted_at: datetime
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class AgentTraceResponse(BaseModel):
    id: int
    check_run_id: Optional[int] = None
    tool_name: str
    decision_type: str
    explanation: str
    input_redacted_json: Optional[str] = None
    output_redacted_json: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CheckRunResponse(BaseModel):
    id: int
    loyalty_account_id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    outcome: str
    error_code: Optional[str] = None
    verification_status: Optional[str] = None
    evidence_json: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class CalendarItemResponse(BaseModel):
    account_id: int
    account_display_name: str
    provider_code: str
    batch_id: str
    amount: float
    unit: str
    expiry_date: date
    days_left: int
    status: str
    is_stale: bool
    source_reference: str
