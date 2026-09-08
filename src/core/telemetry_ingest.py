"""JARVIS portfolio telemetry ingestion boundary.

The module validates the common envelope without taking ownership of domain data.
Production transport remains opt-in and must be supplied by deployment configuration.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

REQUIRED = {"schema_version", "event_id", "project_id", "event_type", "occurred_at", "payload"}


def validate_envelope(event: Mapping[str, Any]) -> dict[str, Any]:
    missing = REQUIRED - set(event)
    if missing:
        raise ValueError(f"Missing required JARVIS envelope fields: {sorted(missing)}")
    if event["schema_version"] != "1.0":
        raise ValueError("Unsupported JARVIS envelope schema_version")
    return dict(event)


def make_health_event(project_id: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "event_id": f"health:{project_id}:{datetime.now(timezone.utc).isoformat()}",
        "project_id": project_id,
        "event_type": "project.health.snapshot",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"metrics": dict(metrics)},
    }
