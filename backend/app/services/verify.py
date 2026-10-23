from typing import Optional, Dict, Any, List
import httpx
from backend.app.services.retrieval import fetch_from_portal, RetrievalResult
from backend.app.services.validation import validate_portal_payload
from backend.app.schemas import MockRewardBatch


class VerificationResult:
    def __init__(
        self,
        status: str,  # verified | mismatch | verification_failed
        details: Dict[str, Any]
    ):
        self.status = status
        self.details = details


def verify_post_run(
    provider_code: str,
    external_mock_id: str,
    expected_total: float,
    expected_batches: List[MockRewardBatch],
    client: Optional[httpx.Client] = None,
    scenario: Optional[str] = None
) -> VerificationResult:
    """
    Step 9: Post-run verification re-read.
    Rule 9: 'Re-read portal after the run; compare observed vs stored;
    record verified, mismatch or verification_failed.
    Never claim verification success if the re-read failed.'
    """
    re_read: RetrievalResult = fetch_from_portal(
        provider_code=provider_code,
        external_mock_id=external_mock_id,
        client=client,
        scenario=scenario
    )

    if not re_read.success:
        return VerificationResult(
            status="verification_failed",
            details={
                "reason": "Re-read portal fetch failed",
                "error_code": re_read.error_code,
                "status_code": re_read.status_code
            }
        )

    val = validate_portal_payload(re_read.data)
    if not val.is_valid:
        return VerificationResult(
            status="verification_failed",
            details={
                "reason": "Re-read payload validation failed",
                "error_code": val.error_code,
                "error_message": val.error_message
            }
        )

    observed_payload = val.payload

    # Compare observed total vs stored
    if observed_payload.total_balance != expected_total:
        return VerificationResult(
            status="mismatch",
            details={
                "expected_total": expected_total,
                "observed_total": observed_payload.total_balance
            }
        )

    # Compare batch count
    if len(observed_payload.batches) != len(expected_batches):
        return VerificationResult(
            status="mismatch",
            details={
                "expected_batch_count": len(expected_batches),
                "observed_batch_count": len(observed_payload.batches)
            }
        )

    # All checks passed
    return VerificationResult(
        status="verified",
        details={
            "total_balance": observed_payload.total_balance,
            "batches_count": len(observed_payload.batches)
        }
    )
