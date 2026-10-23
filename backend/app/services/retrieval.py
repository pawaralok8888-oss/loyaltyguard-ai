from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import httpx
from backend.app.clock import Clock
from backend.app.config import settings


class RetrievalResult:
    def __init__(
        self,
        success: bool,
        status_code: int,
        data: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        source_reference: str = "",
        retrieved_at: Optional[datetime] = None
    ):
        self.success = success
        self.status_code = status_code
        self.data = data
        self.error_code = error_code
        self.error_message = error_message
        self.source_reference = source_reference
        self.retrieved_at = retrieved_at or Clock.now_utc()


def fetch_from_portal(
    provider_code: str,
    external_mock_id: str,
    client: Optional[httpx.Client] = None,
    scenario: Optional[str] = None,
    base_url: Optional[str] = None
) -> RetrievalResult:
    """
    Fetches synthetic account balance and reward batches from the mock portal.
    Captures HTTP 401 (login_fail), HTTP 504 (timeout), connection errors, etc.
    base_url defaults to settings.PORTAL_BASE_URL; tests inject their own client.
    """
    effective_base_url = base_url or settings.PORTAL_BASE_URL
    url = f"/mock/providers/{provider_code}/accounts/{external_mock_id}"
    headers = {}
    if scenario:
        headers["X-Mock-Scenario"] = scenario

    retrieved_at = Clock.now_utc()
    source_ref = f"{url}?ts={retrieved_at.isoformat()}"

    close_client = False
    if client is None:
        try:
            from starlette.testclient import TestClient
            from backend.app.main import app
            client = TestClient(app, base_url="http://testserver")
        except Exception:
            client = httpx.Client(base_url=effective_base_url, timeout=5.0)
        close_client = True

    try:
        response = client.get(url, headers=headers)
        if response.status_code == 200:
            return RetrievalResult(
                success=True,
                status_code=200,
                data=response.json(),
                source_reference=source_ref,
                retrieved_at=retrieved_at
            )
        elif response.status_code == 401:
            return RetrievalResult(
                success=False,
                status_code=401,
                error_code="LOGIN_FAILED",
                error_message="Portal authentication failed: invalid credentials or session expired",
                source_reference=source_ref,
                retrieved_at=retrieved_at
            )
        elif response.status_code == 504:
            return RetrievalResult(
                success=False,
                status_code=504,
                error_code="TIMEOUT",
                error_message="Portal request timed out",
                source_reference=source_ref,
                retrieved_at=retrieved_at
            )
        else:
            return RetrievalResult(
                success=False,
                status_code=response.status_code,
                error_code="HTTP_ERROR",
                error_message=f"Portal returned HTTP {response.status_code}: {response.text}",
                source_reference=source_ref,
                retrieved_at=retrieved_at
            )
    except httpx.TimeoutException:
        return RetrievalResult(
            success=False,
            status_code=504,
            error_code="TIMEOUT",
            error_message="Client-side timeout contacting mock portal",
            source_reference=source_ref,
            retrieved_at=retrieved_at
        )
    except Exception as exc:
        return RetrievalResult(
            success=False,
            status_code=500,
            error_code="CONNECTION_ERROR",
            error_message=str(exc),
            source_reference=source_ref,
            retrieved_at=retrieved_at
        )
    finally:
        if close_client:
            try:
                client.close()
            except Exception:
                pass
