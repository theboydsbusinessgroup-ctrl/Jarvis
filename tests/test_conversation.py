import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request, Response

from api.index import ConversationRequest, LoginRequest, app, conversation, owner_login
from src.core.conversation import converse
from src.core.owner_session import COOKIE, authenticated, issue_session, require_same_origin
from src.integrations.hermes_agent import HermesResult


def request(headers=()):
    return Request({"type": "http", "method": "POST", "scheme": "https", "path": "/api/conversation",
                    "headers": [(k.encode(), v.encode()) for k, v in headers],
                    "server": ("jarvis.test", 443), "client": ("127.0.0.1", 1234), "query_string": b""})


class ConversationTests(unittest.TestCase):
    def test_anonymous_cannot_call_worker(self):
        with patch("api.index.converse") as worker:
            with self.assertRaises(HTTPException) as cm:
                conversation(ConversationRequest(transcript="check my email"), request())
        self.assertEqual(cm.exception.status_code, 401)
        worker.assert_not_called()

    def test_cookie_signature_tamper_and_rotation(self):
        with patch.dict(os.environ, {"JARVIS_OWNER_KEY": "test-owner"}):
            token = issue_session()
            self.assertTrue(authenticated(request([("cookie", COOKIE + "=" + token)])))
            self.assertFalse(authenticated(request([("cookie", COOKIE + "=" + token + "bad")])))
        with patch.dict(os.environ, {"JARVIS_OWNER_KEY": "rotated-owner"}):
            self.assertFalse(authenticated(request([("cookie", COOKIE + "=" + token)])))

    def test_cross_origin_rejected(self):
        with self.assertRaises(HTTPException):
            require_same_origin(request([("origin", "https://other.test")]))

    def test_owner_login_cookie_is_private_and_secure(self):
        response = Response()
        with patch.dict(os.environ, {"JARVIS_OWNER_KEY": "test-owner"}):
            owner_login(LoginRequest(key="test-owner"), request(), response)
        cookie = response.headers["set-cookie"]
        for flag in ("HttpOnly", "Secure", "SameSite=strict"):
            self.assertIn(flag, cookie)
        self.assertNotIn("test-owner", cookie)

    def test_sleep_works_without_hermes(self):
        with patch("src.core.conversation.delegate_to_hermes") as worker:
            result = converse("Jarvis, go to sleep", {}, [], None)
        self.assertEqual(result["client_action"], "sleep")
        worker.assert_not_called()

    def test_model_cannot_inject_executable_client_action(self):
        model = HermesResult(status="ok", response='{"intent":"open_url","reply":"Proposed only","client_action":"shell","payload":{"command":"rm -rf /"}}')
        with patch("src.core.conversation.delegate_to_hermes", return_value=model):
            result = converse("could you organize my files", {}, [], None)
        self.assertIsNone(result["client_action"])
        self.assertIsNone(result["payload"])

    def test_natural_local_intent_uses_authoritative_state(self):
        model = HermesResult(status="ok", response='{"intent":"revenue_summary","reply":"You made a million dollars"}')
        with patch("src.core.conversation.delegate_to_hermes", return_value=model):
            result = converse("how much have we earned so far", {"verified_revenue":{"gross_revenue":12}}, [], None)
        self.assertIn("$12.00", result["reply"])
        self.assertNotIn("million", result["reply"])

    def test_unavailable_worker_does_not_claim_execution(self):
        with patch("src.core.conversation.delegate_to_hermes", return_value=HermesResult(status="disabled")):
            result = converse("please check important mail", {}, [], None)
        self.assertEqual(result["decision"], "not_connected")

    def test_public_config_never_contains_secrets(self):
        from api.index import voice_config
        with patch.dict(os.environ, {"JARVIS_OWNER_KEY":"owner-secret", "HERMES_API_KEY":"worker-secret"}):
            result = str(voice_config(request()))
        self.assertNotIn("owner-secret", result)
        self.assertNotIn("worker-secret", result)


if __name__ == "__main__":
    unittest.main()
