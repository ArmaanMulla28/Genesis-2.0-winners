"""
audit.py - Structured Audit Event Logger for Self-Healing API Operations.

Maintains an immutable record of recovery attempts, schema drift events,
patch validation decisions, retry counters, and final outcomes.
Safeguards privacy by sanitizing sensitive fields before logging.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class AuditEvent:
    """Represents a structured record of a single recovery event."""
    event_id: str
    timestamp: str
    tool_name: str
    endpoint: str
    method: str
    previous_schema_version: str
    target_schema_version: str
    original_payload: Dict[str, Any]
    transformed_payload: Optional[Dict[str, Any]]
    failure_reason: str
    patch_decision: str
    retry_count: int
    max_retries: int
    final_outcome: str  # e.g., "SUCCESS", "REJECTED", "FAILED", "RETRY_LIMIT_EXCEEDED"
    error_detail: Optional[str] = None


class AuditLogger:
    """
    In-memory audit trail recorder.
    """

    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def record_event(
        self,
        tool_name: str,
        endpoint: str,
        method: str,
        previous_schema_version: str,
        target_schema_version: str,
        original_payload: Any,
        transformed_payload: Optional[Dict[str, Any]],
        failure_reason: str,
        patch_decision: str,
        retry_count: int,
        max_retries: int,
        final_outcome: str,
        error_detail: Optional[str] = None,
    ) -> AuditEvent:
        """Create and store a sanitized structured audit entry."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_name=tool_name,
            endpoint=endpoint,
            method=method.upper(),
            previous_schema_version=previous_schema_version,
            target_schema_version=target_schema_version,
            original_payload=self._sanitize(original_payload),
            transformed_payload=self._sanitize(transformed_payload) if transformed_payload else None,
            failure_reason=failure_reason,
            patch_decision=patch_decision,
            retry_count=retry_count,
            max_retries=max_retries,
            final_outcome=final_outcome,
            error_detail=error_detail,
        )
        self._events.append(event)
        return event

    def get_events(self) -> List[Dict[str, Any]]:
        """Return all recorded audit events as JSON-serializable dictionaries."""
        return [asdict(e) for e in self._events]

    def clear(self) -> None:
        """Reset the audit log (useful for testing and reset-api)."""
        self._events.clear()

    @staticmethod
    def _sanitize(payload: Any) -> Any:
        """
        Redacts sensitive tokens, passwords, or keys from log payloads.
        """
        if not isinstance(payload, dict):
            return payload

        sanitized: Dict[str, Any] = {}
        sensitive_keywords = {"password", "secret", "token", "auth", "key", "credential"}

        for k, v in payload.items():
            if any(word in str(k).lower() for word in sensitive_keywords):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, dict):
                sanitized[k] = AuditLogger._sanitize(v)
            elif isinstance(v, list):
                sanitized[k] = [AuditLogger._sanitize(item) for item in v]
            else:
                sanitized[k] = v
        return sanitized


# Global in-memory singleton
audit_logger = AuditLogger()
