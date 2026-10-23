from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models import AlertProposal, NotificationEvent
from backend.app.schemas import AlertProposalResponse, NotificationEventResponse
from backend.app.services.notify import (
    approve_alert, reject_alert, send_alert_notification, NotificationError
)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertProposalResponse])
def list_alerts(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(AlertProposal)
    if status_filter:
        query = query.filter(AlertProposal.status == status_filter)
    return query.order_by(AlertProposal.created_at.desc()).all()


@router.get("/{id}", response_model=AlertProposalResponse)
def get_alert(id: int, db: Session = Depends(get_db)):
    proposal = db.query(AlertProposal).filter(AlertProposal.id == id).first()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert proposal not found")
    return proposal


@router.post("/{id}/approve", response_model=AlertProposalResponse)
def approve_alert_endpoint(id: int, db: Session = Depends(get_db)):
    try:
        return approve_alert(db=db, proposal_id=id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/reject", response_model=AlertProposalResponse)
def reject_alert_endpoint(id: int, db: Session = Depends(get_db)):
    try:
        return reject_alert(db=db, proposal_id=id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/send")
def send_alert_endpoint(id: int, db: Session = Depends(get_db)):
    """
    Sends approved alert proposal via simulated in-app channel.
    Idempotent: Subsequent calls return the existing notification event.
    """
    try:
        proposal, event, newly_sent = send_alert_notification(db=db, proposal_id=id)
        return {
            "status": "success",
            "is_newly_sent": newly_sent,
            "proposal": AlertProposalResponse.model_validate(proposal),
            "notification_event": NotificationEventResponse.model_validate(event)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotificationError as e:
        # Rejection or unapproved status rejects send
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
