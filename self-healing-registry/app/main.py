"""
main.py - Mock API Server with Integrated Self-Healing Tool Registry Engine.

This module provides the complete FastAPI application for:
"Self-Healing Tool Registry — Automatic Recovery from Runtime API Schema Drift"

Endpoints:
- POST   /student         : Student registration endpoint (healed transparently on drift).
- POST   /admin/break-api : Simulates runtime API drift (switches active schema from v1 to v2).
- POST   /admin/reset-api : Resets active schema and tool registry back to original (v1).
- GET    /schema          : Exposes trusted active schema definition and historical comparisons.
- GET    /registry        : Inspects current in-memory tool registry contracts and versions.
- GET    /audit           : Inspects structured audit trail of all recovery events.
- DELETE /audit           : Clears audit log.
- GET    /health          : Quick health check confirming the server is live.
- GET    /                : Welcome index with quick links to docs and available endpoints.
"""

from typing import Any, Dict, List, Optional, Type
from fastapi import Body, FastAPI, HTTPException, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ValidationError

from app.audit import audit_logger
from app.models import (
    AdminActionResponse,
    HealthResponse,
    SchemaDetail,
    SchemaInfoResponse,
    SchemaVersion,
    StudentRequestV1,
    StudentRequestV2,
    StudentResponse,
    StudentTargetV2,
)
from app.registry import tool_registry
from app.recovery import RecoveryCoordinator, SelfHealingASGIMiddleware

# ==============================================================================
# In-Memory State Manager
# ==============================================================================

class APIStateManager:
    """
    Manages runtime schema state in-memory without requiring server restarts.
    """

    def __init__(self) -> None:
        self.active_version: SchemaVersion = SchemaVersion.V1

    def break_api(self) -> str:
        """Switch active schema to v2 (simulating schema drift)."""
        previous = self.active_version.value
        self.active_version = SchemaVersion.V2
        return previous

    def reset_api(self) -> str:
        """Reset active schema back to original v1 format."""
        previous = self.active_version.value
        self.active_version = SchemaVersion.V1
        return previous

    def get_active_model(self) -> Type[BaseModel]:
        """Return the Pydantic model corresponding to the active schema."""
        if self.active_version == SchemaVersion.V1:
            return StudentRequestV1
        return StudentRequestV2

    def get_version_definitions(self) -> Dict[str, SchemaDetail]:
        """Provide detailed metadata and JSON schemas for all versions."""
        return {
            SchemaVersion.V1.value: SchemaDetail(
                version=SchemaVersion.V1.value,
                model_name=StudentRequestV1.__name__,
                description="Original schema: expects top-level string field 'user_id'",
                sample_payload={"user_id": "123"},
                json_schema=StudentRequestV1.model_json_schema(),
            ),
            SchemaVersion.V2.value: SchemaDetail(
                version=SchemaVersion.V2.value,
                model_name=StudentRequestV2.__name__,
                description="Changed schema (drifted): expects nested 'target' object with integer 'id'",
                sample_payload={"target": {"id": 123}},
                json_schema=StudentRequestV2.model_json_schema(),
            ),
        }

    def get_schema_summary(self) -> SchemaInfoResponse:
        """Build the complete schema discovery response for GET /schema."""
        definitions = self.get_version_definitions()
        active_def = definitions[self.active_version.value]

        return SchemaInfoResponse(
            active_version=self.active_version.value,
            schema_name=active_def.model_name,
            description=active_def.description,
            expected_format=active_def.sample_payload,
            json_schema=active_def.json_schema,
            supported_versions=[SchemaVersion.V1.value, SchemaVersion.V2.value],
            version_definitions=definitions,
        )


# Instantiate single state manager in memory
state = APIStateManager()

# Instantiate recovery coordinator linked to authoritative state manager
coordinator = RecoveryCoordinator(state_manager=state)


# ==============================================================================
# FastAPI Application Initialization
# ==============================================================================

