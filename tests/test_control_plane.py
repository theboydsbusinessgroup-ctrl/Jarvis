import unittest

from api.index import build_state, health, project


class ControlPlaneTests(unittest.TestCase):
    def test_state_is_read_only_and_truth_preserving(self):
        state = build_state()
        self.assertEqual(state["mode"], "read_only")
        self.assertFalse(state["guardrails"]["writes_enabled"])
        self.assertEqual(state["guardrails"]["revenue_truth"], "verified_only")

    def test_health_exposes_project_count(self):
        data = health()
        self.assertEqual(data["status"], "ok")
        self.assertGreaterEqual(data["project_count"], 20)

    def test_known_project_lookup(self):
        data = project("productized_ai_service")
        self.assertEqual(data["id"], "productized_ai_service")
        self.assertEqual(data["revenue"], "pre_revenue")


if __name__ == "__main__":
    unittest.main()
