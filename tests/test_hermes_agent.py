import os
import unittest
from unittest.mock import patch

from src.integrations.hermes_agent import build_worker_prompt, call_hermes


class HermesAgentIntegrationTests(unittest.TestCase):
    def context(self):
        return {
            "task_id": "task-hermes-1",
            "trace_id": "trace-hermes-1",
            "project_id": "jarvis",
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

    def test_missing_key_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            result = call_hermes(task="Inspect a build", context=self.context())
        self.assertEqual(result.status, "not_configured")
        self.assertIn("HERMES_API_KEY", result.error)


if __name__ == "__main__":
    unittest.main()
