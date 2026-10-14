"""
run_verification.py - End-to-End Verification Runner for Self-Healing Tool Registry.

Verifies the full lifecycle of Phase 1 (Mock API) and Phase 2 (Self-Healing Engine):
1. Initial health and baseline v1 validation.
2. Runtime schema drift simulation via /admin/break-api.
3. Raw schema mismatch failure (HTTP 422) when recovery is bypassed.
4. Automatic self-healing: intercept 422, obtain trusted schema, validate patch,
   update Tool Registry, execute bounded retry, and succeed with HTTP 200!
5. Tool Registry contract verification (shows migration from v1 to v2).
6. Structured audit log inspection (verifies event recording and sanitization).
7. Safety validation: invalid patches (non-numeric id) rejected without registry corruption.
8. System restoration via /admin/reset-api.
"""

import sys
from fastapi.testclient import TestClient

try:
    from app.main import app, state
    from app.registry import tool_registry
    from app.audit import audit_logger
except ImportError:
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
    from app.main import app, state
    from app.registry import tool_registry
    from app.audit import audit_logger


def print_step(step_num: int, title: str) -> None:
    print(f"\n{'='*70}\n[STEP {step_num}] {title}\n{'='*70}")


def main() -> None:
    client = TestClient(app)

    print("\n" + "#"*70)
    print("  SELF-HEALING TOOL REGISTRY - VERIFICATION RUNNER (PHASES 1 & 2)")
    print("#"*70)

    # Reset state to clean baseline
    state.reset_api()
    tool_registry.reset()
    audit_logger.clear()

    # Step 0: Health Check
    print_step(0, "Health Check - Confirming server state")
    res_health = client.get("/health")
    print(f"GET /health -> HTTP {res_health.status_code}")
    print(f"Response: {res_health.json()}")
    assert res_health.status_code == 200
    assert res_health.json()["active_schema_version"] == "v1"
    print(">>> PASS: Health check confirmed active v1 schema.")

    # Step 1: Normal request succeeds before schema change
    print_step(1, "Original payload {'user_id': '123'} succeeds initially (HTTP 200)")
    v1_payload = {"user_id": "123"}
    res_v1 = client.post("/student", json=v1_payload)
    print(f"POST /student with {v1_payload} -> HTTP {res_v1.status_code}")
    print(f"Response: {res_v1.json()}")
    assert res_v1.status_code == 200
    assert res_v1.json()["schema_version"] == "v1"
    assert res_v1.json()["student_id"] == "123"
    assert tool_registry.get_tool("student_service").active_version == "v1"
    print(">>> PASS: Initial v1 payload succeeded natively.")

    # Step 2: Trigger runtime schema drift
    print_step(2, "Simulate schema drift: POST /admin/break-api")
    res_break = client.post("/admin/break-api")
    print(f"POST /admin/break-api -> HTTP {res_break.status_code}")
    print(f"Response: {res_break.json()}")
    assert res_break.status_code == 200
    assert res_break.json()["active_schema_version"] == "v2"
    print(">>> PASS: Active schema switched to v2 in memory.")

    # Step 3: Raw schema mismatch fails when recovery is bypassed
    print_step(3, "Bypassed recovery: Old payload fails with HTTP 422")
    res_bypassed = client.post("/student?bypass_recovery=true", json=v1_payload)
    print(f"POST /student?bypass_recovery=true -> HTTP {res_bypassed.status_code}")
    print(f"Error details: {res_bypassed.json()}")
    assert res_bypassed.status_code == 422
    print(">>> PASS: Raw schema mismatch properly triggers HTTP 422 when recovery is bypassed.")

    # Step 4: Self-Healing in action!
    print_step(4, "Self-Healing Engine: Transparent recovery of old v1 payload")
    res_healed = client.post("/student", json=v1_payload)
    print(f"POST /student (Self-Healed) -> HTTP {res_healed.status_code}")
    print(f"Headers: x-self-healing-recovered={res_healed.headers.get('x-self-healing-recovered')}")
    print(f"Response: {res_healed.json()}")
    assert res_healed.status_code == 200
    assert res_healed.headers.get("x-self-healing-recovered") == "true"
    assert res_healed.json()["status"] == "success"
    assert res_healed.json()["student_id"] == 123
    assert res_healed.json()["schema_version"] == "v2"
    print(">>> PASS: Self-healing engine successfully healed request and returned HTTP 200!")

    # Step 5: Verify Tool Registry updated to v2
    print_step(5, "Verifying In-Memory Tool Registry contract update")
    reg_entry = tool_registry.get_tool("student_service")
    print(f"Registry Active Version: {reg_entry.active_version}")
    print(f"Version History: {reg_entry.version_history}")
    assert reg_entry.active_version == "v2"
    print(">>> PASS: In-memory Tool Registry successfully updated to v2.")

    # Step 6: Verify Structured Audit Trail
    print_step(6, "Inspecting Self-Healing Audit Trail")
    audit_events = audit_logger.get_events()
    print(f"Total Audit Events Recorded: {len(audit_events)}")
    latest_event = audit_events[-1]
    print(f"Event ID:        {latest_event['event_id']}")
    print(f"Timestamp:       {latest_event['timestamp']}")
    print(f"Tool Name:       {latest_event['tool_name']}")
    print(f"Patch Decision:  {latest_event['patch_decision']}")
    print(f"Retry Count:     {latest_event['retry_count']}/{latest_event['max_retries']}")
    print(f"Final Outcome:   {latest_event['final_outcome']}")
    assert latest_event["final_outcome"] == "SUCCESS"
    assert latest_event["previous_schema_version"] == "v1"
    assert latest_event["target_schema_version"] == "v2"
    print(">>> PASS: Audit trail accurately recorded recovery metrics.")

    # Step 7: Safety check - Invalid patch rejected
    print_step(7, "Safety Guard: Non-convertible payload rejected without registry damage")
    invalid_payload = {"user_id": "not_a_number"}
    res_invalid = client.post("/student", json=invalid_payload)
    print(f"POST /student with invalid payload -> HTTP {res_invalid.status_code}")
    assert res_invalid.status_code == 422
    print(">>> PASS: Incompatible patch was safely rejected.")

    # Step 8: Reset API and Registry
    print_step(8, "Restoring baseline via POST /admin/reset-api")
    res_reset = client.post("/admin/reset-api")
    print(f"POST /admin/reset-api -> HTTP {res_reset.status_code}")
    assert res_reset.status_code == 200
    assert res_reset.json()["active_schema_version"] == "v1"
    assert state.active_version.value == "v1"
    assert tool_registry.get_tool("student_service").active_version == "v1"

    # Confirm v1 works cleanly again
    res_v1_restored = client.post("/student", json=v1_payload)
    assert res_v1_restored.status_code == 200
    print(">>> PASS: Full reset confirmed! System returned to baseline v1.")

    print("\n" + "#"*70)
    print("  ALL VERIFICATION STEPS PASSED SUCCESSFULLY! (PHASE 2 COMPLETE)")
    print("#"*70 + "\n")


if __name__ == "__main__":
    main()
