import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from scripts.check_portfolio_health import check_target


class ReadinessTests(unittest.TestCase):
    def test_failed_publication_is_an_incident_even_when_website_is_healthy(self):
        target = {"id": "media", "url": "https://api.github.com/example", "kind": "github_workflow"}
        run = {"head_branch": "main", "status": "completed", "conclusion": "failure",
               "updated_at": datetime.now(timezone.utc).isoformat(), "token": "private"}
        with patch("scripts.check_portfolio_health.fetch_json", return_value={"workflow_runs": [run]}):
            result = check_target(target)
        self.assertTrue(result["incident"])
        self.assertNotIn("private", str(result))

    def test_successful_old_publication_is_stale(self):
        target = {"id": "media", "url": "https://api.github.com/example", "kind": "github_workflow"}
        run = {"head_branch": "main", "status": "completed", "conclusion": "success",
               "updated_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()}
        with patch("scripts.check_portfolio_health.fetch_json", return_value={"workflow_runs": [run]}):
            self.assertTrue(check_target(target)["incident"])

    def test_recent_successful_publication_is_ready(self):
        target = {"id": "media", "url": "https://api.github.com/example", "kind": "github_workflow"}
        run = {"head_branch": "main", "status": "completed", "conclusion": "success",
               "updated_at": datetime.now(timezone.utc).isoformat()}
        with patch("scripts.check_portfolio_health.fetch_json", return_value={"workflow_runs": [run]}):
            result = check_target(target)
        self.assertFalse(result["incident"])
        self.assertFalse(result["attention"])

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


def atom(*published):
    entries = "".join(f"<entry><title>private title</title><published>{p}</published></entry>" for p in published)
    return f'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">{entries}</feed>'.encode()


FEED = {"id": "media", "url": "https://feed.test/videos.xml", "kind": "publication_feed", "stale_after_hours": 48}


class PublicationFeedTests(unittest.TestCase):
    def check(self, body):
        with patch("scripts.check_portfolio_health.fetch_feed", return_value=body):
            return check_target(FEED)

    def fail(self, exc):
        with patch("scripts.check_portfolio_health.fetch_feed", side_effect=exc):
            return check_target(FEED)

    def http_error(self, code):
        return HTTPError(FEED["url"], code, "err", {}, None)

    def test_feed_503_is_attention_not_incident(self):
        result = self.fail(self.http_error(503))
        self.assertFalse(result["incident"])
        self.assertEqual(result["attention"], ["Publication feed unavailable (HTTP 503); freshness unverified"])

    def test_feed_429_is_attention_not_incident(self):
        result = self.fail(self.http_error(429))
        self.assertFalse(result["incident"])
        self.assertEqual(len(result["attention"]), 1)

    def test_feed_network_errors_are_attention(self):
        for exc in (URLError("unreachable"), TimeoutError(), ConnectionResetError()):
            result = self.fail(exc)
            self.assertFalse(result["incident"], exc)
            self.assertEqual(len(result["attention"]), 1)

    def test_feed_404_is_still_an_incident(self):
        self.assertTrue(self.fail(self.http_error(404))["incident"])

    def test_recent_public_post_is_ready(self):
        now = datetime.now(timezone.utc)
        result = self.check(atom((now - timedelta(days=30)).isoformat(), (now - timedelta(hours=13)).isoformat()))
        self.assertFalse(result["incident"])
        self.assertFalse(result["attention"])
        self.assertEqual(result["readiness"]["conclusion"], "success")
        self.assertNotIn("private title", str(result))

    def test_no_recent_post_is_an_incident(self):
        result = self.check(atom((datetime.now(timezone.utc) - timedelta(hours=60)).isoformat()))
        self.assertTrue(result["incident"])
        self.assertEqual(result["readiness"]["conclusion"], "stale")

    def test_empty_feed_is_an_incident(self):
        self.assertTrue(self.check(atom())["incident"])

    def test_future_timestamp_is_not_reported_as_evidence(self):
        result = self.check(atom((datetime.now(timezone.utc) + timedelta(hours=5)).isoformat()))
        self.assertTrue(result["incident"])
        self.assertIsNone(result["readiness"]["completed_at"])

    def test_malformed_feed_fails_closed(self):
        self.assertTrue(self.check(b"<feed")["incident"])

    def test_dtd_is_refused(self):
        body = b'<?xml version="1.0"?><!DOCTYPE feed [<!ENTITY x "y">]><feed xmlns="http://www.w3.org/2005/Atom"/>'
        with patch("scripts.check_portfolio_health.urlopen") as opened:
            opened.return_value.__enter__.return_value.read.return_value = body
            result = check_target(FEED)
        self.assertTrue(result["incident"])

class FeedConfigurationFaultTests(unittest.TestCase):
    def _check(self, exc):
        with patch("scripts.check_portfolio_health.fetch_feed", side_effect=exc):
            return check_target(FEED)

    def test_dns_failure_stays_an_incident(self):
        import socket
        from urllib.error import URLError
        self.assertTrue(self._check(URLError(socket.gaierror(-2, "Name or service not known")))["incident"])

    def test_certificate_failure_stays_an_incident(self):
        import ssl
        from urllib.error import URLError
        self.assertTrue(self._check(URLError(ssl.SSLCertVerificationError("certificate verify failed")))["incident"])
