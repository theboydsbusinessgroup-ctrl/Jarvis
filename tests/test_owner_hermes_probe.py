import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from api.index import app
from src.integrations.hermes_agent import HermesResult


class OwnerHermesProbeTests(unittest.TestCase):
    def test_anonymous_cannot_use_the_worker(self):
        with patch.dict(os.environ, {"JARVIS_OWNER_KEY": "owner-test"}), \
             patch("api.index.delegate_to_hermes") as worker:
            response = TestClient(app).post("/api/owner/hermes/probe")
        self.assertEqual(response.status_code, 401)
        worker.assert_not_called()

    def test_signed_in_owner_can_verify_worker_without_service_secret(self):
        with patch.dict(os.environ, {"JARVIS_OWNER_KEY": "owner-test"}), \
             patch("api.index.rate_limit"), \
             patch("api.index.delegate_to_hermes", return_value=HermesResult(
                 status="ok", response="JARVIS_HERMES_E2E_OK")):
            client = TestClient(app, base_url="https://jarvis.test")
            login = client.post("/api/owner/login", json={"key": "owner-test"})
            self.assertEqual(login.status_code, 200)
            response = client.post("/api/owner/hermes/probe")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["worker_verified"])
        self.assertFalse(response.json()["external_writes"])

    def test_arbitrary_worker_response_is_not_a_successful_probe(self):
        from api.index import _run_hermes_probe
        from fastapi import HTTPException
        with patch("api.index.delegate_to_hermes", return_value=HermesResult(status="ok", response="maybe")):
            with self.assertRaises(HTTPException) as error:
                _run_hermes_probe()
        self.assertEqual(error.exception.status_code, 502)
