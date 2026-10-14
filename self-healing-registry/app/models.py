"""
models.py - Pydantic models for the Self-Healing Tool Registry Mock API.

Defines the request and response schemas for:
- Version 1 (Original): Expects a flat JSON with 'user_id' as a string.
- Version 2 (Drifted):  Expects a nested JSON with 'target.id' as an integer.
Along with system responses for health, schema discovery, and admin actions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class SchemaVersion(str, Enum):
    """Enumeration of supported API schema versions."""
    V1 = "v1"
    V2 = "v2"


# ==============================================================================
# Request Models
# ==============================================================================

class StudentRequestV1(BaseModel):
    """
    Original API Request Schema (v1).
    Expects a top-level string field `user_id`.
    Example: {"user_id": "123"}
    """
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        json_schema_extra={
            "example": {
                "user_id": "123"
            }
        }
    )

    user_id: str = Field(
        ...,
        description="Unique student identifier (string format)",
        examples=["123"],
    )


class StudentTargetV2(BaseModel):
    """Target object container for v2 schema."""
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        json_schema_extra={
            "example": {
                "id": 123
            }
        }
    )

    id: int = Field(
        ...,
        description="Unique student identifier (integer format)",
        examples=[123],
    )


class StudentRequestV2(BaseModel):
    """
    Drifted / Broken API Request Schema (v2).
    Expects a nested object `target` containing an integer `id`.
    Example: {"target": {"id": 123}}
    """
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        json_schema_extra={
            "example": {
                "target": {
                    "id": 123
                }
            }
        }
    )

    target: StudentTargetV2 = Field(
        ...,
        description="Target student object wrapping student credentials",
    )


# ==============================================================================
# Response Models
# ==============================================================================

class StudentResponse(BaseModel):
    """Standard success response returned by POST /student."""
    status: str = Field(default="success", description="Status of the operation")
    message: str = Field(..., description="Human-readable result summary")
    student_id: Union[str, int] = Field(..., description="Processed student identifier")
    schema_version: str = Field(..., description="Schema version used during processing")
    data: Dict[str, Any] = Field(..., description="The validated payload as accepted by the server")


class HealthResponse(BaseModel):
    """Health check response format."""
    status: str = Field(default="ok", description="Service health state")
    service: str = Field(default="self-healing-mock-api", description="Service identifier")
    active_schema_version: str = Field(..., description="Currently active schema version")


class AdminActionResponse(BaseModel):
    """Response returned by admin actions (break-api / reset-api)."""
    status: str = Field(default="success", description="Outcome of the admin command")
    message: str = Field(..., description="Confirmation details")
    previous_schema_version: str = Field(..., description="Schema version before switch")
    active_schema_version: str = Field(..., description="Active schema version after switch")
    expected_format: Dict[str, Any] = Field(..., description="Sample payload accepted by the active schema")


class SchemaDetail(BaseModel):
    """Schema descriptor containing metadata and JSON schema."""
    version: str = Field(..., description="Version label")
    model_name: str = Field(..., description="Pydantic model class name")
    description: str = Field(..., description="Description of the schema")
    sample_payload: Dict[str, Any] = Field(..., description="Canonical valid payload")
    json_schema: Dict[str, Any] = Field(..., description="Full OpenAPI-compliant JSON schema")


class SchemaInfoResponse(BaseModel):
    """Response returned by GET /schema describing the active trusted schema."""
    active_version: str = Field(..., description="Active schema version: 'v1' or 'v2'")
    schema_name: str = Field(..., description="Model name of the currently active schema")
    description: str = Field(..., description="Summary of current schema expectations")
    expected_format: Dict[str, Any] = Field(..., description="Sample payload matching current expectations")
    json_schema: Dict[str, Any] = Field(..., description="JSON Schema definition for active model")
    supported_versions: List[str] = Field(..., description="All supported schema versions")
    version_definitions: Dict[str, SchemaDetail] = Field(
        ...,
        description="Definitions of both original (v1) and changed (v2) schemas for comparison"
    )
