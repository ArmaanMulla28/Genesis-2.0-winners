"""
validator.py - Validation Engine for Schema Patches and Transformed Requests.

Ensures:
- Patch proposals are verified, safe, and compatible.
- Incompatible data or malformed values are rejected before registry changes.
- Transformed requests strictly validate against target Pydantic models.
- Never invents credentials, tokens, or unverified security parameters.
"""

from typing import Any, Dict, Optional, Tuple
from pydantic import ValidationError

from app.models import (
    SchemaVersion,
    StudentRequestV1,
    StudentRequestV2,
)


class PatchValidationResult:
    """Encapsulates the outcome of patch proposal and transformed payload validation."""

    def __init__(
        self,
        is_valid: bool,
        reason: str,
        transformed_payload: Optional[Dict[str, Any]] = None,
        error_details: Optional[Any] = None,
    ) -> None:
        self.is_valid = is_valid
        self.reason = reason
        self.transformed_payload = transformed_payload
        self.error_details = error_details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "reason": self.reason,
            "transformed_payload": self.transformed_payload,
            "error_details": self.error_details,
        }


class SchemaPatchValidator:
    """
    Validates proposed schema transformations and checks target model conformity.
    """

    # Disallowed credential keys that must never be fabricated or injected
    RESTRICTED_SECURITY_FIELDS = {
        "authorization",
        "access_token",
        "api_key",
        "bearer",
        "client_secret",
        "oauth_token",
        "password",
        "secret",
        "token",
    }

    @classmethod
    def validate_patch_proposal(
        cls,
        source_version: str,
        target_version: str,
        original_payload: Any,
    ) -> PatchValidationResult:
        """
        Validates whether a safe, explicit transformation exists from source to target version
        and whether the payload contains valid, convertible data.
        """
        # Ensure payload is a dictionary
        if not isinstance(original_payload, dict):
            return PatchValidationResult(
                is_valid=False,
                reason=f"Payload must be a dictionary, got {type(original_payload).__name__}",
            )

        # Check for prohibited security field injection
        for key in original_payload.keys():
            key_lower = str(key).lower()
            if any(sec in key_lower for sec in cls.RESTRICTED_SECURITY_FIELDS):
                return PatchValidationResult(
                    is_valid=False,
                    reason=f"Security violation: payload contains unauthorized security field '{key}'",
                )

        # Explicit known transformation: v1 -> v2 (Student registration)
        if source_version == SchemaVersion.V1.value and target_version == SchemaVersion.V2.value:
            if "user_id" not in original_payload:
                return PatchValidationResult(
                    is_valid=False,
                    reason="Incompatible payload: missing required source field 'user_id'",
                )

            user_id_raw = original_payload["user_id"]

            # Target v2 requires target.id to be an integer
            try:
                # Attempt integer conversion
                int_id = int(user_id_raw)
            except (ValueError, TypeError) as exc:
                return PatchValidationResult(
                    is_valid=False,
                    reason=(
                        f"Incompatible data: 'user_id' value '{user_id_raw}' cannot be "
                        f"converted to integer for target schema v2: {exc}"
                    ),
                    error_details=str(exc),
                )

            # Construct proposed transformed payload
            proposed_payload = {
                "target": {
                    "id": int_id
                }
            }

            # Strictly validate the proposed payload against the target Pydantic model
            return cls.validate_transformed_payload(target_version, proposed_payload)

        # Fallback: Arbitrary unverified schema changes are rejected
        return PatchValidationResult(
            is_valid=False,
            reason=(
                f"No verified transformation patch available for "
                f"migration from '{source_version}' to '{target_version}'"
            ),
        )

    @classmethod
    def validate_transformed_payload(
        cls,
        target_version: str,
        transformed_payload: Dict[str, Any],
    ) -> PatchValidationResult:
        """
        Validates that a transformed payload strictly adheres to the target version's model.
        """
        if target_version == SchemaVersion.V2.value:
            try:
                validated_model = StudentRequestV2.model_validate(transformed_payload)
                return PatchValidationResult(
                    is_valid=True,
                    reason="Payload successfully transformed and verified against StudentRequestV2.",
                    transformed_payload=validated_model.model_dump(),
                )
            except ValidationError as exc:
                return PatchValidationResult(
                    is_valid=False,
                    reason=f"Transformed payload failed validation against StudentRequestV2: {exc.errors()}",
                    error_details=exc.errors(),
                )

        elif target_version == SchemaVersion.V1.value:
            try:
                validated_model = StudentRequestV1.model_validate(transformed_payload)
                return PatchValidationResult(
                    is_valid=True,
                    reason="Payload successfully verified against StudentRequestV1.",
                    transformed_payload=validated_model.model_dump(),
                )
            except ValidationError as exc:
                return PatchValidationResult(
                    is_valid=False,
                    reason=f"Transformed payload failed validation against StudentRequestV1: {exc.errors()}",
                    error_details=exc.errors(),
                )

        return PatchValidationResult(
            is_valid=False,
            reason=f"Unrecognized target schema version: '{target_version}'",
        )
