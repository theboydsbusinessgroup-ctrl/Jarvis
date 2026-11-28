"""Read-only public readiness monitor. Never creates orders, pays, or publishes."""
from __future__ import annotations

import argparse
import json
import time
import socket
import ssl
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ATOM = {"a": "http://www.w3.org/2005/Atom"}
FEED_LIMIT = 262144


def fetch_json(url):
    if not url.startswith("https://"):
        raise ValueError("Health endpoints must use HTTPS")
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "jarvis-readiness-monitor/1"})
    with urlopen(request, timeout=15) as response:
        body = response.read(65537)
        if len(body) > 65536:
            raise ValueError("Health response exceeds size limit")
        return json.loads(body)


def fetch_feed(url, attempts=2):
    """Fetch a public Atom feed (bounded, no DTDs). One retry absorbs transient feed errors."""
    if not url.startswith("https://"):
        raise ValueError("Publication feeds must use HTTPS")
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"Accept": "application/atom+xml", "User-Agent": "jarvis-readiness-monitor/1"})
            with urlopen(request, timeout=15) as response:
                body = response.read(FEED_LIMIT + 1)
            break
        except Exception:
            if attempt + 1 >= attempts:
                raise
            time.sleep(3)
    if len(body) > FEED_LIMIT:
        raise ValueError("Publication feed exceeds size limit")
    if b"<!DOCTYPE" in body or b"<!ENTITY" in body:
        raise ValueError("Publication feed must not declare a DTD")
    return body


def latest_feed_publication(body):
    """Return the newest Atom entry <published> time, or None when the feed has no entries."""
    root = ET.fromstring(body)
    stamps = []
    for entry in root.findall("a:entry", ATOM):
        value = entry.findtext("a:published", namespaces=ATOM)
        if value:
            stamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("Publication timestamp must be timezone-aware")
            stamps.append(stamp)
    return max(stamps) if stamps else None


def check_feed_target(target, result):
    """Publication evidence from a public channel feed: the newest public post must be recent."""
    try:
        body = fetch_feed(target["url"])
    except HTTPError as exc:  # HTTPError subclasses URLError, so it must be handled first.
        if exc.code >= 500 or exc.code == 429:
            result["attention"].append(f"Publication feed unavailable (HTTP {exc.code}); freshness unverified")
            return result
        raise
    except (URLError, TimeoutError, ConnectionError) as exc:  # socket timeouts are TimeoutError
        reason = getattr(exc, "reason", None)
        if isinstance(reason, (socket.gaierror, ssl.SSLCertVerificationError)):
            raise  # a wrong host or a failed certificate is a configuration fault, not an outage
        result["attention"].append(f"Publication feed unavailable ({type(exc).__name__}); freshness unverified")
        return result
    latest = latest_feed_publication(body)
    if latest is None:
        raise ValueError("No publication evidence in feed")
    now = datetime.now(timezone.utc)
    age = (now - latest).total_seconds() / 3600
    fresh = -1 <= age <= target.get("stale_after_hours", 48)
    # A timestamp ahead of this clock is not reported as evidence (downstream rejects future times).
    completed_at = latest.astimezone(timezone.utc).isoformat() if latest <= now else None
    result["readiness"] = {"status": "completed", "conclusion": "success" if fresh else "stale",
                           "completed_at": completed_at}
    if not fresh:
        result["incident"] = True
        result["attention"].append("No public post within the freshness window; check the publishing queue.")
    return result


def check_target(target):
    result = {"project_id": target["id"], "url": target["url"],
              "observed_at": datetime.now(timezone.utc).isoformat(), "incident": False, "attention": []}
    try:
        if target.get("kind") == "publication_feed":
            return check_feed_target(target, result)
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
