"""Verified-only portfolio revenue ledger.

The ledger records money only from authoritative, evidence-bearing events. Forecasts,
checkout starts, invoices, and unverified claims are intentionally excluded.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal
from typing import Any, Mapping

VERIFIED_REVENUE_EVENTS = {"payment.completed", "sale.completed", "revenue.recorded"}
REVERSAL_EVENTS = {"payment.refunded", "sale.refunded", "revenue.reversed"}


@dataclass(frozen=True)
class LedgerEntry:
    event_id: str
    project_id: str
    occurred_at: str
    gross: Decimal
    fees: Decimal
    fulfillment_cost: Decimal
    advertising_cost: Decimal
    refunds: Decimal
    currency: str
    evidence: tuple[str, ...]

    @property
    def contribution(self) -> Decimal:
        return self.gross - self.fees - self.fulfillment_cost - self.advertising_cost - self.refunds

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("gross", "fees", "fulfillment_cost", "advertising_cost", "refunds"):
            data[key] = float(data[key])
        data["contribution"] = float(self.contribution)
        data["evidence"] = list(self.evidence)
        return data


class RevenueLedger:
    def __init__(self) -> None:
        self._entries: dict[str, LedgerEntry] = {}

    @staticmethod
    def _money(value: Any) -> Decimal:
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))

    def record_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        event_type = str(event.get("event_type") or "")
        if event_type not in VERIFIED_REVENUE_EVENTS | REVERSAL_EVENTS:
            return {"recorded": False, "reason": "not_a_verified_revenue_event"}
        event_id = str(event.get("event_id") or "")
        if not event_id:
            raise ValueError("Revenue event requires event_id")
        if event_id in self._entries:
            return {"recorded": False, "reason": "duplicate", "entry": self._entries[event_id].to_dict()}

        evidence = tuple(str(x) for x in (event.get("evidence") or []) if x)
        confidence = event.get("confidence")
        source_event_id = event.get("source_event_id")
        if not evidence or not source_event_id or confidence != 1:
            raise ValueError("Revenue requires authoritative source_event_id, confidence=1, and evidence")

        currency = str(event.get("currency") or "").upper()
        if len(currency) != 3:
            raise ValueError("Revenue event requires 3-letter currency")

        payload = dict(event.get("payload") or {})
        amount = self._money(event.get("amount"))
        if amount < 0:
            raise ValueError("Revenue amount cannot be negative")

        if event_type in REVERSAL_EVENTS:
            gross = Decimal("0.00")
            refunds = amount
        else:
            gross = amount
            refunds = self._money(payload.get("refunds"))

        entry = LedgerEntry(
            event_id=event_id,
            project_id=str(event.get("project_id") or ""),
            occurred_at=str(event.get("occurred_at") or ""),
            gross=gross,
            fees=self._money(payload.get("fees")),
            fulfillment_cost=self._money(payload.get("fulfillment_cost")),
            advertising_cost=self._money(payload.get("advertising_cost")),
            refunds=refunds,
            currency=currency,
            evidence=evidence,
        )
        self._entries[event_id] = entry
        return {"recorded": True, "entry": entry.to_dict()}

    def summary(self, currency: str = "USD") -> dict[str, Any]:
        entries = [e for e in self._entries.values() if e.currency == currency.upper()]
        return {
            "currency": currency.upper(),
            "verified_entries": len(entries),
            "gross_revenue": float(sum((e.gross for e in entries), Decimal("0.00"))),
            "fees": float(sum((e.fees for e in entries), Decimal("0.00"))),
            "fulfillment_cost": float(sum((e.fulfillment_cost for e in entries), Decimal("0.00"))),
            "advertising_cost": float(sum((e.advertising_cost for e in entries), Decimal("0.00"))),
            "refunds": float(sum((e.refunds for e in entries), Decimal("0.00"))),
            "contribution": float(sum((e.contribution for e in entries), Decimal("0.00"))),
        }
