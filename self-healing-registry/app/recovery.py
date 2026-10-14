"""
recovery.py - Self-Healing Middleware and Recovery Coordination Engine.

Coordinates the end-to-end self-healing lifecycle:
1. Intercepts schema validation failures (HTTP 422).
2. Checks bounded retry guardrails (strictly maximum 1 retry).
3. Fetches the trusted active schema from the authoritative schema registry.
4. Proposes a known, safe transformation patch.
5. Validates the patch and transformed payload against the target model.
6. Updates the in-memory tool registry ONLY after successful validation.
7. Retries the request with the transformed payload.
8. Records detailed structured audit events for every attempt.
"""

import json
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs

from app.audit import audit_logger
from app.models import SchemaVersion
from app.registry import tool_registry
from app.validator import SchemaPatchValidator


class RecoveryResult:
    """Result data structure returned by the RecoveryCoordinator."""

    def __init__(
        self,
        success: bool,
        reason: str,
        transformed_payload: Optional[Dict[str, Any]] = None,
        previous_version: Optional[str] = None,
        target_version: Optional[str] = None,
        patch_decision: Optional[str] = None,
    ) -> None:
        self.success = success
        self.reason = reason
        self.transformed_payload = transformed_payload
        self.previous_version = previous_version
        self.target_version = target_version
        self.patch_decision = patch_decision


class RecoveryCoordinator:
    """
    Coordinates trusted schema discovery, patch evaluation, registry updates,
    and bounded retries.
    """

    MAX_RETRIES: int = 1

    def __init__(self, state_manager: Any) -> None:
        # References the active server state manager for trusted schema retrieval
        self.state_manager = state_manager

    def attempt_recovery(
        self,
        tool_name: str,
        endpoint: str,
        method: str,
        original_payload: Any,
        current_retry_count: int = 0,
    ) -> RecoveryResult:
        """
        Coordinates the recovery attempt for a failed request.
        """
        # 1. Enforce strict bounded retry limit
        if current_retry_count >= self.MAX_RETRIES:
            reason = f"Retry limit exceeded: already attempted {current_retry_count} retries (max {self.MAX_RETRIES})"
            audit_logger.record_event(
                tool_name=tool_name,
                endpoint=endpoint,
                method=method,
                previous_schema_version="unknown",
                target_schema_version=self.state_manager.active_version.value,
                original_payload=original_payload,
                transformed_payload=None,
                failure_reason="schema_mismatch_422",
                patch_decision="ABORTED_RETRY_LIMIT_EXCEEDED",
                retry_count=current_retry_count,
                max_retries=self.MAX_RETRIES,
                final_outcome="RETRY_LIMIT_EXCEEDED",
                error_detail=reason,
            )
            return RecoveryResult(success=False, reason=reason)

        # 2. Retrieve trusted active schema from the authoritative state
        # (Never infer schema solely from an HTTP error response)
        trusted_schema_summary = self.state_manager.get_schema_summary()
        target_version = trusted_schema_summary.active_version
        target_schema = trusted_schema_summary.json_schema

        # 3. Lookup current known schema in the Tool Registry
        registry_entry = tool_registry.get_tool(tool_name)
        source_version = registry_entry.active_version if registry_entry else SchemaVersion.V1.value

        # Check if the registry is already aligned with the target schema
        if source_version == target_version:
            # Payload simply violated current schema rules, no drift occurred
            reason = f"No schema drift detected. Registry and server are both on version '{target_version}'."
            audit_logger.record_event(
                tool_name=tool_name,
                endpoint=endpoint,
                method=method,
                previous_schema_version=source_version,
                target_schema_version=target_version,
                original_payload=original_payload,
                transformed_payload=None,
                failure_reason="validation_error_no_drift",
                patch_decision="NO_ACTION_VERSIONS_MATCH",
                retry_count=current_retry_count,
                max_retries=self.MAX_RETRIES,
                final_outcome="REJECTED",
                error_detail=reason,
            )
            return RecoveryResult(success=False, reason=reason)

        # 4. Propose and validate transformation patch
        patch_decision = f"PROPOSED_KNOWN_MIGRATION_{source_version.upper()}_TO_{target_version.upper()}"
        validation_result = SchemaPatchValidator.validate_patch_proposal(
            source_version=source_version,
            target_version=target_version,
            original_payload=original_payload,
        )

        # 5. Handle rejected / invalid patches
        if not validation_result.is_valid:
            audit_logger.record_event(
                tool_name=tool_name,
                endpoint=endpoint,
                method=method,
                previous_schema_version=source_version,
                target_schema_version=target_version,
                original_payload=original_payload,
                transformed_payload=None,
                failure_reason="schema_mismatch_422",
                patch_decision=f"REJECTED_INVALID_PATCH: {validation_result.reason}",
                retry_count=current_retry_count,
                max_retries=self.MAX_RETRIES,
                final_outcome="REJECTED",
                error_detail=validation_result.reason,
            )
            return RecoveryResult(
                success=False,
                reason=validation_result.reason,
                previous_version=source_version,
                target_version=target_version,
                patch_decision="REJECTED",
            )

        # 6. Patch is verified! Update the in-memory Tool Registry
        tool_registry.update_tool_version(
            tool_name=tool_name,
            new_version=target_version,
            new_schema=target_schema,
            reason=f"self_healed_from_{source_version}_to_{target_version}",
        )

        # 7. Record successful audit event
        audit_logger.record_event(
            tool_name=tool_name,
            endpoint=endpoint,
            method=method,
            previous_schema_version=source_version,
            target_schema_version=target_version,
            original_payload=original_payload,
            transformed_payload=validation_result.transformed_payload,
            failure_reason="schema_mismatch_422",
            patch_decision=f"APPLIED_AND_VERIFIED_{source_version.upper()}_TO_{target_version.upper()}",
            retry_count=current_retry_count + 1,
            max_retries=self.MAX_RETRIES,
            final_outcome="SUCCESS",
            error_detail=None,
        )

        return RecoveryResult(
            success=True,
            reason="Recovery successful: payload transformed and registry updated.",
            transformed_payload=validation_result.transformed_payload,
            previous_version=source_version,
            target_version=target_version,
            patch_decision=patch_decision,
        )


