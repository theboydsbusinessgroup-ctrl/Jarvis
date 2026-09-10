from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


HIGH_IMPACT_TERMS = (
    "buy ", "purchase", "spend", "pay ", "send money", "transfer",
    "delete", "destroy", "change password", "security setting",
    "sign contract", "submit binding", "live trade", "place trade",
    "withdraw", "wire ", "credential", "api key", "secret"
)


@dataclass
class CommandDecision:
    transcript: str
    intent: str
    decision: str
    reply: str
    client_action: str | None = None
    payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def route_command(transcript: str, state: dict[str, Any]) -> CommandDecision:
    raw = (transcript or "").strip()
    text = raw.lower()
    portfolio = state.get("portfolio", {})
    revenue = state.get("verified_revenue", {})
    recovery = state.get("revenue_recovery", {})

    if not raw:
        return CommandDecision(raw, "empty", "rejected", "I didn't catch that. Try again.")

    if any(term in text for term in HIGH_IMPACT_TERMS):
        return CommandDecision(
            raw, "high_impact_action", "require_approval",
            "I understood the command, but that action crosses a protected authority boundary. I will not execute it from an unconfirmed voice command.",
        )

    if any(x in text for x in ("reboot", "restart jarvis", "restart yourself")):
        return CommandDecision(raw, "reboot", "execute", "Reinitializing. Try to contain your excitement.", "reboot")
    if any(x in text for x in ("mute yourself", "voice off", "stop talking")):
        return CommandDecision(raw, "voice_off", "execute", "Voice channel muted.", "voice_off")
    if any(x in text for x in ("voice on", "start talking", "unmute yourself")):
        return CommandDecision(raw, "voice_on", "execute", "Voice channel online.", "voice_on")
    if any(x in text for x in ("sound off", "effects off", "sfx off")):
        return CommandDecision(raw, "sound_off", "execute", "Sound effects disabled.", "sound_off")
    if any(x in text for x in ("sound on", "effects on", "sfx on")):
        return CommandDecision(raw, "sound_on", "execute", "Sound effects enabled.", "sound_on")
    if any(x in text for x in ("refresh", "sync", "update status", "rescan")):
        return CommandDecision(raw, "refresh", "execute", "Synchronizing the control plane now.", "refresh")
    if any(x in text for x in ("what needs me", "need me", "needs eric", "my action items", "what do i need to do")):
        needs = portfolio.get("needs_user", [])
        if not needs:
            reply = "Nothing currently requires you. A rare and beautiful moment."
        else:
            names = [x.get("display_name", x.get("id", "project")) for x in needs[:4]]
            reply = f"{len(needs)} item{'s' if len(needs)!=1 else ''} need you. " + ", ".join(names) + "."
        return CommandDecision(raw, "needs_user", "execute", reply, "show_actions", {"needs_user": needs})
    if "revenue" in text or "money" in text or "first dollar" in text:
        gross = float(revenue.get("gross_revenue", 0) or 0)
        reply = f"Verified revenue is ${gross:,.2f}. I am not counting identified opportunities as revenue."
        return CommandDecision(raw, "revenue_summary", "execute", reply, "show_revenue", {"revenue": revenue, "recovery": recovery})
    if "project" in text or "portfolio" in text:
        count = portfolio.get("project_count", 0)
        live = (portfolio.get("counts", {}).get("deployment", {}) or {}).get("production_live", 0)
        reply = f"I am tracking {count} projects, with {live} currently marked production live."
        return CommandDecision(raw, "portfolio_summary", "execute", reply, "show_projects", {"project_count": count, "production_live": live})
    if any(x in text for x in ("status", "how are we doing", "system check", "report")):
        count = portfolio.get("project_count", 0)
        needs = len(portfolio.get("needs_user", []))
        gross = float(revenue.get("gross_revenue", 0) or 0)
        reply = f"Systems online. {count} projects tracked, ${gross:,.2f} verified revenue, and {needs} owner actions pending."
        return CommandDecision(raw, "status", "execute", reply, "status")
    if any(x in text for x in ("help", "what can i say", "commands")):
        return CommandDecision(raw, "help", "execute", "Try: status report, show revenue, what needs me, show projects, refresh systems, mute yourself, or reboot.", "help")

    return CommandDecision(
        raw, "unmapped_external_command", "not_connected",
        "I heard you, but that command is not yet connected to an authenticated execution tool. I will not pretend I executed it.",
    )
