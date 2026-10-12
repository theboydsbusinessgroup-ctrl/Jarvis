"""Read-only public readiness monitor. Never creates orders, pays, or publishes."""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def fetch_json(url):
    if not url.startswith("https://"):
        raise ValueError("Health endpoints must use HTTPS")
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "jarvis-readiness-monitor/1"})
    with urlopen(request, timeout=15) as response:
        body = response.read(65537)
        if len(body) > 65536:
            raise ValueError("Health response exceeds size limit")
        return json.loads(body)


def check_target(target):
    result = {"project_id": target["id"], "url": target["url"],
              "observed_at": datetime.now(timezone.utc).isoformat(), "incident": False, "attention": []}
    try:
        data = fetch_json(target["url"])
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        if target.get("kind") == "github_workflow":
            runs = data.get("workflow_runs")
            if not isinstance(runs, list) or not runs:
                raise ValueError("No publication workflow evidence")
            run = runs[0]
            if run.get("head_branch") != "main":
                raise ValueError("Unexpected publication branch")
            conclusion = run.get("conclusion")
            result["readiness"] = {"status": run.get("status"), "conclusion": conclusion,
                                   "run_id": run.get("id"), "completed_at": run.get("updated_at")}
            if run.get("status") != "completed":
                result["attention"].append("Publication workflow is still running; success is not verified.")
            elif conclusion != "success":
                result["incident"] = True
                result["attention"].append("Latest publication workflow failed or was cancelled; inspect its job log.")
            timestamp = run.get("updated_at")
            observed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - observed).total_seconds() / 3600
            if age < -1 or age > target.get("stale_after_hours", 48):
                result["incident"] = True
                result["attention"].append("Publication workflow evidence is stale or has an invalid timestamp.")
            return result
        # Preserve only explicitly configured readiness fields, never entire responses.
        fields = {**target.get("required", {}), **target.get("advisory", {})}
        result["readiness"] = {key: data.get(key) for key in fields}
        for key, expected in target.get("required", {}).items():
            if data.get(key) != expected:
                result["incident"] = True
                result["attention"].append(f"Required readiness field failed: {key}")
        for key, expected in target.get("advisory", {}).items():
            if data.get(key) != expected:
                result["attention"].append(f"Setup or freshness remains incomplete: {key}")
    except Exception as exc:
        result["incident"] = True
        # Do not print upstream response bodies or configuration values.
        result["attention"].append(f"Endpoint verification unavailable: {type(exc).__name__}")
    return result


def check_targets(targets):
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(check_target, targets))
    for result in results:
        result["status"] = "incident" if result["incident"] else "attention" if result["attention"] else "ready"
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "mode": "read_only",
            "revenue_verified": False, "targets": results,
            "incident_count": sum(r["incident"] for r in results),
            "attention_count": sum(bool(r["attention"]) and not r["incident"] for r in results)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("portfolio-health.json"))
    args = parser.parse_args()
    targets = json.loads((ROOT / "config/health-targets.json").read_text())["targets"]
    report = check_targets(targets)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    for result in report["targets"]:
        status = "INCIDENT" if result["incident"] else "ATTENTION" if result["attention"] else "READY"
        print(f"{result['project_id']}: {status}")
    return int(bool(report["incident_count"]))


if __name__ == "__main__":
    raise SystemExit(main())
