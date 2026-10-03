import unittest
from unittest.mock import patch

from scripts.check_portfolio_health import check_target


class ReadinessTests(unittest.TestCase):
    def test_healthy_http_does_not_hide_disabled_checkout(self):
        target = {"id": "offer", "url": "https://offer.test/health", "required": {"payment_gate": True}}
        with patch("scripts.check_portfolio_health.fetch_json", return_value={"status": "ok", "payment_gate": False}):
            result = check_target(target)
        self.assertTrue(result["incident"])

    def test_known_provider_gate_is_attention_without_incident(self):
        target = {"id": "arbitrage", "url": "https://offer.test/health", "advisory": {"payment_ready": True}}
        with patch("scripts.check_portfolio_health.fetch_json", return_value={"payment_ready": False}):
            result = check_target(target)
        self.assertFalse(result["incident"])
        self.assertTrue(result["attention"])

    def test_unavailable_endpoint_is_unknown_not_ready(self):
        target = {"id": "offer", "url": "https://offer.test/health", "required": {"status": "ok"}}
        with patch("scripts.check_portfolio_health.fetch_json", side_effect=TimeoutError("private upstream detail")):
            result = check_target(target)
        self.assertTrue(result["incident"])
        self.assertNotIn("private upstream detail", str(result))

    def test_only_readiness_fields_are_preserved(self):
        target = {"id": "offer", "url": "https://offer.test/health", "required": {"status": "ok"}}
        with patch("scripts.check_portfolio_health.fetch_json", return_value={"status": "ok", "token": "private"}):
            result = check_target(target)
        self.assertFalse(result["incident"])
        self.assertNotIn("private", str(result))

    def test_malformed_response_fails_closed(self):
        with patch("scripts.check_portfolio_health.fetch_json", return_value=[]):
            result = check_target({"id": "offer", "url": "https://offer.test/health"})
        self.assertTrue(result["incident"])
