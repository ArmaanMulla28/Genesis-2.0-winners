"""
test_recovery.py - Acceptance Tests for Phase 2 Self-Healing Engine.

Verifies:
1. Normal request succeeds before the schema changes.
2. Old-format request fails after schema changes when recovery is bypassed.
3. The self-healing request succeeds after schema changes.
4. The registry reflects the new schema version upon recovery.
5. Invalid patches are rejected without changing the registry.
6. Failed recovery does not cause an infinite retry loop (strict retry limit).
7. /admin/reset-api restores the original schema and resets the registry.
8. /health continues working.
9. Audit logs correctly record recovery events with sanitized payloads.
"""

import pytest
from fastapi.testclient import TestClient

from app.audit import audit_logger
from app.main import app, state
from app.registry import tool_registry


@pytest.fixture(autouse=True)
def reset_system():
    """Ensure state, registry, and audit logs are reset before each test."""
    state.reset_api()
    tool_registry.reset()
    audit_logger.clear()
    yield
    state.reset_api()
    tool_registry.reset()
    audit_logger.clear()


client = TestClient(app)


def test_1_normal_request_succeeds_before_schema_change():
    """
    Acceptance Test 1:
    Normal request succeeds before the schema changes (v1 payload on v1 API).
    """
    v1_payload = {"user_id": "123"}
    response = client.post("/student", json=v1_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["student_id"] == "123"
    assert data["schema_version"] == "v1"

    # Registry remains on v1
    entry = tool_registry.get_tool("student_service")
    assert entry is not None
    assert entry.active_version == "v1"

    # No recovery events were needed
    assert len(audit_logger.get_events()) == 0


def test_2_old_format_fails_when_recovery_is_bypassed():
    """
    Acceptance Test 2:
    Old-format request fails after schema changes when recovery is bypassed.
    Tested via header 'X-Bypass-Recovery: true' and query param '?bypass_recovery=true'.
    """
    # Trigger schema drift
    client.post("/admin/break-api")
    assert state.active_version.value == "v2"

    v1_payload = {"user_id": "123"}

    # Case A: Bypass via header
    res_header_bypass = client.post(
        "/student",
        json=v1_payload,
        headers={"X-Bypass-Recovery": "true"},
    )
    assert res_header_bypass.status_code == 422
    assert "detail" in res_header_bypass.json()

    # Case B: Bypass via query param
    res_query_bypass = client.post(
        "/student?bypass_recovery=true",
        json=v1_payload,
    )
    assert res_query_bypass.status_code == 422
    assert "detail" in res_query_bypass.json()

    # Registry still reflects v1 (unmodified because recovery was bypassed)
    entry = tool_registry.get_tool("student_service")
    assert entry.active_version == "v1"


def test_3_and_4_self_healing_succeeds_and_updates_registry():
    """
    Acceptance Tests 3 & 4:
    3. The self-healing request succeeds after the schema changes.
    4. The registry reflects the new schema version.
    """
    # 1. Simulate API schema drift to v2
    client.post("/admin/break-api")
    assert state.active_version.value == "v2"

    # Tool registry starts on v1
    assert tool_registry.get_tool("student_service").active_version == "v1"

    # 2. Client sends old v1 format request without bypass
    v1_payload = {"user_id": "123"}
    response = client.post("/student", json=v1_payload)

    # 3. Assert self-healing recovered the request successfully!
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Target.id 123 was processed under v2
    assert data["student_id"] == 123
    assert data["schema_version"] == "v2"
    assert data["data"] == {"target": {"id": 123}}

    # 4. Assert response contains self-healing metadata headers
    assert response.headers.get("x-self-healing-recovered") == "true"
    assert response.headers.get("x-self-healing-version") == "v2"

    # 5. Assert Tool Registry was updated to reflect v2
    entry = tool_registry.get_tool("student_service")
    assert entry.active_version == "v2"
    assert len(entry.version_history) >= 2
    assert entry.version_history[-1]["action"] == "self_healed_from_v1_to_v2"

    # 6. Assert audit event recorded the successful recovery
    events = audit_logger.get_events()
    assert len(events) == 1
    event = events[0]
    assert event["final_outcome"] == "SUCCESS"
    assert event["previous_schema_version"] == "v1"
    assert event["target_schema_version"] == "v2"
    assert event["original_payload"] == {"user_id": "123"}
    assert event["transformed_payload"] == {"target": {"id": 123}}
    assert event["retry_count"] == 1


def test_5_invalid_patches_are_rejected_without_changing_registry():
    """
    Acceptance Test 5:
    Invalid patches are rejected without changing the registry.
    e.g., 'user_id' is non-numeric ("abc") so cannot be converted to target integer id.
    """
    client.post("/admin/break-api")

    # Non-convertible payload
    invalid_payload = {"user_id": "abc_not_a_number"}

    response = client.post("/student", json=invalid_payload)
    assert response.status_code == 422

    # Registry must NOT change!
    entry = tool_registry.get_tool("student_service")
    assert entry.active_version == "v1"

    # Audit event records rejection
    events = audit_logger.get_events()
    assert len(events) == 1
    event = events[0]
    assert event["final_outcome"] == "REJECTED"
    assert "cannot be converted to integer" in event["error_detail"]


def test_6_failed_recovery_does_not_cause_infinite_retry():
    """
    Acceptance Test 6:
    Failed recovery does not cause an infinite retry loop.
    Enforces maximum retry limit (max 1 retry).
    """
    client.post("/admin/break-api")

    # If a request comes in with retry count already at 1
    response = client.post(
        "/student",
        json={"user_id": "cannot_heal_non_numeric"},
        headers={"X-Retry-Count": "1"},
    )
    assert response.status_code == 422

    events = audit_logger.get_events()
    assert len(events) == 1
    assert events[0]["final_outcome"] == "RETRY_LIMIT_EXCEEDED"
    assert "Retry limit exceeded" in events[0]["error_detail"]


def test_7_admin_reset_api_restores_original_schema_and_registry():
    """
    Acceptance Test 7:
    /admin/reset-api restores original schema and resets the tool registry.
    """
    # Drift and heal
    client.post("/admin/break-api")
    client.post("/student", json={"user_id": "123"})
    assert tool_registry.get_tool("student_service").active_version == "v2"

    # Reset
    reset_res = client.post("/admin/reset-api")
    assert reset_res.status_code == 200
    assert reset_res.json()["active_schema_version"] == "v1"

    # Server state and tool registry are both restored to v1
    assert state.active_version.value == "v1"
    assert tool_registry.get_tool("student_service").active_version == "v1"

    # V1 payload works natively without healing
    v1_res = client.post("/student", json={"user_id": "123"})
    assert v1_res.status_code == 200
    assert v1_res.json()["schema_version"] == "v1"


def test_8_health_endpoint_continues_working():
    """
    Acceptance Test 8:
    /health continues working in all states.
    """
    # Initial state
    res1 = client.get("/health")
    assert res1.status_code == 200
    assert res1.json()["status"] == "ok"
    assert res1.json()["active_schema_version"] == "v1"

    # After break
    client.post("/admin/break-api")
    res2 = client.get("/health")
    assert res2.status_code == 200
    assert res2.json()["active_schema_version"] == "v2"

    # After reset
    client.post("/admin/reset-api")
    res3 = client.get("/health")
    assert res3.status_code == 200
    assert res3.json()["active_schema_version"] == "v1"


def test_audit_endpoint_and_sanitization():
    """
    Verifies GET /audit returns structured records and redacts sensitive keys.
    """
    client.post("/admin/break-api")

    # Send payload containing a mock sensitive key
    payload_with_secret = {"user_id": "555", "secret_token": "super_secret_123"}
    # Note: validator will reject prohibited security keys as a safety measure
    client.post("/student", json=payload_with_secret)

    audit_res = client.get("/audit")
    assert audit_res.status_code == 200
    data = audit_res.json()
    assert data["total_events"] >= 1

    last_event = data["events"][-1]
    assert "super_secret_123" not in str(last_event)
    assert last_event["original_payload"].get("secret_token") == "[REDACTED]"
