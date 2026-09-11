from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

STATE_OWNER = os.getenv("JARVIS_STATE_OWNER", "theboydsbusinessgroup-ctrl")
STATE_REPO = os.getenv("JARVIS_STATE_REPO", "Jarvis-State")
STATE_REF = os.getenv("JARVIS_STATE_REF", "main")
CLAUDE_MODEL = os.getenv("JARVIS_SECOND_BRAIN_MODEL", "anthropic/claude-sonnet-5")

DEFAULT_STATE_FILES = (
    "OPERATING_PROTOCOLS.md",
    "AGENT_ROLES.md",
    "CURRENT_STATUS.md",
    "REVENUE_PRIORITY.md",
    "DECISIONS.md",
    "CONTEXT_PACKET_SPEC.md",
)


@dataclass(frozen=True)
class SecondBrainResult:
    status: str
    model: str
    review_mode: str
    response: str | None = None
    error: str | None = None
    usage: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "model": self.model,
            "review_mode": self.review_mode,
            "response": self.response,
            "error": self.error,
            "usage": self.usage,
        }


def _request_json(url: str, *, headers: dict[str, str], method: str = "GET", body: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(url, data=payload, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc


def load_private_state(paths: tuple[str, ...] = DEFAULT_STATE_FILES) -> dict[str, str]:
    token = os.getenv("GITHUB_STATE_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_STATE_TOKEN is not configured")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "jarvis-control-plane",
    }
    state: dict[str, str] = {}
    for path in paths:
        encoded_path = quote(path, safe="/")
        url = f"https://api.github.com/repos/{STATE_OWNER}/{STATE_REPO}/contents/{encoded_path}?ref={quote(STATE_REF)}"
        data = _request_json(url, headers=headers)
        if data.get("encoding") != "base64" or not data.get("content"):
            raise RuntimeError(f"Unexpected GitHub content format for {path}")
        raw = base64.b64decode(data["content"])
        state[path] = raw.decode("utf-8", errors="replace")
    return state


def build_context_packet(*, task: str, decision_criteria: str = "", review_mode: str = "parallel", evidence: str = "") -> str:
    state = load_private_state()
    sections = [
        "# JARVIS SECOND-BRAIN CONTEXT PACKET",
        f"REVIEW_MODE: {review_mode.upper()}",
        "",
        "## TASK",
        task.strip(),
        "",
        "## DECISION CRITERIA",
        decision_criteria.strip() or "Revenue impact, risk, cost, speed, reversibility, compliance, and operational burden.",
        "",
        "## EVIDENCE",
        evidence.strip() or "No additional evidence supplied.",
    ]
    for path in DEFAULT_STATE_FILES:
        sections.extend(["", f"## STATE: {path}", state[path].strip()])
    sections.extend([
        "",
        "## OUTPUT CONTRACT",
        "Return: Decision (APPROVE/MODIFY/REJECT), Top reason, Required material changes, Risk if ignored, Eric required (YES/NO), Confidence (LOW/MEDIUM/HIGH). Do not reveal private chain-of-thought.",
    ])
    return "\n".join(sections)


def call_second_brain(*, task: str, decision_criteria: str = "", review_mode: str = "parallel", evidence: str = "") -> SecondBrainResult:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return SecondBrainResult(
            status="not_configured",
            model=CLAUDE_MODEL,
            review_mode=review_mode,
            error="OPENROUTER_API_KEY is not configured",
        )

    try:
        packet = build_context_packet(
            task=task,
            decision_criteria=decision_criteria,
            review_mode=review_mode,
            evidence=evidence,
        )
        body = {
            "model": CLAUDE_MODEL,
            "temperature": 0.2,
            "max_tokens": 1200,
            "messages": [
                {
                    "role": "system",
                    "content": "You are Jarvis's independent second-brain CTO/red-team reviewer. Follow the supplied output contract. Be concise, challenge assumptions, and do not reveal chain-of-thought.",
                },
                {"role": "user", "content": packet},
            ],
        }
        data = _request_json(
            "https://openrouter.ai/api/v1/chat/completions",
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-Title": "Jarvis Second Brain",
            },
            body=body,
            timeout=45,
        )
        choices = data.get("choices") or []
        message = (choices[0].get("message") or {}) if choices else {}
        text = (message.get("content") or message.get("reasoning") or "").strip()
        if not text:
            raise RuntimeError("Claude returned no usable text")
        return SecondBrainResult(
            status="ok",
            model=data.get("model") or CLAUDE_MODEL,
            review_mode=review_mode,
            response=text,
            usage=data.get("usage"),
        )
    except Exception as exc:
        return SecondBrainResult(
            status="error",
            model=CLAUDE_MODEL,
            review_mode=review_mode,
            error=str(exc),
        )
