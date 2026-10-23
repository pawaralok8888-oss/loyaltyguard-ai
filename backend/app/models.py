from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, UniqueConstraint, Text
)
from sqlalchemy.orm import relationship
from backend.app.db import Base
from backend.app.clock import Clock


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True)  # synthetic
    created_at = Column(DateTime, default=Clock.now_utc)

    loyalty_accounts = relationship("LoyaltyAccount", back_populates="user", cascade="all, delete-orphan")
    alert_proposals = relationship("AlertProposal", back_populates="user", cascade="all, delete-orphan")


class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_code = Column(String(50), nullable=False)  # shop_rewards, fly_miles, gift_hub
    external_mock_id = Column(String(100), nullable=False)  # demo_shop_01
    display_name = Column(String(100), nullable=False)
    status = Column(String(20), default="unchecked")  # verified | unchecked
    last_checked_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    user = relationship("User", back_populates="loyalty_accounts")
    reward_batches = relationship("RewardBatch", back_populates="loyalty_account", cascade="all, delete-orphan")
    balance_snapshots = relationship("BalanceSnapshot", back_populates="loyalty_account", cascade="all, delete-orphan")
    check_runs = relationship("CheckRun", back_populates="loyalty_account", cascade="all, delete-orphan")
    alert_proposals = relationship("AlertProposal", back_populates="loyalty_account", cascade="all, delete-orphan")


class RewardBatch(Base):
    __tablename__ = "reward_batches"

    id = Column(Integer, primary_key=True, index=True)
    loyalty_account_id = Column(Integer, ForeignKey("loyalty_accounts.id"), nullable=False)
    external_batch_id = Column(String(100), nullable=False)
    reward_type = Column(String(20), nullable=False)  # points | currency
    amount_remaining = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # points | INR
    expires_at = Column(Date, nullable=False)
    last_verified_at = Column(DateTime, nullable=True)

    loyalty_account = relationship("LoyaltyAccount", back_populates="reward_batches")
    alert_proposals = relationship("AlertProposal", back_populates="reward_batch")

    __table_args__ = (
        UniqueConstraint("loyalty_account_id", "external_batch_id", name="uq_account_batch"),
    )


class CheckRun(Base):
    __tablename__ = "check_runs"

    id = Column(Integer, primary_key=True, index=True)
    loyalty_account_id = Column(Integer, ForeignKey("loyalty_accounts.id"), nullable=False)
    started_at = Column(DateTime, default=Clock.now_utc)
    finished_at = Column(DateTime, nullable=True)
    outcome = Column(String(50), nullable=False)  # success | failed | partial
    error_code = Column(String(50), nullable=True)
    verification_status = Column(String(50), nullable=True)  # verified | mismatch | verification_failed
    evidence_json = Column(Text, nullable=True)

    loyalty_account = relationship("LoyaltyAccount", back_populates="check_runs")
    snapshots = relationship("BalanceSnapshot", back_populates="check_run")
    agent_traces = relationship("AgentTrace", back_populates="check_run", cascade="all, delete-orphan")


class BalanceSnapshot(Base):
    __tablename__ = "balance_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    loyalty_account_id = Column(Integer, ForeignKey("loyalty_accounts.id"), nullable=False)
    total_balance = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    retrieved_at = Column(DateTime, default=Clock.now_utc)
    source_reference = Column(String(255), nullable=False)
    check_run_id = Column(Integer, ForeignKey("check_runs.id"), nullable=True)
    is_stale = Column(Boolean, default=False)

    loyalty_account = relationship("LoyaltyAccount", back_populates="balance_snapshots")
    check_run = relationship("CheckRun", back_populates="snapshots")


class AlertProposal(Base):
    __tablename__ = "alert_proposals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    loyalty_account_id = Column(Integer, ForeignKey("loyalty_accounts.id"), nullable=False)
    reward_batch_id = Column(Integer, ForeignKey("reward_batches.id"), nullable=True)
    threshold_days = Column(Integer, nullable=False)
    expiry_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")  # pending | approved | rejected | sent | failed
    dedupe_key = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=Clock.now_utc)
    approved_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="alert_proposals")
    loyalty_account = relationship("LoyaltyAccount", back_populates="alert_proposals")
    reward_batch = relationship("RewardBatch", back_populates="alert_proposals")
    notification_events = relationship("NotificationEvent", back_populates="alert_proposal", cascade="all, delete-orphan")


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id = Column(Integer, primary_key=True, index=True)
    alert_proposal_id = Column(Integer, ForeignKey("alert_proposals.id"), nullable=False)
    channel = Column(String(50), default="simulated_in_app")
    outcome = Column(String(20), nullable=False)  # sent | failed
    attempted_at = Column(DateTime, default=Clock.now_utc)
    provider_message_id = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

    alert_proposal = relationship("AlertProposal", back_populates="notification_events")

    __table_args__ = (
        UniqueConstraint("alert_proposal_id", name="uq_proposal_notification"),
    )


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(Integer, primary_key=True, index=True)
    check_run_id = Column(Integer, ForeignKey("check_runs.id"), nullable=True)
    tool_name = Column(String(50), nullable=False)
    decision_type = Column(String(50), nullable=False)
    explanation = Column(Text, nullable=False)
    input_redacted_json = Column(Text, nullable=True)
    output_redacted_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=Clock.now_utc)

    check_run = relationship("CheckRun", back_populates="agent_traces")
