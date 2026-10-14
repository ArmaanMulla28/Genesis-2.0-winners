"""
audit.py - Structured Audit Event Logger for Self-Healing API Operations.

Maintains an immutable record of recovery attempts, schema drift events,
patch validation decisions, retry counters, final HTTP statuses, and recovery timings.
Safeguards privacy by sanitizing sensitive fields before logging.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class AuditEvent:
    """Represents a structured record of a single recovery attempt."""
    event_id: str
    attempt_id: str
    timestamp: str
    tool_name: str
    endpoint: str
    method: str
    original_schema_version: str
    previous_schema_version: str
    target_schema_version: Optional[str]
    original_payload: Dict[str, Any]
    transformed_payload: Optional[Dict[str, Any]]
    failure_reason: str
    patch_validation_result: Dict[str, Any]
    patch_decision: str
    retry_count: int
    max_retries: int
    final_http_status: int
    recovery_outcome: str  # "SUCCESS", "REJECTED", "FAILED", "RETRY_LIMIT_EXCEEDED"
    final_outcome: str     # Backward compatibility alias for recovery_outcome
    elapsed_time_ms: float
    error_detail: Optional[str] = None


class AuditLogger:
    """
    In-memory audit trail recorder.
    Designed with a clean interface so persistent storage (e.g., PostgreSQL)
    can be attached without altering the recovery engine.
    """

    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def record_event(
        self,
        tool_name: str,
        endpoint: str,
        method: str,
        previous_schema_version: str,
        target_schema_version: Optional[str],
        original_payload: Any,
        transformed_payload: Optional[Dict[str, Any]],
        failure_reason: str,
        patch_decision: str,
        retry_count: int,
        max_retries: int,
        final_outcome: str,
        final_http_status: int = 422,
        elapsed_time_ms: float = 0.0,
        patch_validation_result: Optional[Dict[str, Any]] = None,
        error_detail: Optional[str] = None,
    ) -> AuditEvent:
        """Create and store a sanitized structured audit entry."""
        unique_id = str(uuid.uuid4())
        event = AuditEvent(
            event_id=unique_id,
            attempt_id=unique_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_name=tool_name,
            endpoint=endpoint,
            method=method.upper(),
            original_schema_version=previous_schema_version,
            previous_schema_version=previous_schema_version,
            target_schema_version=target_schema_version,
            original_payload=self._sanitize(original_payload),
            transformed_payload=self._sanitize(transformed_payload) if transformed_payload else None,
            failure_reason=failure_reason,
            patch_validation_result=patch_validation_result or {"status": patch_decision},
            patch_decision=patch_decision,
            retry_count=retry_count,
            max_retries=max_retries,
            final_http_status=final_http_status,
            recovery_outcome=final_outcome,
            final_outcome=final_outcome,
            elapsed_time_ms=round(elapsed_time_ms, 2),
            error_detail=error_detail,
        )
        self._events.append(event)
        return event

    def get_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return all recorded audit events as JSON-serializable dictionaries."""
        events = [asdict(e) for e in self._events]
        if limit is not None and limit > 0:
            return events[-limit:]
        return events

    def clear(self) -> None:
        """Reset the audit log (useful for testing and reset-api)."""
        self._events.clear()

    @staticmethod
    def _sanitize(payload: Any) -> Any:
        """
        Redacts sensitive tokens, passwords, authorization headers, or keys.
        """
        if not isinstance(payload, dict):
            return payload

        sanitized: Dict[str, Any] = {}
        sensitive_keywords = {
            "password",
            "secret",
            "token",
            "auth",
            "key",
            "credential",
            "authorization",
            "bearer",
            "api_key",
        }

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
