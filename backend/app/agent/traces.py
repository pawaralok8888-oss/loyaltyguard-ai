import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models import AgentTrace
from backend.app.clock import Clock


def record_agent_trace(
    db: Session,
    check_run_id: Optional[int],
    tool_name: str,
    decision_type: str,
    explanation: str,
    input_data: Optional[Dict[str, Any]] = None,
    output_data: Optional[Dict[str, Any]] = None
) -> AgentTrace:
    """
    Persists an agent trace to the database for auditable decision logging.
    Shows whether decision was taken by deterministic fallback or LLM planner.
    """
    trace = AgentTrace(
        check_run_id=check_run_id,
        tool_name=tool_name,
        decision_type=decision_type,
        explanation=explanation,
        input_redacted_json=json.dumps(input_data) if input_data else None,
        output_redacted_json=json.dumps(output_data) if output_data else None,
        created_at=Clock.now_utc()
    )
    db.add(trace)
    db.commit()
    db.refresh(trace)
    return trace
