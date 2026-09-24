import unittest

from src.core.connector_reliability import (
    ConnectorCallError,
    FaultKind,
    RetryPolicy,
    call_with_reliability,
    classify_http_status,
)


class ConnectorReliabilityTests(unittest.TestCase):
    def test_rate_limit_retries_with_same_idempotency_key(self):
        seen = []
        sleeps = []

        def operation(key):
            seen.append(key)
            if len(seen) < 3:
                raise ConnectorCallError("rate limited", kind=FaultKind.RATE_LIMIT)
            return {"ok": True}

        result = call_with_reliability(
            operation,
            idempotency_key="op-123",
            retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0.01),
            sleep_fn=sleeps.append,
        )
        self.assertEqual(result.attempts, 3)
        self.assertEqual(seen, ["op-123", "op-123", "op-123"])
        self.assertEqual(result.faults, ("rate_limit", "rate_limit"))
        self.assertEqual(len(sleeps), 2)

    def test_auth_failure_does_not_retry(self):
        attempts = []

        def operation(key):
            attempts.append(key)
            raise ConnectorCallError("unauthorized", kind=FaultKind.AUTH, status_code=401)

        with self.assertRaises(ConnectorCallError):
            call_with_reliability(operation, idempotency_key="auth-1", sleep_fn=lambda _: None)
        self.assertEqual(len(attempts), 1)

    def test_timeout_is_bounded(self):
        attempts = []

        def operation(key):
            attempts.append(key)
            raise TimeoutError("slow")

        with self.assertRaises(ConnectorCallError) as ctx:
            call_with_reliability(
                operation,
                idempotency_key="timeout-1",
                retry_policy=RetryPolicy(max_attempts=2, base_delay_seconds=0),
                sleep_fn=lambda _: None,
            )
        self.assertEqual(ctx.exception.kind, FaultKind.TIMEOUT)
        self.assertEqual(len(attempts), 2)

    def test_partial_response_fails_closed_without_retry(self):
        attempts = []

        def operation(key):
            attempts.append(key)
            return {"status": "ok"}

        with self.assertRaises(ConnectorCallError) as ctx:
            call_with_reliability(
                operation,
                idempotency_key="partial-1",
                validate=lambda value: "required_field" in value,
                sleep_fn=lambda _: None,
            )
        self.assertEqual(ctx.exception.kind, FaultKind.PARTIAL)
        self.assertEqual(len(attempts), 1)

    def test_http_fault_classification(self):
        self.assertEqual(classify_http_status(401), FaultKind.AUTH)
        self.assertEqual(classify_http_status(403), FaultKind.FORBIDDEN)
        self.assertEqual(classify_http_status(429), FaultKind.RATE_LIMIT)
        self.assertEqual(classify_http_status(503), FaultKind.SERVER)


if __name__ == "__main__":
    unittest.main()
