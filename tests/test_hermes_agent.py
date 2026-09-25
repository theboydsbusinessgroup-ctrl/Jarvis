import os
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.orchestration_gate import OrchestrationGate
from src.integrations.hermes_agent import build_worker_prompt, delegate_to_hermes

ROOT = Path(__file__).resolve().parents[1]


class HermesAgentIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = OrchestrationGate.from_file(ROOT / "config" / "orchestration-policy.json")

    def context(self):
        return {
            "task_id": "task-hermes-1",
            "trace_id": "trace-hermes-1",
            "project_id": "jarvis",
            "objective": "Inspect a failing build",
            "constraints": ["no live writes"],
            "authority_context": {"tier": "GREEN"},
            "evidence_refs": ["repo:Jarvis"],
        }

    def test_prompt_preserves_authority_and_forbidden_actions(self):
        prompt = build_worker_prompt(task="Inspect a failing build", context=self.context(), role="specialist")
        self.assertIn("task-hermes-1", prompt)
        self.assertIn("no live writes", prompt)
        self.assertIn("Do not move money", prompt)
        self.assertIn('"tier": "GREEN"', prompt)

    def test_missing_key_fails_closed_after_gate(self):
        with patch.dict(os.environ, {}, clear=True):
            result = delegate_to_hermes(
                gate=self.gate,
                task="Inspect a build",
                context=self.context(),
            )
        self.assertEqual(result.status, "not_configured")
        self.assertIn("HERMES_API_KEY", result.error)
        self.assertEqual(len(result.context_fingerprint), 64)

    def test_worker_limit_blocks_before_network_call(self):
        with patch("src.integrations.hermes_agent._call_hermes") as network:
            result = delegate_to_hermes(
                gate=self.gate,
                task="Inspect a build",
                context=self.context(),
                active_workers=4,
            )
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error, "max_parallel_workers_reached")
        network.assert_not_called()

    def test_missing_authority_context_blocks_before_network_call(self):
        context = self.context()
        del context["authority_context"]
        with patch("src.integrations.hermes_agent._call_hermes") as network:
            result = delegate_to_hermes(
                gate=self.gate,
                task="Inspect a build",
                context=context,
            )
        self.assertEqual(result.status, "blocked")
        self.assertIn("authority_context", result.error)
        network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
