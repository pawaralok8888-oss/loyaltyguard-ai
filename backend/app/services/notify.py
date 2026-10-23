import uuid
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.models import AlertProposal, NotificationEvent
from backend.app.clock import Clock


class NotificationError(Exception):
    """Custom exception raised when alert sending policy is violated."""
    pass


def approve_alert(db: Session, proposal_id: int) -> AlertProposal:
    """Explicit human approval record with timestamp."""
    proposal = db.query(AlertProposal).filter(AlertProposal.id == proposal_id).first()
    if not proposal:
        raise ValueError(f"AlertProposal {proposal_id} not found")

    if proposal.status != "pending":
        raise NotificationError(f"Invalid transition: Cannot approve alert in '{proposal.status}' state.")

    proposal.status = "approved"
    proposal.approved_at = Clock.now_utc()
    db.commit()
    db.refresh(proposal)
    return proposal


def reject_alert(db: Session, proposal_id: int) -> AlertProposal:
    """Explicit human rejection record with timestamp."""
    proposal = db.query(AlertProposal).filter(AlertProposal.id == proposal_id).first()
    if not proposal:
        raise ValueError(f"AlertProposal {proposal_id} not found")

    if proposal.status != "pending":
        raise NotificationError(f"Invalid transition: Cannot reject alert in '{proposal.status}' state.")

    proposal.status = "rejected"
    proposal.approved_at = None
    db.commit()
    db.refresh(proposal)
    return proposal


def send_alert_notification(
    db: Session,
    proposal_id: int,
    channel: str = "simulated_in_app"
) -> Tuple[AlertProposal, NotificationEvent, bool]:
    """
    Sends an alert proposal via simulated in-app channel.
    Hard rules:
    - Rule 5: No alert is sent without an explicit human approval record.
      Pending and rejected alerts NEVER send.
    - Idempotency: Retrying send on an already sent proposal returns the
      existing notification event without duplicating sends.

    Returns:
        (proposal, notification_event, is_newly_sent)
    """
    proposal = db.query(AlertProposal).filter(AlertProposal.id == proposal_id).first()
    if not proposal:
        raise ValueError(f"AlertProposal {proposal_id} not found")

    # Guard: Pending proposals cannot send
    if proposal.status == "pending":
        raise NotificationError("Cannot send alert: Proposal is pending explicit human approval.")

    # Guard: Rejected proposals cannot send
    if proposal.status == "rejected":
        raise NotificationError("Cannot send alert: Proposal was rejected by operator.")

    # Idempotency check: Already sent proposals return the existing event
    if proposal.status == "sent":
        existing_event = db.query(NotificationEvent).filter(
            NotificationEvent.alert_proposal_id == proposal.id,
            NotificationEvent.outcome == "sent"
        ).order_by(NotificationEvent.attempted_at.asc()).first()

        if existing_event:
            return proposal, existing_event, False

    # Status must be "approved" or "failed" (retry) to send
    if proposal.status not in ["approved", "failed"]:
        raise NotificationError(f"Cannot send alert: Unexpected proposal status '{proposal.status}'.")

    now = Clock.now_utc()
    provider_msg_id = f"in_app_{uuid.uuid4().hex[:12]}"

    existing_event = db.query(NotificationEvent).filter(
        NotificationEvent.alert_proposal_id == proposal.id
    ).first()

    if existing_event:
        existing_event.outcome = "sent"
        existing_event.attempted_at = now
        existing_event.provider_message_id = provider_msg_id
        existing_event.error_message = None
        event = existing_event
    else:
        event = NotificationEvent(
            alert_proposal_id=proposal.id,
            channel=channel,
            outcome="sent",
            attempted_at=now,
            provider_message_id=provider_msg_id,
            error_message=None
        )
        db.add(event)

    proposal.status = "sent"
    proposal.sent_at = now
    db.commit()
    db.refresh(proposal)
    db.refresh(event)

    return proposal, event, True
