"""Public, bounded service and publishing checks; no account credentials."""
from __future__ import annotations

import json
import time
from pathlib import Path
from threading import Lock

from scripts.check_portfolio_health import check_targets

ROOT = Path(__file__).resolve().parents[2]
_cache = None
_expires = 0.0
_lock = Lock()


def load_live_readiness():
    global _cache, _expires
    with _lock:
        if _cache is None or time.monotonic() >= _expires:
            targets = json.loads((ROOT / "config/health-targets.json").read_text())["targets"]
            _cache = check_targets(targets)
            _expires = time.monotonic() + 120
        return _cache
