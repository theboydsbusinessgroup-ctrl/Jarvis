import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request
from api.index import owner_hermes_probe
from src.core.owner_session import COOKIE, issue_session
from src.integrations.hermes_agent import HermesResult


class OwnerHermesProbeTests(unittest.TestCase):
    def test_anonymous_cannot_use_the_worker(self):
        with patch.dict(os.environ, {"JARVIS_OWNER_KEY": "owner-test"}), \
             patch("api.index.delegate_to_hermes") as worker:
            request = Request({"type": "http", "method": "POST", "path": "/api/owner/hermes/probe", "headers": []})
            with self.assertRaises(HTTPException) as response:
                owner_hermes_probe(request)
        self.assertEqual(response.exception.status_code, 401)
        worker.assert_not_called()

    def test_signed_in_owner_can_verify_worker_without_service_secret(self):
        with patch.dict(os.environ, {"JARVIS_OWNER_KEY": "owner-test"}), \
             patch("api.index.rate_limit"), \
             patch("api.index.delegate_to_hermes", return_value=HermesResult(
                 status="ok", response="JARVIS_HERMES_E2E_OK")):
            cookie = (COOKIE + "=" + issue_session()).encode()
            request = Request({"type": "http", "method": "POST", "path": "/api/owner/hermes/probe",
                               "headers": [(b"cookie", cookie)]})
            response = owner_hermes_probe(request)
        self.assertTrue(response["worker_verified"])
        self.assertFalse(response["external_writes"])

    def test_arbitrary_worker_response_is_not_a_successful_probe(self):
        from api.index import _run_hermes_probe
        from fastapi import HTTPException
        with patch("api.index.delegate_to_hermes", return_value=HermesResult(status="ok", response="maybe")):
            with self.assertRaises(HTTPException) as error:
                _run_hermes_probe()
        self.assertEqual(error.exception.status_code, 502)
