"""Fail-closed action control plane for tool and connector execution."""
from __future__ import annotations

import json
import os
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from src.core.policy_engine import PolicyEngine


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_clone(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str))


@dataclass(frozen=True)
class ToolRule:
    key: str
    risk: str
    policy_action: str
    authority_tier: str
    description: str = ""


class ToolPolicyRegistry:
    """Resolve connector operations to deterministic policy actions."""

    def __init__(self, config: Mapping[str, Any]):
        if config.get("schema_version") != "1.0":
            raise ValueError("Unsupported tool policy schema")
        self.config = dict(config)

    @classmethod
    def from_file(cls, path: str | Path) -> "ToolPolicyRegistry":
        with Path(path).open(encoding="utf-8") as fh:
            return cls(json.load(fh))

    def resolve(self, connector: str, operation: str) -> ToolRule:
        key = f"{connector}.{operation}"
        tools = self.config.get("tools") or {}
        raw = tools.get(key) or tools.get(f"{connector}.*") or self.config["default"]
        return ToolRule(
            key=key,
            risk=str(raw.get("risk", "RED")).upper(),
            policy_action=str(raw.get("policy_action", "high_impact_external_action")),
            authority_tier=str(raw.get("authority_tier", raw.get("risk", "RED"))).upper(),
            description=str(raw.get("description", "")),
        )


class JsonCheckpointStore:
    """Durable JSON checkpoints for approval/resume state.

    Use a persistent volume or replace this adapter with a database-backed
    implementation before enabling live connector writes in serverless production.
    """

    def __init__(self, path: str | Path | None = None):
        configured = path or os.getenv("JARVIS_APPROVAL_STORE")
        self.path = Path(configured or "/tmp/jarvis-runtime/approval-checkpoints.json")

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": "1.0", "operations": {}}
        with self.path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("schema_version") != "1.0":
            raise ValueError("Unsupported approval checkpoint schema")
        data.setdefault("operations", {})
        return data

    def _write(self, data: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8")
        tmp.replace(self.path)

    def get(self, operation_id: str) -> dict[str, Any] | None:
        record = self._read()["operations"].get(operation_id)
        return deepcopy(record) if record else None

    def put(self, record: Mapping[str, Any]) -> dict[str, Any]:
        data = self._read()
        stored = _json_clone(record)
        data["operations"][stored["operation_id"]] = stored
        self._write(data)
        return deepcopy(stored)


class AutonomyControlPlane:
    """Policy + approval + checkpoint + idempotency gate for connector actions."""

    def __init__(self, policy_engine: PolicyEngine, tool_registry: ToolPolicyRegistry, store: JsonCheckpointStore):
        self.policy_engine = policy_engine
        self.tool_registry = tool_registry
        self.store = store

    def propose(
        self,
        connector: str,
        operation: str,
        payload: Mapping[str, Any] | None = None,
        *,
        project_id: str | None = None,
        context: Mapping[str, Any] | None = None,
        workflow_state: Mapping[str, Any] | None = None,
        operation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        operation_id = operation_id or uuid.uuid4().hex
        existing = self.store.get(operation_id)
        if existing:
            return existing

        rule = self.tool_registry.resolve(connector, operation)
        ctx = dict(context or {})
        ctx.setdefault("authority_tier", rule.authority_tier)
        policy = self.policy_engine.decide(rule.policy_action, project_id=project_id, context=ctx)

        status = {
            "execute": "approved",
            "require_approval": "pending_approval",
            "prohibited": "prohibited",
        }.get(policy["decision"], "pending_approval")

        record = {
            "schema_version": "1.0",
            "operation_id": operation_id,
            "idempotency_key": idempotency_key or operation_id,
            "connector": connector,
            "operation": operation,
            "tool_key": rule.key,
            "risk": rule.risk,
            "policy_action": rule.policy_action,
            "project_id": project_id,
            "payload": _json_clone(payload or {}),
            "workflow_state": _json_clone(workflow_state or {}),
            "context": _json_clone(ctx),
            "policy": _json_clone(policy),
            "status": status,
            "approval": None,
            "attempt_count": 0,
            "result": None,
            "error": None,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        return self.store.put(record)

    def approve(self, operation_id: str, *, approved: bool, actor: str = "human") -> dict[str, Any]:
        record = self._require(operation_id)
        if record["status"] == "prohibited":
            raise PermissionError("Prohibited actions cannot be approved")
        if record["status"] not in {"pending_approval", "approved", "rejected"}:
            raise ValueError(f"Operation in {record['status']} state cannot be reviewed")

        record["approval"] = {
            "approved": bool(approved),
            "actor": actor,
            "decided_at": _utcnow(),
        }
        record["status"] = "approved" if approved else "rejected"
        record["updated_at"] = _utcnow()
        return self.store.put(record)

    def execute(self, operation_id: str, executor: Callable[..., Any]) -> dict[str, Any]:
        record = self._require(operation_id)
        if record["status"] == "executed":
            return {"record": record, "replayed": True}
        if record["status"] in {"pending_approval", "rejected", "prohibited"}:
            raise PermissionError(f"Operation is not executable: {record['status']}")
        if record["status"] not in {"approved", "failed"}:
            raise ValueError(f"Operation in {record['status']} state cannot execute")

        record["attempt_count"] = int(record.get("attempt_count", 0)) + 1
        record["updated_at"] = _utcnow()
        self.store.put(record)

        try:
            result = executor(
                connector=record["connector"],
                operation=record["operation"],
                payload=deepcopy(record["payload"]),
                idempotency_key=record["idempotency_key"],
            )
        except Exception as exc:
            record["status"] = "failed"
            record["error"] = {"type": type(exc).__name__, "message": str(exc)}
            record["updated_at"] = _utcnow()
            self.store.put(record)
            raise

        record["status"] = "executed"
        record["result"] = _json_clone(result)
        record["error"] = None
        record["executed_at"] = _utcnow()
        record["updated_at"] = _utcnow()
        stored = self.store.put(record)
        return {"record": stored, "replayed": False}

    def resume(self, operation_id: str) -> dict[str, Any]:
        """Return the exact persisted action and workflow checkpoint for resumption."""
        return self._require(operation_id)

    def _require(self, operation_id: str) -> dict[str, Any]:
        record = self.store.get(operation_id)
        if not record:
            raise KeyError(f"Unknown operation_id: {operation_id}")
        return record
