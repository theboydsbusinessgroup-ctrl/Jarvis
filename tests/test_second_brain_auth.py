import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request

from api.index import SecondBrainRequest, etsy_callback, second_brain, build_state
from src.integrations.second_brain import SecondBrainResult
from src.integrations.second_brain import call_second_brain


def request(headers=()):
    return Request({'type': 'http', 'method': 'POST', 'scheme': 'https', 'path': '/api/second-brain',
                    'headers': [(key.encode(), value.encode()) for key, value in headers],
                    'server': ('jarvis.test', 443), 'query_string': b''})


class SecondBrainSecurityTests(unittest.TestCase):
    def test_anonymous_request_cannot_read_state_or_spend(self):
        with patch('api.index.call_second_brain') as worker:
            with self.assertRaises(HTTPException) as error:
                second_brain(SecondBrainRequest(task='Review my projects'), request())
        self.assertEqual(error.exception.status_code, 401)
        worker.assert_not_called()

    def test_authenticated_owner_can_request_review(self):
        result = SecondBrainResult(status='ok', model='test', review_mode='parallel', response='review')
        with patch.dict(os.environ, {'JARVIS_OWNER_KEY': 'test-owner'}), patch('api.index.call_second_brain', return_value=result):
            response = second_brain(SecondBrainRequest(task='Review my projects'), request([('authorization', 'Bearer test-owner')]))
        self.assertEqual(response['response'], 'review')

    def test_etsy_error_is_plain_text_not_executable_html(self):
        response = etsy_callback(error='<script>alert(1)</script>')
        self.assertNotIn('<script>', response)
        self.assertIn('&lt;script&gt;', response)

    def test_unconnected_ledger_does_not_claim_observed_zero(self):
        result = build_state()['verified_revenue']
        self.assertEqual(result['status'], 'not_connected')
        self.assertIsNone(result['observed_at'])

    def test_reasoning_only_response_is_not_returned_as_final_answer(self):
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}), \
             patch('src.integrations.second_brain.build_context_packet', return_value='test packet'), \
             patch('src.integrations.second_brain._request_json', return_value={
                 'choices': [{'message': {'content': '', 'reasoning': 'private internal reasoning'}}],
             }):
            result = call_second_brain(task='Review the portfolio')
        self.assertEqual(result.status, 'error')
        self.assertIsNone(result.response)
        self.assertNotIn('private internal reasoning', result.error)
