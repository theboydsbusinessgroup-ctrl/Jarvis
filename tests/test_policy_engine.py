import unittest
from pathlib import Path

from src.core.policy_engine import PolicyEngine

ROOT = Path(__file__).resolve().parents[1]


class PolicyEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = PolicyEngine.from_file(ROOT / "config" / "autonomy-policy.json")

    def test_code_commit_is_autonomous(self):
        self.assertEqual(self.engine.decide("commit_code")["decision"], "execute")

    def test_new_spend_requires_approval(self):
        self.assertEqual(self.engine.decide("new_spend")["decision"], "require_approval")

    def test_secret_exposure_is_prohibited(self):
        self.assertEqual(self.engine.decide("expose_secret")["decision"], "prohibited")

    def test_service_arbitrage_payment_gate_blocks_early_enablement(self):
        d = self.engine.decide("enable_customer_payment", project_id="service_arbitrage", context={"approved_provider_count": 1, "margin_gate_passes": True, "scope_gate_passes": True})
        self.assertEqual(d["decision"], "require_approval")

    def test_service_arbitrage_payment_gate_can_reach_approval_state(self):
        d = self.engine.decide("enable_customer_payment", project_id="service_arbitrage", context={"approved_provider_count": 2, "margin_gate_passes": True, "scope_gate_passes": True})
        self.assertEqual(d["decision"], "require_approval")
        self.assertEqual(d["reason"], "project_gate")

    def test_live_trading_is_prohibited_until_separate_validation(self):
        d = self.engine.decide("live_trade", project_id="autonomous_trading", context={})
        self.assertEqual(d["decision"], "require_approval")

    def test_deploy_requires_passing_ci(self):
        blocked = self.engine.decide("production_deploy", context={"ci":"failing", "new_spend":0, "secret_exposure":False})
        allowed = self.engine.decide("production_deploy", context={"ci":"passing", "new_spend":0, "secret_exposure":False})
        self.assertEqual(blocked["decision"], "require_approval")
        self.assertEqual(allowed["decision"], "execute")


if __name__ == "__main__":
    unittest.main()
