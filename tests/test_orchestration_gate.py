import unittest
from pathlib import Path

from src.core.orchestration_gate import OrchestrationGate

ROOT = Path(__file__).resolve().parents[1]


class OrchestrationGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = OrchestrationGate.from_file(ROOT / "config" / "orchestration-policy.json")

    @staticmethod
    def context():
        return {
            "task_id": "task-1",
            "trace_id": "trace-1",
            "project_id": "jarvis",
            "objective": "Test a bounded specialist delegation",
            "constraints": ["no live writes"],
            "authority_context": {"tier": "GREEN"},
            "evidence_refs": ["repo:Jarvis"],
            "incidental": "not preserved",
        }

    def test_valid_specialist_delegation_is_allowed(self):
        decision = self.gate.evaluate(
            current_depth=0,
            active_workers=0,
            target_role="specialist",
            context=self.context(),
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.next_depth, 1)
        self.assertEqual(len(decision.context_fingerprint), 64)

    def test_depth_is_bounded(self):
        decision = self.gate.evaluate(
            current_depth=2,
            active_workers=0,
            target_role="specialist",
            context=self.context(),
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "max_delegation_depth_exceeded")

    def test_parallelism_is_bounded(self):
        decision = self.gate.evaluate(
            current_depth=0,
            active_workers=4,
            target_role="reviewer",
            context=self.context(),
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "max_parallel_workers_reached")

    def test_missing_critical_context_blocks_delegation(self):
        context = self.context()
        del context["authority_context"]
        decision = self.gate.evaluate(
            current_depth=0,
            active_workers=0,
            target_role="specialist",
            context=context,
        )
        self.assertFalse(decision.allowed)
        self.assertIn("authority_context", decision.missing_context)

    def test_context_fingerprint_detects_material_change(self):
        context = self.context()
        decision = self.gate.evaluate(
            current_depth=0,
            active_workers=0,
            target_role="reviewer",
            context=context,
        )
        self.assertTrue(self.gate.verify_preserved_context(context, decision.context_fingerprint))
        context["constraints"] = ["live writes allowed"]
        self.assertFalse(self.gate.verify_preserved_context(context, decision.context_fingerprint))


if __name__ == "__main__":
    unittest.main()
