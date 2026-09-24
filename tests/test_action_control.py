import tempfile
import unittest
from pathlib import Path

from src.core.action_control import AutonomyControlPlane, JsonCheckpointStore, ToolPolicyRegistry
from src.core.policy_engine import PolicyEngine

ROOT = Path(__file__).resolve().parents[1]


class ActionControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        engine = PolicyEngine.from_file(ROOT / "config" / "autonomy-policy.json")
        registry = ToolPolicyRegistry.from_file(ROOT / "config" / "tool-policy.json")
        store = JsonCheckpointStore(Path(self.tempdir.name) / "approvals.json")
        self.control = AutonomyControlPlane(engine, registry, store)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_green_read_is_auto_approved(self):
        record = self.control.propose("github", "read", {"repo": "example"}, operation_id="read-1")
        self.assertEqual(record["status"], "approved")
        self.assertEqual(record["policy"]["decision"], "execute")

    def test_external_send_checkpoints_exact_state_until_approval(self):
        record = self.control.propose(
            "gmail",
            "send",
            {"to": "client@example.com", "body": "hello"},
            workflow_state={"step": 4, "lead_id": "lead-17"},
            operation_id="send-1",
        )
        self.assertEqual(record["status"], "pending_approval")
        resumed = self.control.resume("send-1")
        self.assertEqual(resumed["payload"]["to"], "client@example.com")
        self.assertEqual(resumed["workflow_state"]["lead_id"], "lead-17")

        approved = self.control.approve("send-1", approved=True, actor="owner")
        self.assertEqual(approved["status"], "approved")

    def test_unknown_tool_fails_closed(self):
        record = self.control.propose("new_connector", "surprise_write", {"x": 1}, operation_id="unknown-1")
        self.assertEqual(record["risk"], "RED")
        self.assertEqual(record["status"], "pending_approval")

    def test_prohibited_action_cannot_be_approved(self):
        record = self.control.propose("security", "expose_secret", {}, operation_id="secret-1")
        self.assertEqual(record["status"], "prohibited")
        with self.assertRaises(PermissionError):
            self.control.approve("secret-1", approved=True)

    def test_duplicate_execution_returns_stored_result(self):
        self.control.propose("github", "read", {"repo": "example"}, operation_id="idem-1")
        calls = []

        def executor(**kwargs):
            calls.append(kwargs)
            return {"ok": True, "key": kwargs["idempotency_key"]}

        first = self.control.execute("idem-1", executor)
        second = self.control.execute("idem-1", executor)
        self.assertFalse(first["replayed"])
        self.assertTrue(second["replayed"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(first["record"]["result"], second["record"]["result"])


if __name__ == "__main__":
    unittest.main()
