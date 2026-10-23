from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models import CheckRun, AgentTrace
from backend.app.schemas import CheckRunResponse, AgentTraceResponse

router = APIRouter(prefix="/api", tags=["runs_and_traces"])


@router.get("/runs", response_model=List[CheckRunResponse])
def list_check_runs(db: Session = Depends(get_db)):
    return db.query(CheckRun).order_by(CheckRun.started_at.desc()).all()


@router.get("/traces", response_model=List[AgentTraceResponse])
def list_agent_traces(
    check_run_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(AgentTrace)
    if check_run_id is not None:
        query = query.filter(AgentTrace.check_run_id == check_run_id)
    return query.order_by(AgentTrace.created_at.desc()).all()
