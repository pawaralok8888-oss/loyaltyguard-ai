import copy
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Response, status
from pydantic import BaseModel
from backend.app.mock_portal.fixtures import DEFAULT_FIXTURES
from backend.app.config import settings


def _require_mock_admin(x_shared_secret: Optional[str] = Header(None, alias="X-Shared-Secret")) -> None:
    """
    Gate for all /mock/admin/* endpoints.
    Requires MOCK_ADMIN_ENABLED=true (env flag) AND a valid X-Shared-Secret header.
    In production, MOCK_ADMIN_ENABLED should be unset/false — the route returns 403
    even if the secret is correct, so the admin surface is fully disabled.
    """
    if not settings.mock_admin_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock admin endpoints are disabled in this environment (MOCK_ADMIN_ENABLED is not true)"
        )
    if not x_shared_secret or x_shared_secret != settings.N8N_SHARED_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Valid X-Shared-Secret header required for mock admin access"
        )


router = APIRouter(prefix="/mock", tags=["mock_portal"])

# In-memory admin overrides for test controllability
# Key: f"{provider}:{external_id}", Value: scenario string or custom payload
scenario_overrides: Dict[str, str] = {}
custom_payload_overrides: Dict[str, dict] = {}


class ScenarioOverrideRequest(BaseModel):
    provider: str
    external_id: str
    scenario: str  # success, unchanged, login_fail, timeout, partial_expiry, malformed, mixed_units


class CustomPayloadRequest(BaseModel):
    provider: str
    external_id: str
    payload: dict


@router.post("/admin/scenario", dependencies=[Depends(_require_mock_admin)])
def set_scenario(req: ScenarioOverrideRequest):
    key = f"{req.provider}:{req.external_id}"
    scenario_overrides[key] = req.scenario
    return {"status": "ok", "key": key, "scenario": req.scenario}


@router.post("/admin/payload", dependencies=[Depends(_require_mock_admin)])
def set_custom_payload(req: CustomPayloadRequest):
    key = f"{req.provider}:{req.external_id}"
    custom_payload_overrides[key] = req.payload
    return {"status": "ok", "key": key}


@router.post("/admin/reset", dependencies=[Depends(_require_mock_admin)])
def reset_scenarios():
    scenario_overrides.clear()
    custom_payload_overrides.clear()
    return {"status": "reset_successful"}


@router.get("/admin/scenarios", dependencies=[Depends(_require_mock_admin)])
def list_scenarios():
    return {
        "overrides": scenario_overrides,
        "custom_payloads": list(custom_payload_overrides.keys())
    }


@router.get("/providers/{provider}/accounts/{external_id}")
def get_mock_account_data(
    provider: str,
    external_id: str,
    x_mock_scenario: Optional[str] = Header(None, alias="X-Mock-Scenario"),
    scenario: Optional[str] = Query(None)
):
    key = f"{provider}:{external_id}"
    effective_scenario = x_mock_scenario or scenario or scenario_overrides.get(key, "success")

    # 1. Login Failure scenario (HTTP 401)
    if effective_scenario == "login_fail":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Portal authentication failed: invalid token or expired session"
        )

    # 2. Timeout scenario (HTTP 504)
    if effective_scenario == "timeout":
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Portal upstream gateway timeout after 10000ms"
        )

    # 3. Custom payload override if registered
    if key in custom_payload_overrides:
        return custom_payload_overrides[key]

    # 4. Partial expiry scenario (TC4 standard)
    if effective_scenario == "partial_expiry":
        return {
            "account_id": external_id,
            "provider": provider,
            "unit": "points",
            "total_balance": 1200.0,
            "batches": [
                {"batch_id": "batch_A", "amount_remaining": 300.0, "expires_at": "2026-10-25"},
                {"batch_id": "batch_B", "amount_remaining": 900.0, "expires_at": "2026-12-31"}
            ]
        }

    # 5. Malformed payload scenarios
    if effective_scenario == "malformed":
        # Missing date or negative amount
        return {
            "account_id": external_id,
            "provider": provider,
            "unit": "points",
            "total_balance": 1200.0,
            "batches": [
                {"batch_id": "bad_batch_1", "amount_remaining": -50.0, "expires_at": "2026-10-25"},
                {"batch_id": "bad_batch_2", "amount_remaining": 300.0}  # missing expires_at
            ]
        }

    # 6. Mixed units scenario (Hard Rule 7 violation to test validation rejection)
    if effective_scenario == "mixed_units":
        return {
            "account_id": external_id,
            "provider": provider,
            "unit": "points",
            "total_balance": 1000.0,
            "batches": [
                {"batch_id": "batch_pts", "amount_remaining": 500.0, "expires_at": "2026-10-25", "unit": "points"},
                {"batch_id": "batch_inr", "amount_remaining": 500.0, "expires_at": "2026-10-26", "unit": "INR"}
            ]
        }

    # 7. Default fixtures / success / unchanged
    provider_fixtures = DEFAULT_FIXTURES.get(provider)
    if not provider_fixtures:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mock provider '{provider}' not found"
        )

    fixture = provider_fixtures.get(external_id)
    if not fixture:
        # Fallback synthetic record if not explicitly in fixtures
        unit = "INR" if provider == "gift_hub" else "points"
        return {
            "account_id": external_id,
            "provider": provider,
            "unit": unit,
            "total_balance": 1000.0,
            "batches": [
                {"batch_id": f"{external_id}_batch_1", "amount_remaining": 1000.0, "expires_at": "2026-10-28"}
            ]
        }

    return copy.deepcopy(fixture)
