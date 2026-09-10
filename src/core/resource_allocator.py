"""Bounded, evidence-driven portfolio resource allocation for JARVIS."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class ResourceAllocator:
    def __init__(self, config: Mapping[str, Any]):
        if config.get("schema_version") != "1.0":
            raise ValueError("Unsupported resource allocation schema")
        self.config = dict(config)
        if round(sum(self.config["baseline_percent"].values()), 6) != 100:
            raise ValueError("Baseline allocation must total 100")

    @classmethod
    def from_file(cls, path: str | Path) -> "ResourceAllocator":
        with Path(path).open(encoding="utf-8") as fh:
            return cls(json.load(fh))

    def score_bucket(self, bucket: str, evidence: Mapping[str, Any]) -> float:
        w = self.config["weights"]
        score = 0.0
        score += min(float(evidence.get("verified_revenue_events", 0)), 5) * w["verified_revenue"]
        score += min(float(evidence.get("conversion_events", 0)), 10) * w["conversion_signal"]
        score += (1 if evidence.get("needs_user") else 0) * w["user_blocker"]
        score += (1 if evidence.get("production_failure") else 0) * w["production_failure"]
        score += float(evidence.get("near_revenue", 0)) * w["near_revenue"]
        score += float(evidence.get("deployment_readiness", 0)) * w["deployment_readiness"]
        score += float(evidence.get("automation_leverage", 0)) * w["automation_leverage"]
        score += float(evidence.get("strategic_reuse", 0)) * w["strategic_reuse"]
        score += float(evidence.get("stale_no_signal", 0)) * w["stale_no_signal"]
        score += float(evidence.get("high_risk", 0)) * w["high_risk"]
        return round(score, 4)

    def allocate(self, evidence_by_bucket: Mapping[str, Mapping[str, Any]], previous: Mapping[str, float] | None = None) -> dict[str, Any]:
        baseline = {k: float(v) for k, v in self.config["baseline_percent"].items()}
        previous = {k: float(v) for k, v in (previous or baseline).items()}
        scores = {k: self.score_bucket(k, evidence_by_bucket.get(k, {})) for k in baseline}
        eligible_signal = any(
            sum(float(v) for key, v in evidence_by_bucket.get(k, {}).items() if key in {"verified_revenue_events", "conversion_events"}) >= self.config["minimum_evidence_count_for_signal_shift"]
            or evidence_by_bucket.get(k, {}).get("production_failure")
            or evidence_by_bucket.get(k, {}).get("needs_user")
            for k in baseline
        )
        if not eligible_signal:
            return {"allocation": previous, "scores": scores, "changed": False, "reason": "insufficient_material_evidence"}

        min_score = min(scores.values())
        positive = {k: (scores[k] - min_score + 1.0) for k in scores}
        total = sum(positive.values())
        target = {k: 100.0 * positive[k] / total for k in positive}

        inertia = float(self.config["inertia"])
        max_shift = float(self.config["max_shift_per_cycle"])
        proposed = {}
        for k in baseline:
            blended = inertia * previous[k] + (1 - inertia) * target[k]
            delta = max(-max_shift, min(max_shift, blended - previous[k]))
            lo = max(float(self.config["bounds_percent"][k]["min"]), previous[k] - max_shift)
            hi = min(float(self.config["bounds_percent"][k]["max"]), previous[k] + max_shift)
            proposed[k] = max(lo, min(hi, previous[k] + delta))

        proposed = self._normalize_with_bounds(proposed, previous)
        changed = any(abs(proposed[k] - previous[k]) >= 0.01 for k in proposed)
        return {"allocation": proposed, "scores": scores, "changed": changed, "reason": "material_evidence_rebalance"}

    def _normalize_with_bounds(self, values: Mapping[str, float], previous: Mapping[str, float]) -> dict[str, float]:
        result = {k: float(v) for k, v in values.items()}
        max_shift = float(self.config["max_shift_per_cycle"])
        effective_bounds = {
            k: (
                max(float(self.config["bounds_percent"][k]["min"]), float(previous[k]) - max_shift),
                min(float(self.config["bounds_percent"][k]["max"]), float(previous[k]) + max_shift),
            )
            for k in result
        }
        for _ in range(50):
            diff = 100.0 - sum(result.values())
            if abs(diff) < 0.0001:
                break
            if diff > 0:
                candidates = [k for k in result if result[k] < effective_bounds[k][1] - 1e-9]
            else:
                candidates = [k for k in result if result[k] > effective_bounds[k][0] + 1e-9]
            if not candidates:
                raise ValueError("Cannot normalize allocation within configured bounds and shift caps")
            share = diff / len(candidates)
            for k in candidates:
                lo, hi = effective_bounds[k]
                result[k] = max(lo, min(hi, result[k] + share))
        if abs(sum(result.values()) - 100.0) >= 0.01:
            raise ValueError("Allocation normalization did not converge to 100")
        return {k: round(v, 2) for k, v in result.items()}
