from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse

from src.core.health_aggregator import aggregate, load_registry
from src.core.policy_engine import PolicyEngine
from src.core.resource_allocator import ResourceAllocator
from src.core.revenue_ledger import RevenueLedger
from src.core.command_router import route_command
from src.integrations.revenue_recovery import load_recovery_snapshot
from src.integrations.second_brain import call_second_brain

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "contracts" / "portfolio-registry.json"
POLICY_PATH = ROOT / "config" / "autonomy-policy.json"
ALLOCATION_PATH = ROOT / "config" / "resource-allocation.json"
DASHBOARD_PATH = ROOT / "web" / "dashboard.html"
RECOVERY_PATH = ROOT / "data" / "revenue-recovery.json"

app = FastAPI(title="JARVIS Control Plane", version="0.3.0")


def build_state() -> dict[str, Any]:
    registry = load_registry(REGISTRY_PATH)
    health = aggregate(registry)
    allocator = ResourceAllocator.from_file(ALLOCATION_PATH)
    ledger = RevenueLedger()
    recovery = load_recovery_snapshot(RECOVERY_PATH)
    return {
        "service": "jarvis-control-plane",
        "mode": "read_only",
        "schema_version": "1.2",
        "portfolio": health,
        "allocation": allocator.config["baseline_percent"],
        "verified_revenue": ledger.summary(),
        "revenue_recovery": recovery,
        "guardrails": {
            "revenue_truth": "verified_only",
            "recovery_value_is_not_revenue": True,
            "domain_systems_authoritative": True,
            "writes_enabled": False,
            "second_brain_advisory_only": True,
        },
    }


@app.get("/health")
def health() -> dict[str, Any]:
    state = build_state()
    return {
        "status": "ok",
        "service": state["service"],
        "mode": state["mode"],
        "project_count": state["portfolio"]["project_count"],
        "recovery_signal_status": state["revenue_recovery"]["status"],
    }


@app.get("/api/control-plane")
def control_plane() -> dict[str, Any]:
    return build_state()


@app.get("/api/projects")
def projects() -> dict[str, Any]:
    state = build_state()
    return {
        "projects": state["portfolio"]["projects"],
        "counts": state["portfolio"]["counts"],
        "action_queue": state["portfolio"]["action_queue"],
        "needs_user": state["portfolio"]["needs_user"],
    }


@app.get("/api/projects/{project_id}")
def project(project_id: str) -> dict[str, Any]:
    for item in build_state()["portfolio"]["projects"]:
        if item["id"] == project_id:
            return item
    raise HTTPException(status_code=404, detail="Project not found")


@app.get("/api/revenue")
def revenue() -> dict[str, Any]:
    return build_state()["verified_revenue"]


@app.get("/api/recovery")
def recovery() -> dict[str, Any]:
    return build_state()["revenue_recovery"]


@app.get("/api/allocation")
def allocation() -> dict[str, Any]:
    allocator = ResourceAllocator.from_file(ALLOCATION_PATH)
    return {
        "baseline": allocator.config["baseline_percent"],
        "bounds": allocator.config["bounds_percent"],
        "rules": allocator.config["rules"],
    }


@app.get("/api/policy/{project_id}/{action}")
def policy(project_id: str, action: str, authority_tier: str = "UNKNOWN") -> dict[str, Any]:
    engine = PolicyEngine.from_file(POLICY_PATH)
    return engine.decide(action, project_id=project_id, context={"authority_tier": authority_tier})


class VoiceCommandRequest(BaseModel):
    transcript: str


@app.post("/api/command")
def command(request: VoiceCommandRequest) -> dict[str, Any]:
    state = build_state()
    return route_command(request.transcript, state).to_dict()


class SecondBrainRequest(BaseModel):
    task: str = Field(min_length=3, max_length=12000)
    decision_criteria: str = Field(default="", max_length=4000)
    evidence: str = Field(default="", max_length=16000)
    review_mode: Literal["parallel", "adversarial"] = "parallel"


@app.post("/api/second-brain")
def second_brain(request: SecondBrainRequest) -> dict[str, Any]:
    """Advisory-only Claude review. This endpoint cannot execute external actions."""
    result = call_second_brain(
        task=request.task,
        decision_criteria=request.decision_criteria,
        evidence=request.evidence,
        review_mode=request.review_mode,
    )
    if result.status == "not_configured":
        raise HTTPException(status_code=503, detail=result.error)
    if result.status == "error":
        raise HTTPException(status_code=502, detail=result.error)
    return result.to_dict()


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_PATH.read_text(encoding="utf-8")
