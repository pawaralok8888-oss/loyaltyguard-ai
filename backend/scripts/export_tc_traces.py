"""
Exports exact agent traces for TC1 and TC3 into evidence/traces/
"""
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.db import SessionLocal, Base, engine
from backend.app.clock import Clock, KOLKATA_TZ
from backend.app.models import User, LoyaltyAccount, AgentTrace, CheckRun
from backend.app.services.check_runner import run_account_check
from backend.app.mock_portal.router import scenario_overrides


def export_traces():
    os.makedirs("evidence/traces", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Freeze clock for test reproducibility
    freeze_time = datetime(2026, 10, 21, 0, 0, 0, tzinfo=KOLKATA_TZ)
    Clock.set_frozen(freeze_time)

    client = TestClient(app, base_url="http://testserver")

    try:
        user = db.query(User).filter(User.email == "traces_user@synthetic.local").first()
        if not user:
            user = User(display_name="Traces User", email="traces_user@synthetic.local")
            db.add(user)
            db.commit()
            db.refresh(user)

        # -----------------------------
        # 1. RUN TC1 (7-day expiry)
        # -----------------------------
        acc_tc1 = db.query(LoyaltyAccount).filter(
            LoyaltyAccount.user_id == user.id,
            LoyaltyAccount.external_mock_id == "tc1_account"
        ).first()
        if not acc_tc1:
            acc_tc1 = LoyaltyAccount(
                user_id=user.id,
                provider_code="shop_rewards",
                external_mock_id="tc1_account",
                display_name="ShopRewards TC1 Trace",
                status="unchecked"
            )
            db.add(acc_tc1)
            db.commit()
            db.refresh(acc_tc1)

        run_tc1 = run_account_check(db=db, account_id=acc_tc1.id, client=client)
        traces_tc1 = db.query(AgentTrace).filter(
            AgentTrace.check_run_id == run_tc1.id
        ).order_by(AgentTrace.id.asc()).all()

        tc1_data = [
            {
                "step": idx + 1,
                "tool_name": t.tool_name,
                "decision_type": t.decision_type,
                "explanation": t.explanation,
                "input": json.loads(t.input_redacted_json) if t.input_redacted_json else None,
                "output": json.loads(t.output_redacted_json) if t.output_redacted_json else None,
                "timestamp": t.created_at.isoformat()
            }
            for idx, t in enumerate(traces_tc1)
        ]

        with open("evidence/traces/tc1_trace.json", "w", encoding="utf-8") as f:
            json.dump(tc1_data, f, indent=2)
        print(f"[Export] Saved {len(tc1_data)} traces for TC1 to evidence/traces/tc1_trace.json")

        # -----------------------------
        # 2. RUN TC3 (Login failure 401)
        # -----------------------------
        acc_tc3 = db.query(LoyaltyAccount).filter(
            LoyaltyAccount.user_id == user.id,
            LoyaltyAccount.external_mock_id == "tc3_account"
        ).first()
        if not acc_tc3:
            acc_tc3 = LoyaltyAccount(
                user_id=user.id,
                provider_code="shop_rewards",
                external_mock_id="tc3_account",
                display_name="ShopRewards TC3 401 Trace",
                status="verified"
            )
            db.add(acc_tc3)
            db.commit()
            db.refresh(acc_tc3)

        scenario_overrides["shop_rewards:tc3_account"] = "login_fail"
        try:
            run_tc3 = run_account_check(db=db, account_id=acc_tc3.id, client=client)
            traces_tc3 = db.query(AgentTrace).filter(
                AgentTrace.check_run_id == run_tc3.id
            ).order_by(AgentTrace.id.asc()).all()

            tc3_data = [
                {
                    "step": idx + 1,
                    "tool_name": t.tool_name,
                    "decision_type": t.decision_type,
                    "explanation": t.explanation,
                    "input": json.loads(t.input_redacted_json) if t.input_redacted_json else None,
                    "output": json.loads(t.output_redacted_json) if t.output_redacted_json else None,
                    "timestamp": t.created_at.isoformat()
                }
                for idx, t in enumerate(traces_tc3)
            ]

            with open("evidence/traces/tc3_trace.json", "w", encoding="utf-8") as f:
                json.dump(tc3_data, f, indent=2)
            print(f"[Export] Saved {len(tc3_data)} traces for TC3 to evidence/traces/tc3_trace.json")
        finally:
            scenario_overrides.pop("shop_rewards:tc3_account", None)

    finally:
        Clock.reset()
        db.close()


if __name__ == "__main__":
    export_traces()
