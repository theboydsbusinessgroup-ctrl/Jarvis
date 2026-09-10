import unittest

from src.core.event_bus import EventBus
from src.core.revenue_ledger import RevenueLedger


def payment_event(event_id="evt_local_1", source_event_id="stripe_evt_1"):
    return {
        "schema_version": "1.1",
        "event_id": event_id,
        "project_id": "productized_ai_service",
        "event_type": "payment.completed",
        "source_system": "stripe",
        "source_event_id": source_event_id,
        "occurred_at": "2026-09-10T16:30:00+00:00",
        "idempotency_key": source_event_id,
        "amount": 49.00,
        "currency": "USD",
        "confidence": 1,
        "evidence": ["stripe:checkout.session.completed:stripe_evt_1"],
        "payload": {"fees": 4.00, "fulfillment_cost": 0, "advertising_cost": 0}
    }


class EventBusRevenueTests(unittest.TestCase):
    def test_payment_flows_once_into_ledger(self):
        ledger = RevenueLedger()
        bus = EventBus()
        bus.subscribe("payment.completed", ledger.record_event)
        first = bus.publish(payment_event())
        second = bus.publish(payment_event(event_id="evt_local_duplicate"))
        self.assertTrue(first["accepted"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(ledger.summary()["gross_revenue"], 49.0)
        self.assertEqual(ledger.summary()["contribution"], 45.0)

    def test_checkout_start_is_not_revenue(self):
        ledger = RevenueLedger()
        event = payment_event()
        event["event_type"] = "checkout.started"
        self.assertFalse(ledger.record_event(event)["recorded"])
        self.assertEqual(ledger.summary()["verified_entries"], 0)

    def test_unverified_payment_is_rejected(self):
        ledger = RevenueLedger()
        event = payment_event()
        event["confidence"] = 0.9
        with self.assertRaises(ValueError):
            ledger.record_event(event)

    def test_refund_reduces_contribution(self):
        ledger = RevenueLedger()
        ledger.record_event(payment_event())
        refund = payment_event("evt_refund_1", "stripe_refund_1")
        refund["event_type"] = "payment.refunded"
        refund["amount"] = 10
        refund["payload"] = {}
        refund["evidence"] = ["stripe:refund:stripe_refund_1"]
        ledger.record_event(refund)
        self.assertEqual(ledger.summary()["refunds"], 10.0)
        self.assertEqual(ledger.summary()["contribution"], 35.0)


if __name__ == "__main__":
    unittest.main()
