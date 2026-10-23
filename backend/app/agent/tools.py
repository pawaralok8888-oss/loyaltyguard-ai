from typing import List, Dict, Any

ALLOWED_TOOLS: List[str] = [
    "fetch_portal",
    "retry_fetch",
    "mark_unchecked",
    "validate_payload",
    "compute_expiries",
    "propose_alert",
    "verify_recheck",
    "explain"
]

TOOL_DESCRIPTIONS: Dict[str, str] = {
    "fetch_portal": "Retrieve synthetic balance and batches from the loyalty mock portal.",
    "retry_fetch": "Retry retrieving portal data after a transient network error or timeout (max 1 retry).",
    "mark_unchecked": "Mark account unchecked and record failure snapshot due to 401, validation error, or persistent timeout.",
    "validate_payload": "Validate raw portal response using Pydantic schema and unit consistency constraints.",
    "compute_expiries": "Calculate reward batches expiring within 7-day inclusive window (0 to 7 days inclusive).",
    "propose_alert": "Create deduplicated pending alert proposals in database with dedupe_key constraint.",
    "verify_recheck": "Re-read portal after processing to verify stored state against observed state.",
    "explain": "Produce human-readable briefing and audit explanation for the complete run."
}
