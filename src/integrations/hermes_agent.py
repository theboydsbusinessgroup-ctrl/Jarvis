from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.core.orchestration_gate import OrchestrationGate

HERMES_URL = os.getenv("HERMES_API_URL", "http://127.0.0.1:8642").rstrip("/")
HERMES_MODEL = os.getenv("HERMES_MODEL", "hermes-agent")
HERMES_TIMEOUT = int(os.getenv("HERMES_TIMEOUT_SECONDS", "120"))


@dataclass(frozen=True)
class HermesResult:
    status: str
    response: str | None = None
    error: str | None = None
    model: str = HERMES_MODEL
    usage: dict[str, Any] | None = None
    context_fingerprint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "response": self.response,
            "error": self.error,
            "model": self.model,
            "usage": self.usage,
            "context_fingerprint": self.context_fingerprint,
        }


def _request_json(url: str, *, headers: Mapping[str, str], body: Mapping[str, Any]) -> dict[str, Any]:
    req = Request(
        url,
        data=json.dumps(dict(body)).encode("utf-8"),
        headers=dict(headers),
        method="POST",
    )
    try:
        with urlopen(req, timeout=HERMES_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Hermes HTTP {exc.code}: {detail[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Hermes network error: {exc.reason}") from exc


def build_worker_prompt(*, task: str, context: Mapping[str, Any], role: str) -> str:
    authority = context.get("authority_context") or {}
    constraints = list(context.get("constraints") or [])
    constraints.extend([
        "Do not move money, place trades, modify credentials, delete data, publish externally, or perform irreversible actions.",
        "Do not bypass JARVIS policy, approval, idempotency, or source-of-truth boundaries.",
        "When an external write would be needed, stop and return the exact proposed action instead.",
    ])
    packet = {
        "role": role,
        "task_id": context.get("task_id"),
        "trace_id": context.get("trace_id"),
        "project_id": context.get("project_id"),
        "objective": task.strip(),
        "constraints": constraints,
        "authority_context": authority,
        "evidence_refs": context.get("evidence_refs") or [],
        "jarvis_context_fingerprint": context.get("jarvis_context_fingerprint"),
    }
    return (
        "You are a bounded Hermes worker operating under the JARVIS control plane. "
        "Treat the JSON packet below as authoritative. Return a concise result, evidence, "
        "open risks, and any proposed external action.\n\n"
        + json.dumps(packet, indent=2, sort_keys=True, default=str)
    )


def _call_hermes(*, task: str, context: Mapping[str, Any], role: str) -> HermesResult:
    """Low-level network call. Callers should use delegate_to_hermes()."""
    key = os.getenv("HERMES_API_KEY")
    if not key:
        return HermesResult(
            status="not_configured",
            error="HERMES_API_KEY is not configured",
            context_fingerprint=context.get("jarvis_context_fingerprint"),
        )

    prompt = build_worker_prompt(task=task, context=context, role=role)
    body = {
        "model": HERMES_MODEL,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": "You are an execution worker subordinate to JARVIS authority and approval controls.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    try:
        data = _request_json(
            f"{HERMES_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "jarvis-hermes-bridge",
            },
            body=body,
        )
        choices = data.get("choices") or []
        message = (choices[0].get("message") or {}) if choices else {}
        response = str(message.get("content") or "").strip()
        if not response:
            raise RuntimeError("Hermes returned no usable response")
        return HermesResult(
            status="ok",
            response=response,
            model=str(data.get("model") or HERMES_MODEL),
            usage=data.get("usage"),
            context_fingerprint=context.get("jarvis_context_fingerprint"),
        )
    except Exception as exc:
        return HermesResult(
            status="error",
            error=str(exc),
            context_fingerprint=context.get("jarvis_context_fingerprint"),
        )


def delegate_to_hermes(
    *,
    gate: OrchestrationGate,
    task: str,
    context: Mapping[str, Any],
    role: str = "specialist",
    current_depth: int = 0,
    active_workers: int = 0,
) -> HermesResult:
    """Authorize a Hermes delegation through JARVIS before any network call."""
    decision = gate.evaluate(
        current_depth=current_depth,
        active_workers=active_workers,
        target_role=role,
        context=context,
    )
    if not decision.allowed:
        detail = decision.reason
        if decision.missing_context:
            detail += ": " + ", ".join(decision.missing_context)
        return HermesResult(status="blocked", error=detail)

    worker_context = dict(context)
    worker_context["jarvis_context_fingerprint"] = decision.context_fingerprint
    if not gate.verify_preserved_context(worker_context, decision.context_fingerprint or ""):
        return HermesResult(status="blocked", error="context_fingerprint_verification_failed")

    return _call_hermes(task=task, context=worker_context, role=role)
