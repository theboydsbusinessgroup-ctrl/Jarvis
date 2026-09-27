from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from src.core.orchestration_gate import OrchestrationGate

DEFAULT_HERMES_MODEL = "hermes-agent"
DEFAULT_HERMES_TIMEOUT = 120
MAX_HERMES_TIMEOUT = 300


@dataclass(frozen=True)
class HermesResult:
    status: str
    response: str | None = None
    error: str | None = None
    model: str = DEFAULT_HERMES_MODEL
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


def _is_enabled() -> bool:
    return os.getenv("HERMES_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}


def _runtime_settings() -> tuple[str, str, int]:
    raw_url = os.getenv("HERMES_API_URL", "http://127.0.0.1:8642").strip().rstrip("/")
    parts = urlsplit(raw_url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("HERMES_API_URL must be an absolute HTTP(S) URL")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("HERMES_API_URL must not include credentials, a query, or a fragment")
    if parts.scheme != "https" and parts.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("HERMES_API_URL must use HTTPS unless it targets loopback")

    model = os.getenv("HERMES_MODEL", DEFAULT_HERMES_MODEL).strip()
    if not model:
        raise ValueError("HERMES_MODEL must not be empty")

    try:
        timeout = int(os.getenv("HERMES_TIMEOUT_SECONDS", str(DEFAULT_HERMES_TIMEOUT)))
    except ValueError as exc:
        raise ValueError("HERMES_TIMEOUT_SECONDS must be an integer") from exc
    if timeout < 1 or timeout > MAX_HERMES_TIMEOUT:
        raise ValueError(f"HERMES_TIMEOUT_SECONDS must be between 1 and {MAX_HERMES_TIMEOUT}")

    return raw_url, model, timeout


def _request_json(
    url: str,
    *,
    headers: Mapping[str, str],
    body: Mapping[str, Any],
    timeout: int,
) -> dict[str, Any]:
    req = Request(
        url,
        data=json.dumps(dict(body)).encode("utf-8"),
        headers=dict(headers),
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as response:
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
    if not _is_enabled():
        return HermesResult(
            status="disabled",
            error="Hermes is disabled; set HERMES_ENABLED=true only after the activation checklist passes",
            context_fingerprint=context.get("jarvis_context_fingerprint"),
        )

    key = os.getenv("HERMES_API_KEY")
    if not key:
        return HermesResult(
            status="not_configured",
            error="HERMES_API_KEY is not configured",
            context_fingerprint=context.get("jarvis_context_fingerprint"),
        )

    try:
        base_url, model, timeout = _runtime_settings()
        prompt = build_worker_prompt(task=task, context=context, role=role)
        body = {
            "model": model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an execution worker subordinate to JARVIS authority and approval controls.",
                },
                {"role": "user", "content": prompt},
            ],
        }
        data = _request_json(
            f"{base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "jarvis-hermes-bridge",
            },
            body=body,
            timeout=timeout,
        )
        choices = data.get("choices") or []
        message = (choices[0].get("message") or {}) if choices else {}
        response = str(message.get("content") or "").strip()
        if not response:
            raise RuntimeError("Hermes returned no usable response")
        return HermesResult(
            status="ok",
            response=response,
            model=str(data.get("model") or model),
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
    if not _is_enabled():
        return HermesResult(
            status="disabled",
            error="Hermes is disabled; set HERMES_ENABLED=true only after the activation checklist passes",
        )

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
