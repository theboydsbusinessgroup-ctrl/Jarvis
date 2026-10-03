import json
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.index import app
from src.integrations.revenue_feed import load_revenue_feed


class RevenueFeedTests(unittest.TestCase):
    def test_anonymous_cannot_read_financial_feed(self):
        with patch('api.index.load_revenue_feed') as fetch:
            self.assertEqual(TestClient(app).get('/api/revenue').status_code,401)
            fetch.assert_not_called()

    def test_missing_token_reports_unknown(self):
        with patch.dict('os.environ',{},clear=True):
            self.assertIsNone(load_revenue_feed()['gross_revenue'])

    def test_failure_never_becomes_zero_revenue(self):
        with patch.dict('os.environ',{'REVENUE_READ_TOKEN':'test'}),patch('src.integrations.revenue_feed.urlopen',side_effect=TimeoutError):
            self.assertEqual(load_revenue_feed()['status'],'unavailable')
            self.assertIsNone(load_revenue_feed()['gross_revenue'])
