"""
test_evaluation.py - Evaluation, Audit Logging, and Reliability Test Suite (Phase 3).

Verifies the 10 core evaluation scenarios:
1. Normal API request without schema drift.
2. Schema changes and successful automatic recovery.
3. Recovery using a trusted current schema.
4. Invalid patch rejection.
5. Incompatible request transformation.
6. Retry limit enforcement.
7. Registry remains unchanged after a rejected patch.
8. Recovery failure is logged correctly.
9. API reset restores the initial schema.
10. Repeated test runs produce consistent results.

Also tests:
- GET /admin/audit-logs: recent events, sanitization, attempt IDs.
- GET /admin/metrics: adaptation rate, MTTR, retries, and empty dataset handling.
"""

import pytest
from fastapi.testclient import TestClient

from app.audit import audit_logger
from app.main import app, state
from app.registry import tool_registry


@pytest.fixture(autouse=True)
def reset_environment():
    """Ensure state, registry, and audit trail are clean before and after each test."""
    state.reset_api()
    tool_registry.reset()
    audit_logger.clear()
    yield
    state.reset_api()
    tool_registry.reset()
    audit_logger.clear()


client = TestClient(app)


def test_eval_1_normal_api_request_without_schema_drift():
    """
    Scenario 1: Normal API request without schema drift.
    Ordinary successful requests should succeed with HTTP 200 and NOT be counted
    as recovery attempts in the metrics denominator.
    """
    res = client.post("/student", json={"user_id": "123"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["schema_version"] == "v1"
    assert data["student_id"] == "123"

    # Verify no recovery attempt was logged
    metrics_res = client.get("/admin/metrics")
    metrics = metrics_res.json()
    assert metrics["total_recovery_attempts"] == 0
    assert metrics["eligible_recovery_attempts"] == 0
    assert metrics["adaptation_rate"] == 0.0


def test_eval_2_schema_change_and_successful_automatic_recovery():
    """
    Scenario 2: Schema changes and successful automatic recovery.
    After /admin/break-api, an old v1 request is transparently recovered to v2.
    """
    client.post("/admin/break-api")

    res = client.post("/student", json={"user_id": "456"})
    assert res.status_code == 200
    assert res.headers.get("x-self-healing-recovered") == "true"
    data = res.json()
    assert data["status"] == "success"
    assert data["schema_version"] == "v2"
    assert data["student_id"] == 456

    # Verify metrics reflect the successful recovery
    metrics = client.get("/admin/metrics").json()
    assert metrics["total_recovery_attempts"] == 1
    assert metrics["successful_recoveries"] == 1
    assert metrics["failed_recoveries"] == 0
    assert metrics["adaptation_rate"] == 100.0
    assert metrics["mean_time_to_recovery_ms"] > 0.0
    assert metrics["average_retry_count"] == 1.0


def test_eval_3_recovery_using_trusted_current_schema():
    """
    Scenario 3: Recovery using a trusted current schema.
    Verifies the recovery engine inspects /schema rather than guessing from an error.
    """
    client.post("/admin/break-api")

    # Authoritative schema is v2
    schema_res = client.get("/schema")
    assert schema_res.status_code == 200
    assert schema_res.json()["active_version"] == "v2"

    # Recovery coordinates against that trusted schema
    res = client.post("/student", json={"user_id": "789"})
    assert res.status_code == 200

    # Audit log confirms target schema version matches trusted schema
    audit_res = client.get("/admin/audit-logs")
    events = audit_res.json()["events"]
    assert len(events) == 1
    assert events[0]["target_schema_version"] == "v2"
    assert events[0]["previous_schema_version"] == "v1"


def test_eval_4_invalid_patch_rejection():
    """
    Scenario 4: Invalid patch rejection.
    Rejects patches attempting to inject prohibited security headers, tokens, or invalid structures.
    """
    client.post("/admin/break-api")

    # Attempt to inject unauthorized security tokens
    malicious_payload = {"user_id": "123", "bearer_token": "secret_abc"}
    res = client.post("/student", json=malicious_payload)
    assert res.status_code == 422

    # Verify rejection was logged
    audit_res = client.get("/admin/audit-logs")
    events = audit_res.json()["events"]
    assert len(events) == 1
    assert events[0]["recovery_outcome"] == "REJECTED"
    assert "Security violation" in events[0]["error_detail"]


def test_eval_5_incompatible_request_transformation():
    """
    Scenario 5: Incompatible request transformation.
    When a v1 payload contains a non-numeric string ('alpha_user') that cannot
    be transformed to an integer target.id for v2, recovery must fail safely.
    """
    client.post("/admin/break-api")

    res = client.post("/student", json={"user_id": "alpha_user_non_int"})
    assert res.status_code == 422

    # Verify audit trail recorded failure
    metrics = client.get("/admin/metrics").json()
    assert metrics["total_recovery_attempts"] == 1
    assert metrics["successful_recoveries"] == 0
    assert metrics["failed_recoveries"] == 1
    assert metrics["patch_rejection_count"] == 1
    assert metrics["adaptation_rate"] == 0.0


def test_eval_6_retry_limit_enforcement():
    """
    Scenario 6: Retry limit enforcement.
    Ensures bounded retry: if the request already has reached the retry limit,
    the engine does not loop or retry indefinitely.
    """
    client.post("/admin/break-api")

    # Incoming request simulating already exhausted retry limit
    res = client.post(
        "/student",
        json={"user_id": "cannot_heal_abc"},
        headers={"X-Retry-Count": "1"},
    )
    assert res.status_code == 422

    events = client.get("/admin/audit-logs").json()["events"]
    assert len(events) == 1
    assert events[0]["recovery_outcome"] == "RETRY_LIMIT_EXCEEDED"
    assert events[0]["max_retries"] == 1


def test_eval_7_registry_remains_unchanged_after_rejected_patch():
    """
    Scenario 7: Registry remains unchanged after a rejected patch.
    Ensures tool registry is updated ONLY upon successful validation.
    """
    client.post("/admin/break-api")

    # Send incompatible request
    client.post("/student", json={"user_id": "incompatible_string"})

    # Registry must STILL be on v1!
    reg_res = client.get("/registry").json()
    assert reg_res["registry"]["student_service"]["active_version"] == "v1"


def test_eval_8_recovery_failure_is_logged_correctly():
    """
    Scenario 8: Recovery failure is logged correctly.
    Verifies all required structured fields in audit logs for failure cases.
    """
    client.post("/admin/break-api")

    client.post("/student", json={"user_id": "xyz"})

    audit_res = client.get("/admin/audit-logs")
    data = audit_res.json()
    assert data["total_events"] == 1
    event = data["events"][0]

    # Verify required structured fields
    assert "event_id" in event or "attempt_id" in event
    assert "timestamp" in event
    assert event["tool_name"] == "student_service"
    assert event["endpoint"] == "/student"
    assert event["original_schema_version"] == "v1"
    assert event["target_schema_version"] == "v2"
    assert event["failure_reason"] == "schema_mismatch_422"
    assert "patch_validation_result" in event
    assert event["retry_count"] == 0
    assert event["final_http_status"] == 422
    assert event["recovery_outcome"] == "REJECTED"
    assert event["elapsed_time_ms"] >= 0.0


def test_eval_9_api_reset_restores_initial_schema():
    """
    Scenario 9: API reset restores initial schema and clears registry/audit.
    """
    client.post("/admin/break-api")
    client.post("/student", json={"user_id": "123"})
    assert tool_registry.get_tool("student_service").active_version == "v2"

    # Reset
    reset_res = client.post("/admin/reset-api")
    assert reset_res.status_code == 200

    # Schema is back to v1
    schema_res = client.get("/schema").json()
    assert schema_res["active_version"] == "v1"

    # Registry is back to v1
    reg_res = client.get("/registry").json()
    assert reg_res["registry"]["student_service"]["active_version"] == "v1"

    # Audit trail is reset
    metrics_res = client.get("/admin/metrics").json()
    assert metrics_res["total_recovery_attempts"] == 0


def test_eval_10_repeated_test_runs_produce_consistent_results():
    """
    Scenario 10: Repeated test runs produce consistent results.
    Executes multiple drift -> heal -> reset cycles in sequence.
    """
    for iteration in range(3):
        # 1. Start clean
        client.post("/admin/reset-api")
        v1_res = client.post("/student", json={"user_id": "100"})
        assert v1_res.status_code == 200
        assert v1_res.json()["schema_version"] == "v1"

        # 2. Break
        client.post("/admin/break-api")

        # 3. Heal
        heal_res = client.post("/student", json={"user_id": "200"})
        assert heal_res.status_code == 200
        assert heal_res.json()["schema_version"] == "v2"
        assert heal_res.json()["student_id"] == 200

        # 4. Check metrics
        metrics = client.get("/admin/metrics").json()
        assert metrics["total_recovery_attempts"] == 1
        assert metrics["successful_recoveries"] == 1
        assert metrics["adaptation_rate"] == 100.0


def test_eval_empty_dataset_metrics():
    """
    Verifies that GET /admin/metrics safely handles empty datasets
    without division by zero or errors.
    """
    res = client.get("/admin/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_recovery_attempts"] == 0
    assert data["successful_recoveries"] == 0
    assert data["adaptation_rate"] == 0.0
    assert data["mean_time_to_recovery_ms"] == 0.0
    assert data["average_retry_count"] == 0.0
    assert data["patch_rejection_count"] == 0
    assert data["dataset_status"] == "empty"


def test_eval_audit_sanitization_comprehensive():
    """
    Ensures passwords, tokens, auth keys, and authorization headers are
    never leaked in audit logs.
    """
    client.post("/admin/break-api")

    sensitive_payload = {
        "user_id": "invalid_user",
        "password": "SuperSecretPassword123!",
        "access_token": "jwt.header.payload.signature",
        "api_key": "live_key_999",
    }
    client.post("/student", json=sensitive_payload)

    logs = client.get("/admin/audit-logs").json()["events"]
    assert len(logs) == 1
    logged_payload = logs[0]["original_payload"]
    assert logged_payload["password"] == "[REDACTED]"
    assert logged_payload["access_token"] == "[REDACTED]"
    assert logged_payload["api_key"] == "[REDACTED]"
    assert "SuperSecretPassword123!" not in str(logs)
    assert "jwt.header.payload.signature" not in str(logs)
