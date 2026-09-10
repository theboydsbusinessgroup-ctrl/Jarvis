import unittest
from src.core.access_broker import AccessAttempt, AccessMethod, resolve_access


class AccessBrokerTests(unittest.TestCase):
    def test_existing_connector_wins_before_escalation(self):
        decision = resolve_access([
            AccessAttempt(AccessMethod.EXISTING_CONNECTOR, True, True, True, "active connector"),
            AccessAttempt(AccessMethod.HUMAN_AUTHORIZATION, True, False, True, "manual login"),
        ])
        self.assertTrue(decision.resolved)
        self.assertFalse(decision.escalate)
        self.assertEqual(decision.selected_method, AccessMethod.EXISTING_CONNECTOR)

    def test_oauth_refresh_precedes_human_login(self):
        decision = resolve_access([
            AccessAttempt(AccessMethod.EXISTING_CONNECTOR, False, True, True, "none"),
            AccessAttempt(AccessMethod.OAUTH_REFRESH, True, True, True, "refresh token valid"),
        ])
        self.assertEqual(decision.selected_method, AccessMethod.OAUTH_REFRESH)

    def test_non_least_privilege_path_is_not_used(self):
        decision = resolve_access([
            AccessAttempt(AccessMethod.SCOPED_TOKEN, True, True, False, "token too broad"),
        ])
        self.assertTrue(decision.escalate)
        self.assertFalse(decision.resolved)

    def test_security_bypass_is_never_attempted(self):
        decision = resolve_access([], requested_bypass="mfa_bypass")
        self.assertTrue(decision.escalate)
        self.assertIn("prohibited", decision.escalation_reason.lower())


if __name__ == "__main__":
    unittest.main()