class SelfHealingASGIMiddleware:
    """
    Pure ASGI Middleware that transparently intercepts schema mismatches on
    monitored endpoints, executes safe self-healing recovery, and retries the request.
    """

    def __init__(self, app: Any, coordinator: RecoveryCoordinator) -> None:
        self.app = app
        self.coordinator = coordinator

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "GET").upper()

        # Only intercept healable endpoints (POST /student)
        if path != "/student" or method != "POST":
            await self.app(scope, receive, send)
            return

        # Check for recovery bypass flag in headers or query parameters
        headers_dict = {k.decode("latin1").lower(): v.decode("latin1") for k, v in scope.get("headers", [])}
        query_string = scope.get("query_string", b"").decode("latin1")
        query_params = parse_qs(query_string)

        bypass_header = (
            headers_dict.get("x-bypass-recovery", "").lower() in ("true", "1", "yes")
            or headers_dict.get("x-self-healing", "").lower() in ("false", "0", "no")
        )
        bypass_query = "bypass_recovery" in query_params and query_params["bypass_recovery"][0].lower() in ("true", "1", "yes")

        if bypass_header or bypass_query:
            # Bypass self-healing: caller receives raw API response directly
            await self.app(scope, receive, send)
            return

        # Read and buffer full request body
        body_bytes = b""
        more_body = True
        while more_body:
            message = await receive()
            body_bytes += message.get("body", b"")
            more_body = message.get("more_body", False)

        async def initial_receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        # Intercept initial response from the application
        captured_status: Optional[int] = None
        captured_headers: list = []
        captured_messages: list = []

        async def capture_send(message: Any) -> None:
            nonlocal captured_status, captured_headers
            if message["type"] == "http.response.start":
                captured_status = message["status"]
                captured_headers = message.get("headers", [])
            captured_messages.append(message)

        # First attempt
        await self.app(scope, initial_receive, capture_send)

        # If response is NOT 422, request succeeded or has non-schema error; return immediately
        if captured_status != 422:
            for msg in captured_messages:
                await send(msg)
            return

        # Attempt self-healing recovery on HTTP 422
        try:
            original_payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            original_payload = {}

        current_retry = int(headers_dict.get("x-retry-count", "0"))

        recovery_result = self.coordinator.attempt_recovery(
            tool_name="student_service",
            endpoint=path,
            method=method,
            original_payload=original_payload,
            current_retry_count=current_retry,
        )

        if not recovery_result.success:
            # Recovery failed or was rejected: emit captured 422 response
            for msg in captured_messages:
                await send(msg)
            return

        # Recovery succeeded: execute bounded retry with transformed payload
        transformed_bytes = json.dumps(recovery_result.transformed_payload).encode("utf-8")

        async def retry_receive():
            return {"type": "http.request", "body": transformed_bytes, "more_body": False}

        # Update headers for retry scope
        new_headers = []
        for k, v in scope.get("headers", []):
            k_lower = k.lower()
            if k_lower != b"content-length" and k_lower != b"x-retry-count":
                new_headers.append((k, v))

        new_headers.append((b"content-length", str(len(transformed_bytes)).encode("latin1")))
        new_headers.append((b"x-retry-count", str(current_retry + 1).encode("latin1")))
        new_headers.append((b"x-self-healing-applied", b"true"))
        scope["headers"] = new_headers

        # Re-dispatch request with new body to the application
        # Wrap send to add self-healing recovery metadata headers in response
        async def enhanced_send(message: Any) -> None:
            if message["type"] == "http.response.start":
                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-self-healing-recovered", b"true"))
                resp_headers.append((b"x-self-healing-version", recovery_result.target_version.encode("latin1")))
                message["headers"] = resp_headers
            await send(message)

        await self.app(scope, retry_receive, enhanced_send)
