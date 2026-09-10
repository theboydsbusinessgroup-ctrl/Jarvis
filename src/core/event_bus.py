"""In-process portfolio event bus with idempotent dispatch.

This is transport-agnostic infrastructure. Persistence/message-queue transport can be
added later without changing handler contracts.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Mapping

from .telemetry_ingest import normalize_envelope

Handler = Callable[[dict[str, Any]], Any]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._processed: set[str] = set()

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: Mapping[str, Any]) -> dict[str, Any]:
        normalized = normalize_envelope(event)
        key = normalized["idempotency_key"]
        if key in self._processed:
            return {"accepted": False, "duplicate": True, "event": normalized, "results": []}

        results = []
        handlers = self._handlers.get(normalized["event_type"], []) + self._handlers.get("*", [])
        for handler in handlers:
            results.append(handler(normalized))
        self._processed.add(key)
        return {"accepted": True, "duplicate": False, "event": normalized, "results": results}

    def has_processed(self, idempotency_key: str) -> bool:
        return idempotency_key in self._processed
