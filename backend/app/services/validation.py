from typing import Any, Dict, Tuple, Optional
from pydantic import ValidationError
from backend.app.schemas import MockPortalPayload


class ValidationResult:
    def __init__(
        self,
        is_valid: bool,
        payload: Optional[MockPortalPayload] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.payload = payload
        self.error_code = error_code
        self.error_message = error_message


def validate_portal_payload(raw_data: Any) -> ValidationResult:
    """
    Validates portal payload using Pydantic schema and business sanity rules:
    - Rejects negative amounts (total_balance < 0 or batch amount < 0)
    - Rejects missing dates or invalid formats
    - Rejects mixed units across batches or mismatched with account unit (Rule 7)
    """
    if not isinstance(raw_data, dict):
        return ValidationResult(
            is_valid=False,
            error_code="INVALID_FORMAT",
            error_message="Raw portal response is not a valid JSON dictionary"
        )

    # 1. Check for negative total_balance early
    total_balance = raw_data.get("total_balance")
    if total_balance is not None and isinstance(total_balance, (int, float)) and total_balance < 0:
        return ValidationResult(
            is_valid=False,
            error_code="NEGATIVE_AMOUNT",
            error_message="Total balance cannot be negative"
        )

    # 2. Check for negative amounts or missing dates in batches
    batches = raw_data.get("batches")
    if batches is not None:
        if not isinstance(batches, list):
            return ValidationResult(
                is_valid=False,
                error_code="INVALID_BATCHES",
                error_message="Batches must be a list"
            )

        account_unit = raw_data.get("unit")
        for idx, b in enumerate(batches):
            if not isinstance(b, dict):
                return ValidationResult(
                    is_valid=False,
                    error_code="INVALID_BATCH_ITEM",
                    error_message=f"Batch at index {idx} is not an object"
                )

            amount = b.get("amount_remaining")
            if amount is not None and isinstance(amount, (int, float)) and amount < 0:
                return ValidationResult(
                    is_valid=False,
                    error_code="NEGATIVE_AMOUNT",
                    error_message=f"Batch {b.get('batch_id', idx)} has negative amount: {amount}"
                )

            if "expires_at" not in b or not b["expires_at"]:
                return ValidationResult(
                    is_valid=False,
                    error_code="MISSING_EXPIRY_DATE",
                    error_message=f"Batch {b.get('batch_id', idx)} is missing required 'expires_at' date"
                )

            # Check unit consistency (Rule 7: Never combine/mix unlike units)
            batch_unit = b.get("unit")
            if batch_unit and account_unit and batch_unit != account_unit:
                return ValidationResult(
                    is_valid=False,
                    error_code="MIXED_UNITS",
                    error_message=f"Batch {b.get('batch_id')} unit '{batch_unit}' does not match account unit '{account_unit}'"
                )

    # 3. Pydantic schema validation
    try:
        validated_payload = MockPortalPayload.model_validate(raw_data)
        return ValidationResult(
            is_valid=True,
            payload=validated_payload
        )
    except ValidationError as err:
        return ValidationResult(
            is_valid=False,
            error_code="SCHEMA_VALIDATION_ERROR",
            error_message=str(err)
        )
