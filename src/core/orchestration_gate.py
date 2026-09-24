"""Deterministic limits for multi-agent delegation and context preservation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


def context_fingerprint(context: Mapping[str, Any]) -> str:
    canonical = json.dumps(context, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class DelegationDecision:
    allowed: bool
    reason: str
    next_depth: int
    context_fingerprint: str | None = None
    missing_context: tuple[str, ...] = ()


class OrchestrationGate:
    def __init__(self, config: Mapping[str, Any]):
        if config.get("schema_version") != "1.0":
            raise ValueError("Unsupported orchestration policy schema")
        self.config = dict(config)

    @classmethod
    def from_file(cls, path: str | Path) -> "OrchestrationGate":
        with Path(path).open(encoding="utf-8") as fh:
            return cls(json.load(fh))

    def evaluate(
        self,
        *,
        current_depth: int,
        active_workers: int,
        target_role: str,
        context: Mapping[str, Any],
    ) -> DelegationDecision:
        next_depth = current_depth + 1
        if next_depth > int(self.config["max_delegation_depth"]):
            return DelegationDecision(False, "max_delegation_depth_exceeded", next_depth)
        if active_workers >= int(self.config["max_parallel_workers"]):
            return DelegationDecision(False, "max_parallel_workers_reached", next_depth)
        if target_role not in set(self.config.get("allowed_target_roles") or []):
            return DelegationDecision(False, "target_role_not_allowed", next_depth)

        required = tuple(self.config.get("required_context_fields") or ())
        missing = tuple(field for field in required if field not in context or context[field] in (None, "", []))
        if missing:
            return DelegationDecision(False, "required_context_missing", next_depth, missing_context=missing)

        preserved = self.preserve_context(context)
        return DelegationDecision(
            True,
            "allowed",
            next_depth,
            context_fingerprint=context_fingerprint(preserved),
        )

    def preserve_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        fields = tuple(self.config.get("preserve_context_fields") or ())
        return {field: context[field] for field in fields if field in context}

    def verify_preserved_context(self, context: Mapping[str, Any], expected_fingerprint: str) -> bool:
        return context_fingerprint(self.preserve_context(context)) == expected_fingerprint
