import unittest
from pathlib import Path

from src.core.health_aggregator import aggregate, load_registry

ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    def test_registry_is_valid_and_unique(self):
        registry = load_registry(ROOT / "contracts" / "portfolio-registry.json")
        ids = [p["id"] for p in registry["registry"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 20)

    def test_live_revenue_systems_are_separate_from_verified_revenue(self):
        report = aggregate(load_registry(ROOT / "contracts" / "portfolio-registry.json"))
        product = next(p for p in report["projects"] if p["id"] == "productized_ai_service")
        self.assertEqual(product["lifecycle"], "live")
        self.assertEqual(product["revenue"], "pre_revenue")

    def test_user_actions_sort_first(self):
        registry = load_registry(ROOT / "contracts" / "portfolio-registry.json")
        snapshot = {"project_id": "eventmatch", "needs_user": True, "next_action": "Provide required credential.", "blockers": ["Credential required."]}
        report = aggregate(registry, [snapshot])
        self.assertEqual(report["action_queue"][0]["project_id"], "eventmatch")


if __name__ == "__main__":
    unittest.main()
