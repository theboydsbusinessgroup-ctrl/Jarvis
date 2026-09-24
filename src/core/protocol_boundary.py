"""Protocol boundary: MCP for tools/data and A2A for agent delegation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol

from src.core.orchestration_gate import context_fingerprint


def route_protocol(target_kind: str) -> str:
    normalized = target_kind.strip().lower()
    if normalized in {"tool", "data"}:
        return "mcp"
    if normalized == "agent":
        return "a2a"
    raise ValueError(f"Unsupported target kind: {target_kind}")


@dataclass(frozen=True)
class ProtocolEnvelope:
    schema_version: str
    protocol: str
    target_kind: str
    target_id: str
    task_id: str
    trace_id: str
    context_fingerprint: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_protocol_envelope(
    *,
    target_kind: str,
    target_id: str,
    task_id: str,
    trace_id: str,
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> ProtocolEnvelope:
    if not all((target_id, task_id, trace_id)):
        raise ValueError("target_id, task_id, and trace_id are required")
    normalized = target_kind.strip().lower()
    return ProtocolEnvelope(
        schema_version="1.0",
        protocol=route_protocol(normalized),
        target_kind=normalized,
        target_id=target_id,
        task_id=task_id,
        trace_id=trace_id,
        context_fingerprint=context_fingerprint(context),
        payload=dict(payload),
    )


class MCPToolAdapter(Protocol):
    def discover_tools(self) -> list[dict[str, Any]]: ...
    def call_tool(
        self,
        name: str,
        arguments: Mapping[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]: ...


class A2AAgentAdapter(Protocol):
    def agent_card(self) -> dict[str, Any]: ...
    def send_task(self, envelope: ProtocolEnvelope) -> dict[str, Any]: ...
