import unittest
from pathlib import Path

from src.core.resource_allocator import ResourceAllocator

ROOT = Path(__file__).resolve().parents[1]


class ResourceAllocatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = ResourceAllocator.from_file(ROOT / "config" / "resource-allocation.json")

    def test_baseline_totals_100(self):
        self.assertEqual(sum(self.a.config["baseline_percent"].values()), 100)

    def test_no_material_evidence_preserves_allocation(self):
        result = self.a.allocate({})
        self.assertFalse(result["changed"])
        self.assertEqual(result["reason"], "insufficient_material_evidence")

    def test_verified_revenue_can_increase_bucket_but_not_unbounded(self):
        e = {"media_engine": {"verified_revenue_events": 3, "conversion_events": 4, "automation_leverage": 1}}
        result = self.a.allocate(e)
        self.assertTrue(result["changed"])
        self.assertGreater(result["allocation"]["media_engine"], 25)
        self.assertLessEqual(result["allocation"]["media_engine"], 33)
        self.assertAlmostEqual(sum(result["allocation"].values()), 100, places=1)

    def test_production_failure_redirects_capacity(self):
        e = {"shared_infrastructure_jarvis": {"production_failure": True}}
        result = self.a.allocate(e)
        self.assertGreater(result["allocation"]["shared_infrastructure_jarvis"], 35)

    def test_single_conversion_does_not_trigger_rebalance(self):
        e = {"eventmatch": {"conversion_events": 1}}
        result = self.a.allocate(e)
        self.assertFalse(result["changed"])

    def test_bounds_are_respected(self):
        e = {"revenue_recovery": {"verified_revenue_events": 20, "conversion_events": 50, "near_revenue": 1}}
        allocation = self.a.allocate(e)["allocation"]
        for k, v in allocation.items():
            b = self.a.config["bounds_percent"][k]
            self.assertGreaterEqual(v, b["min"])
            self.assertLessEqual(v, b["max"])


if __name__ == "__main__":
    unittest.main()
