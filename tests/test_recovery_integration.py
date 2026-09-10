import tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
from api.index import build_state, recovery
from src.integrations.revenue_recovery import load_recovery_snapshot

class RecoveryIntegrationTests(unittest.TestCase):
    def test_control_plane_separates_recovery_value_from_revenue(self):
        state=build_state()
        self.assertIn('revenue_recovery',state)
        self.assertTrue(state['guardrails']['recovery_value_is_not_revenue'])
        self.assertEqual(state['revenue_recovery']['metrics']['verified_recovered_revenue'],0)
        self.assertEqual(state['verified_revenue']['gross_revenue'],0)

    def test_recovery_endpoint_is_read_only_snapshot(self):
        data=recovery()
        self.assertEqual(data['source'],'revenue-recovery')
        self.assertFalse(data['privacy']['customer_pii_included'])

    def test_missing_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            data=load_recovery_snapshot(Path(td)/'missing.json')
            self.assertFalse(data['available'])
            self.assertEqual(data['metrics']['recoverable_value_identified'],0)

if __name__=='__main__':unittest.main()
