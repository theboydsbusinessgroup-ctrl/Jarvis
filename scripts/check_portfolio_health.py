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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("portfolio-health.json"))
    args = parser.parse_args()
    targets = json.loads((ROOT / "config/health-targets.json").read_text())["targets"]
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(check_target, targets))
    report = {"observed_at": datetime.now(timezone.utc).isoformat(), "mode": "read_only",
              "revenue_verified": False, "targets": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    for result in results:
        status = "INCIDENT" if result["incident"] else "ATTENTION" if result["attention"] else "READY"
        print(f"{result['project_id']}: {status}")
    return int(any(result["incident"] for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