app = FastAPI(
    title="Self-Healing Tool Registry — Mock API & Recovery Engine",
    description=(
        "Simulates runtime API schema drift between v1 and v2, equipped with an in-memory "
        "self-healing middleware that intercepts schema mismatches, obtains trusted schemas, "
        "validates transformation patches, updates tool registry contracts, and executes bounded retries."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register pure ASGI Self-Healing Middleware
app.add_middleware(SelfHealingASGIMiddleware, coordinator=coordinator)


# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    tags=["System"],
)
async def get_health() -> HealthResponse:
    """
    Check if the API server is operational and view current active schema version.
    """
    return HealthResponse(
        status="ok",
        service="self-healing-mock-api",
        active_schema_version=state.active_version.value,
    )


@app.get(
    "/schema",
    response_model=SchemaInfoResponse,
    summary="Get Trusted API Schema Definition",
    tags=["Schema Registry"],
)
async def get_schema() -> SchemaInfoResponse:
    """
    Return the current trusted schema definition, active version, sample payload,
    and side-by-side comparison with other schema versions.

    This authoritative endpoint is queried by the recovery engine during drift events.
    """
    return state.get_schema_summary()


@app.get(
    "/registry",
    summary="Inspect In-Memory Tool Registry",
    tags=["Schema Registry"],
)
async def get_registry() -> Dict[str, Any]:
    """
    Inspect the caller's in-memory Tool Registry.
    Shows registered tools, currently known schema versions, and version update history.
    """
    return {
        "status": "success",
        "registry": tool_registry.get_all(),
    }


@app.get(
    "/audit",
    summary="Inspect Self-Healing Audit Trail",
    tags=["Self-Healing Audit"],
)
async def get_audit_events() -> Dict[str, Any]:
    """
    Retrieve structured audit events for all recovery attempts.
    Includes timestamps, tool names, patch decisions, retry counts, and outcomes.
    """
    return {
        "status": "success",
        "total_events": len(audit_logger.get_events()),
        "events": audit_logger.get_events(),
    }


@app.delete(
    "/audit",
    summary="Clear Audit Events",
    tags=["Self-Healing Audit"],
)
async def clear_audit_events() -> Dict[str, Any]:
    """Clear all recorded audit events."""
    audit_logger.clear()
    return {"status": "success", "message": "Audit trail cleared."}


@app.post(
    "/student",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Student record accepted and validated against active schema.",
            "model": StudentResponse,
        },
        422: {
            "description": (
                "Validation Error: Payload does not conform to active schema. "
                "(Self-healing middleware recovers compatible payloads unless bypassed)."
            ),
        },
    },
    summary="Create / Register Student",
    tags=["Student"],
)
async def create_student(
    payload: Any = Body(
        ...,
        description=(
            "Student registration payload.<br>"
            "<b>Schema v1 (Default):</b> <code>{\"user_id\": \"123\"}</code><br>"
            "<b>Schema v2 (After Break):</b> <code>{\"target\": {\"id\": 123}}</code>"
        ),
        openapi_examples={
            "v1_payload": {
                "summary": "Schema v1 Payload (Initial / Default)",
                "description": "Original contract: top-level user_id string.",
                "value": {"user_id": "123"},
            },
            "v2_payload": {
                "summary": "Schema v2 Payload (Drifted / After Break)",
                "description": "Updated contract: nested target object with integer id.",
                "value": {"target": {"id": 123}},
            },
        },
    ),
    bypass_recovery: bool = Query(
        default=False,
        description="Set to true to bypass self-healing recovery and receive raw validation failure (HTTP 422).",
    ),
) -> StudentResponse:
    """
    Accepts a student registration payload according to the currently active schema.

    - **When active schema is v1**: Expects `{"user_id": "123"}`.
    - **When active schema is v2**: Expects `{"target": {"id": 123}}`.

    Self-healing behavior:
    - If schema has drifted to v2 and an old v1 payload is sent, the self-healing middleware
      automatically detects the 422 mismatch, fetches the trusted schema, validates the patch,
      updates the Tool Registry, and retries the request transparently!
    - Pass `?bypass_recovery=true` or header `X-Bypass-Recovery: true` to bypass self-healing.
    """
    # Enforce dictionary payload
    if not isinstance(payload, dict):
        raise RequestValidationError([
            {
                "type": "model_type",
                "loc": ["body"],
                "msg": f"Input must be a JSON object, got {type(payload).__name__}",
                "input": payload,
            }
        ])

    # Validate against active model
    active_model = state.get_active_model()
    try:
        validated = active_model.model_validate(payload)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors())

    # Extract student identifier
    if isinstance(validated, StudentRequestV1):
        student_id = validated.user_id
    elif isinstance(validated, StudentRequestV2):
        student_id = validated.target.id
    else:
        student_id = "unknown"

    return StudentResponse(
        status="success",
        message=(
            f"Student record validated successfully against active schema "
            f"'{state.active_version.value}'."
        ),
        student_id=student_id,
        schema_version=state.active_version.value,
        data=validated.model_dump(),
    )


@app.post(
    "/admin/break-api",
    response_model=AdminActionResponse,
    summary="Simulate Schema Drift (Switch to v2)",
    tags=["Admin Controls"],
)
async def break_api() -> AdminActionResponse:
    """
    Switches active API schema from original v1 to drifted v2 in memory.
    No server restart required.

    After calling this endpoint:
    - The mock API now requires `{"target": {"id": 123}}`.
    - Unhealed or bypassed requests using `{"user_id": "123"}` will return HTTP 422.
    - Normal requests using `{"user_id": "123"}` will be self-healed automatically!
    """
    previous = state.break_api()
    return AdminActionResponse(
        status="success",
        message="Simulated API drift: Active schema switched from v1 to v2.",
        previous_schema_version=previous,
        active_schema_version=state.active_version.value,
        expected_format={"target": {"id": 123}},
    )


@app.post(
    "/admin/reset-api",
    response_model=AdminActionResponse,
    summary="Reset API Schema and Registry (Restore to v1)",
    tags=["Admin Controls"],
)
async def reset_api() -> AdminActionResponse:
    """
    Restores active API schema back to original v1 format and resets the Tool Registry.
    Allows testing and demo cycles to be repeated cleanly.
    """
    previous = state.reset_api()
    tool_registry.reset()
    audit_logger.clear()
    return AdminActionResponse(
        status="success",
        message="API reset: Active schema and tool registry restored to original v1 format.",
        previous_schema_version=previous,
        active_schema_version=state.active_version.value,
        expected_format={"user_id": "123"},
    )
