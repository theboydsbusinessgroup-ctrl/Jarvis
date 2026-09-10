#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.core.health_aggregator import aggregate_files

if __name__ == "__main__":
    report = aggregate_files(ROOT / "contracts" / "portfolio-registry.json")
    print(json.dumps(report, indent=2))
