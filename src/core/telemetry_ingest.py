"""JARVIS portfolio telemetry normalization boundary.

Domain repositories remain sources of truth. JARVIS accepts the deployed v1.0
adapter envelope and normalizes it into the richer v1.1 portfolio envelope.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

REQUIRED = {"schema_version", "event_id", "project_id", "event_type", "occurred_at", "payload"}
SUPPORTED = {"1.0", "1.1"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_envelope(event: Mapping[str, Any]) -> dict[str, Any]:
    missing = REQUIRED - set(event)
    if missing:
        raise ValueError(f"Missing required JARVIS envelope fields: {sorted(missing)}")
    if event["schema_version"] not in SUPPORTED:
        raise ValueError("Unsupported JARVIS envelope schema_version")

    normalized = dict(event)
    normalized["schema_version"] = "1.1"
    normalized.setdefault("source_system", normalized["project_id"])
    normalized.setdefault("source_event_id", None)
    normalized.setdefault("received_at", _utc_now())
    normalized.setdefault("idempotency_key", normalized["event_id"])
    normalized.setdefault("entity_type", None)
    normalized.setdefault("entity_id", None)
    normalized.setdefault("amount", None)
    normalized.setdefault("currency", None)
    normalized.setdefault("confidence", None)
    normalized.setdefault("evidence", [])
    return normalized


def validate_envelope(event: Mapping[str, Any]) -> dict[str, Any]:
    return normalize_envelope(event)


def make_health_event(project_id: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    return normalize_envelope({
        "schema_version": "1.1",
        "event_id": f"health:{project_id}:{now}",
        "project_id": project_id,
        "event_type": "project.health.snapshot",
        "occurred_at": now,
        "payload": {"metrics": dict(metrics)},
    })
