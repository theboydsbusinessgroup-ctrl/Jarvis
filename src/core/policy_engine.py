"""Deterministic autonomy decision engine for JARVIS."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class PolicyEngine:
    def __init__(self, policy: Mapping[str, Any]):
        if policy.get("schema_version") != "1.0":
            raise ValueError("Unsupported autonomy policy schema")
        self.policy = dict(policy)

    @classmethod
    def from_file(cls, path: str | Path) -> "PolicyEngine":
        with Path(path).open(encoding="utf-8") as fh:
            return cls(json.load(fh))

    def decide(self, action: str, *, project_id: str | None = None, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        context = dict(context or {})
        global_policy = self.policy["global"]

        if action in global_policy.get("prohibited", []):
            return self._result("prohibited", action, "global_prohibition")

        project_rule = ((self.policy.get("project_gates") or {}).get(project_id or "") or {}).get(action)
        if project_rule:
            if not self._conditions_met(project_rule.get("conditions", []), context):
                return self._result("require_approval", action, "project_conditions_not_met", project_rule.get("conditions", []))
            return self._result(project_rule["decision"], action, "project_gate", project_rule.get("conditions", []))

        grant = (self.policy.get("grants") or {}).get(action)
        if grant:
            if not self._conditions_met(grant.get("conditions", []), context):
                return self._result("require_approval", action, "grant_conditions_not_met", grant.get("conditions", []))
            return self._result(grant["decision"], action, "explicit_grant", grant.get("conditions", []))

        if action in global_policy.get("execute", []):
            return self._result("execute", action, "global_execute")
        if action in global_policy.get("require_approval", []):
            return self._result("require_approval", action, "global_approval")

        tier = str(context.get("authority_tier") or "UNKNOWN").upper()
        decision = self.policy["default_tier"].get(tier, self.policy["default_tier"]["UNKNOWN"])
        return self._result(decision, action, f"default_tier:{tier}")

    def _conditions_met(self, conditions: list[str], context: Mapping[str, Any]) -> bool:
        for condition in conditions:
            if condition == "no_new_spend" and context.get("new_spend", 0):
                return False
            if condition == "tests_or_ci_pass" and context.get("ci") not in {"passing", "success", True}:
                return False
            if condition == "no_secret_exposure" and context.get("secret_exposure"):
                return False
            if condition == "no_customer_opt_out" and context.get("customer_opt_out"):
                return False
            if condition == "approved_provider_count>=2" and int(context.get("approved_provider_count", 0)) < 2:
                return False
            if condition == "margin_gate_passes" and not context.get("margin_gate_passes"):
                return False
            if condition == "scope_gate_passes" and not context.get("scope_gate_passes"):
                return False
            if condition == "exact_spend_has_existing_authorization" and not context.get("exact_spend_has_existing_authorization"):
                return False
            if condition == "user_authentication_required":
                return False
            if condition == "until_separate_validation_and_live_allocation_authorization":
                return False
            if condition == "message_within_existing_offer_and_brand_rules" and not context.get("message_within_existing_offer_and_brand_rules"):
                return False
            if condition == "within_existing_follow_up_policy" and not context.get("within_existing_follow_up_policy"):
                return False
            if condition == "listing_content_preapproved_or_within_existing_product_scope" and not context.get("listing_content_preapproved_or_within_existing_product_scope"):
                return False
        return True

    @staticmethod
    def _result(decision: str, action: str, reason: str, conditions: list[str] | None = None) -> dict[str, Any]:
        return {"decision": decision, "action": action, "reason": reason, "conditions": conditions or []}
