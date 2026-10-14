"""
test_api.py - Verification tests for Phase 1 Mock API Server.

Tests the full lifecycle:
1. Health check verifies server is active.
2. Initial state: v1 payload {"user_id": "123"} succeeds (200).
3. Initial state: v2 payload {"target": {"id": 123}} fails (422).
4. POST /admin/break-api switches schema to v2.
5. Post-break: v1 payload {"user_id": "123"} now fails (422).
6. Post-break: v2 payload {"target": {"id": 123}} succeeds (200).
7. GET /schema reports active version as v2 and reflects target.id format.
8. POST /admin/reset-api restores original v1 schema.
9. Post-reset: v1 payload succeeds again (200) and v2 payload fails (422).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app, state
from app.registry import tool_registry


@pytest.fixture(autouse=True)
def reset_api_state():
    """Ensure state and registry are reset to v1 before every test."""
    state.reset_api()
    tool_registry.reset()
    yield
    state.reset_api()
    tool_registry.reset()


client = TestClient(app)


def test_health_endpoint():
    """Test GET /health returns 200 with status ok and active schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["active_schema_version"] == "v1"
    assert data["service"] == "self-healing-mock-api"


def test_schema_endpoint_v1():
    """Test GET /schema returns active v1 schema metadata and definitions."""
    response = client.get("/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["active_version"] == "v1"
    assert data["schema_name"] == "StudentRequestV1"
    assert data["expected_format"] == {"user_id": "123"}
    assert "user_id" in data["json_schema"]["properties"]
    assert "v1" in data["version_definitions"]
    assert "v2" in data["version_definitions"]


def test_student_v1_success():
    """Step 1: Original payload succeeds in initial v1 state."""
    payload = {"user_id": "123"}
    response = client.post("/student", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["student_id"] == "123"
    assert data["schema_version"] == "v1"
    assert data["data"] == {"user_id": "123"}


def test_student_v2_payload_fails_in_v1_state():
    """In v1 state, sending a v2 payload must fail with HTTP 422."""
    payload = {"target": {"id": 123}}
    response = client.post("/student", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # Should flag missing user_id and/or forbidden target
    errors = data["detail"]
    error_locs = [tuple(err["loc"]) for err in errors]
    assert any("user_id" in loc for loc in error_locs)


def test_admin_break_api():
    """Step 2: Calling /admin/break-api switches the schema to v2."""
    response = client.post("/admin/break-api")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["previous_schema_version"] == "v1"
    assert data["active_schema_version"] == "v2"
    assert data["expected_format"] == {"target": {"id": 123}}


def test_schema_endpoint_after_break():
    """Step 5: /schema reports the changed schema after /admin/break-api."""
    client.post("/admin/break-api")
    response = client.get("/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["active_version"] == "v2"
    assert data["schema_name"] == "StudentRequestV2"
    assert data["expected_format"] == {"target": {"id": 123}}
    assert "target" in data["json_schema"]["properties"]


def test_post_break_v1_fails_and_v2_succeeds():
    """
    Steps 3 & 4:
    After /admin/break-api:
    - Original v1 payload fails with HTTP 422.
    - Changed v2 payload succeeds with HTTP 200.
    """
    client.post("/admin/break-api")

    # Step 3: Original payload now fails with HTTP 422 when recovery is bypassed
    v1_payload = {"user_id": "123"}
    fail_response = client.post("/student?bypass_recovery=true", json=v1_payload)
    assert fail_response.status_code == 422
    fail_data = fail_response.json()
    assert "detail" in fail_data

    # Step 4: Changed payload succeeds with HTTP 200
    v2_payload = {"target": {"id": 123}}
    success_response = client.post("/student", json=v2_payload)
    assert success_response.status_code == 200
    success_data = success_response.json()
    assert success_data["status"] == "success"
    assert success_data["student_id"] == 123
    assert success_data["schema_version"] == "v2"
    assert success_data["data"] == {"target": {"id": 123}}


def test_admin_reset_api_restores_original_behavior():
    """
    Step 6: Calling /admin/reset-api restores the original behavior.
    Allows demo cycle to be repeated cleanly.
    """
    # Break first
    client.post("/admin/break-api")
    assert client.get("/health").json()["active_schema_version"] == "v2"

    # Reset
    reset_response = client.post("/admin/reset-api")
    assert reset_response.status_code == 200
    reset_data = reset_response.json()
    assert reset_data["status"] == "success"
    assert reset_data["previous_schema_version"] == "v2"
    assert reset_data["active_schema_version"] == "v1"

    # Verify v1 payload succeeds again
    v1_response = client.post("/student", json={"user_id": "123"})
    assert v1_response.status_code == 200
    assert v1_response.json()["schema_version"] == "v1"

    # Verify v2 payload fails again
    v2_response = client.post("/student", json={"target": {"id": 123}})
    assert v2_response.status_code == 422


def test_invalid_payload_types():
    """Verify non-dict payload types return HTTP 422 cleanly."""
    for bad_input in [["item"], "just_a_string", 12345]:
        response = client.post("/student", json=bad_input)
        assert response.status_code == 422
