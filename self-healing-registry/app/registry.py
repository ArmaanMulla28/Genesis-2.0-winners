"""
registry.py - In-Memory Tool Registry for Self-Healing API Architecture.

Stores and manages tool contracts, active schema versions, and schema change history.
The registry maintains the caller's trusted contract and is updated only after
successful patch validation during recovery.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models import SchemaVersion, StudentRequestV1, StudentRequestV2


@dataclass
class ToolRegistryEntry:
    """Represents a registered tool/service contract in memory."""
    tool_name: str
    endpoint: str
    method: str
    active_version: str
    schema_definition: Dict[str, Any]
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version_history: List[Dict[str, Any]] = field(default_factory=list)


class ToolRegistry:
    """
    In-memory registry holding active tool schemas and version tracking.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolRegistryEntry] = {}
        self.reset()

    def reset(self) -> None:
        """
        Reset the registry to initial baseline (v1 schema for student service).
        """
        self._tools.clear()
        now = datetime.now(timezone.utc).isoformat()
        self._tools["student_service"] = ToolRegistryEntry(
            tool_name="student_service",
            endpoint="/student",
            method="POST",
            active_version=SchemaVersion.V1.value,
            schema_definition=StudentRequestV1.model_json_schema(),
            last_updated=now,
            version_history=[
                {
                    "version": SchemaVersion.V1.value,
                    "timestamp": now,
                    "action": "initial_registration",
                }
            ],
        )

    def register_tool(
        self,
        tool_name: str,
        endpoint: str,
        method: str,
        version: str,
        schema_definition: Dict[str, Any],
    ) -> ToolRegistryEntry:
        """Register a new tool contract."""
        now = datetime.now(timezone.utc).isoformat()
        entry = ToolRegistryEntry(
            tool_name=tool_name,
            endpoint=endpoint,
            method=method.upper(),
            active_version=version,
            schema_definition=schema_definition,
            last_updated=now,
            version_history=[
                {
                    "version": version,
                    "timestamp": now,
                    "action": "initial_registration",
                }
            ],
        )
        self._tools[tool_name] = entry
        return entry

    def get_tool(self, tool_name: str) -> Optional[ToolRegistryEntry]:
        """Fetch a tool entry by name."""
        return self._tools.get(tool_name)

    def get_tool_by_endpoint(self, endpoint: str, method: str) -> Optional[ToolRegistryEntry]:
        """Lookup tool by HTTP method and endpoint path."""
        method_upper = method.upper()
        for entry in self._tools.values():
            if entry.endpoint == endpoint and entry.method == method_upper:
                return entry
        return None

    def update_tool_version(
        self,
        tool_name: str,
        new_version: str,
        new_schema: Dict[str, Any],
        reason: str = "self_healed_schema_update",
    ) -> bool:
        """
        Update the registered tool's schema version.
        MUST only be called after patch validation has succeeded.
        """
        entry = self._tools.get(tool_name)
        if not entry:
            return False

        previous_version = entry.active_version
        now = datetime.now(timezone.utc).isoformat()
        entry.active_version = new_version
        entry.schema_definition = new_schema
        entry.last_updated = now
        entry.version_history.append(
            {
                "previous_version": previous_version,
                "version": new_version,
                "timestamp": now,
                "action": reason,
            }
        )
        return True

    def get_all(self) -> Dict[str, Any]:
        """Export registry state for API inspection."""
        return {
            name: {
                "tool_name": entry.tool_name,
                "endpoint": entry.endpoint,
                "method": entry.method,
                "active_version": entry.active_version,
                "last_updated": entry.last_updated,
                "version_history": entry.version_history,
                "schema_definition": entry.schema_definition,
            }
            for name, entry in self._tools.items()
        }


# Global in-memory singleton
tool_registry = ToolRegistry()
