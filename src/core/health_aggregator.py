"""Evidence-preserving portfolio health aggregation for JARVIS."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


VALID_LIFECYCLES = {"backlog", "building", "testing", "revenue_ready", "live", "paused"}
VALID_DEPLOYMENTS = {"not_deployable", "build_ready", "preview_live", "production_live", "deployment_blocked"}
VALID_REVENUE = {"pre_revenue", "monetization_setup", "first_dollar", "generating_revenue", "profitable"}
VALID_CI = {"passing", "failing", "pending", "not_configured", "unknown"}


def load_registry(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    validate_registry(data)
    return data


def validate_registry(data: dict[str, Any]) -> None:
    if data.get("schema_version") != "2.0":
        raise ValueError("Portfolio registry must use schema_version 2.0")
    ids: set[str] = set()
    repos: set[str] = set()
    for item in data.get("registry", []):
        missing = {"id", "repository", "display_name", "lifecycle", "deployment", "revenue", "ci", "blockers", "next_action", "needs_user"} - set(item)
        if missing:
            raise ValueError(f"{item.get('id', '<unknown>')} missing fields: {sorted(missing)}")
        if item["id"] in ids or item["repository"] in repos:
            raise ValueError(f"Duplicate project identity: {item['id']} / {item['repository']}")
        ids.add(item["id"]); repos.add(item["repository"])
        if item["lifecycle"] not in VALID_LIFECYCLES: raise ValueError(f"Invalid lifecycle for {item['id']}")
        if item["deployment"] not in VALID_DEPLOYMENTS: raise ValueError(f"Invalid deployment for {item['id']}")
        if item["revenue"] not in VALID_REVENUE: raise ValueError(f"Invalid revenue state for {item['id']}")
        if item["ci"] not in VALID_CI: raise ValueError(f"Invalid CI state for {item['id']}")


def _priority(item: dict[str, Any]) -> tuple[int, int, int]:
    user = 0 if item.get("needs_user") else 1
    broken = 0 if item.get("ci") == "failing" or item.get("deployment") == "deployment_blocked" else 1
    lifecycle_rank = {"live": 0, "revenue_ready": 1, "testing": 2, "building": 3, "backlog": 4, "paused": 5}.get(item.get("lifecycle"), 9)
    return (user, broken, lifecycle_rank)


def aggregate(registry: dict[str, Any], snapshots: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    """Combine registry state with explicit snapshots; snapshots never invent missing facts."""
    projects = {item["id"]: dict(item) for item in registry["registry"]}
    for snap in snapshots:
        project_id = snap.get("project_id")
        if project_id not in projects:
            continue
        target = projects[project_id]
        for key in ("lifecycle", "deployment", "revenue", "ci", "blockers", "next_action", "needs_user"):
            if key in snap and snap[key] is not None:
                target[key] = snap[key]
        target["observed_at"] = snap.get("observed_at")
        target["evidence"] = list(snap.get("evidence") or [])
        if "revenue_usd" in snap: target["revenue_usd"] = snap["revenue_usd"]
        if "profit_usd" in snap: target["profit_usd"] = snap["profit_usd"]
        if "funnel" in snap: target["funnel"] = snap["funnel"]

    ordered = sorted(projects.values(), key=_priority)
    return {
        "schema_version": "1.0",
        "project_count": len(ordered),
        "counts": {
            "lifecycle": dict(Counter(p["lifecycle"] for p in ordered)),
            "deployment": dict(Counter(p["deployment"] for p in ordered)),
            "revenue": dict(Counter(p["revenue"] for p in ordered)),
            "ci": dict(Counter(p["ci"] for p in ordered)),
        },
        "needs_user": [p for p in ordered if p.get("needs_user")],
        "blocked": [p for p in ordered if p.get("blockers")],
        "action_queue": [{"project_id": p["id"], "display_name": p["display_name"], "next_action": p["next_action"], "needs_user": p["needs_user"]} for p in ordered if p.get("next_action")],
        "projects": ordered,
    }


def aggregate_files(registry_path: str | Path, snapshot_paths: Iterable[str | Path] = ()) -> dict[str, Any]:
    snapshots = []
    for path in snapshot_paths:
        with Path(path).open(encoding="utf-8") as fh:
            snapshots.append(json.load(fh))
    return aggregate(load_registry(registry_path), snapshots)
