import unittest

from src.core.protocol_boundary import build_protocol_envelope, route_protocol


class ProtocolBoundaryTests(unittest.TestCase):
    def test_tools_and_data_route_to_mcp(self):
        self.assertEqual(route_protocol("tool"), "mcp")
        self.assertEqual(route_protocol("data"), "mcp")

    def test_agents_route_to_a2a(self):
        self.assertEqual(route_protocol("agent"), "a2a")

    def test_unknown_target_is_rejected(self):
        with self.assertRaises(ValueError):
            route_protocol("magic")

    def test_envelope_carries_trace_and_context_identity(self):
        envelope = build_protocol_envelope(
            target_kind="agent",
            target_id="second-brain",
            task_id="task-9",
            trace_id="trace-9",
            payload={"prompt": "review"},
            context={"objective": "review", "authority_context": {"tier": "GREEN"}},
        )
        data = envelope.to_dict()
        self.assertEqual(data["protocol"], "a2a")
        self.assertEqual(data["target_kind"], "agent")
        self.assertEqual(data["trace_id"], "trace-9")
        self.assertEqual(len(data["context_fingerprint"]), 64)


if __name__ == "__main__":
    unittest.main()
