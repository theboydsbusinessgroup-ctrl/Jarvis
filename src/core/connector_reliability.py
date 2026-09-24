"""Connector reliability primitives: bounded retries, fault classification, and fail-closed validation."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class FaultKind(str, Enum):
    AUTH = "auth"
    FORBIDDEN = "forbidden"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    SERVER = "server"
    MALFORMED = "malformed"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class ConnectorCallError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        kind: FaultKind = FaultKind.UNKNOWN,
        status_code: int | None = None,
        retry_after: float | None = None,
    ):
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code
        self.retry_after = retry_after


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 8.0

    def delay_for(self, attempt: int) -> float:
        return min(self.max_delay_seconds, self.base_delay_seconds * (2 ** max(0, attempt - 1)))


@dataclass(frozen=True)
class ConnectorCallResult(Generic[T]):
    value: T
    attempts: int
    faults: tuple[str, ...]
    idempotency_key: str


def classify_http_status(status_code: int) -> FaultKind:
    if status_code == 401:
        return FaultKind.AUTH
    if status_code == 403:
        return FaultKind.FORBIDDEN
    if status_code == 429:
        return FaultKind.RATE_LIMIT
    if 500 <= status_code <= 599:
        return FaultKind.SERVER
    return FaultKind.UNKNOWN


RETRYABLE = {FaultKind.RATE_LIMIT, FaultKind.TIMEOUT, FaultKind.SERVER}


def call_with_reliability(
    operation: Callable[[str], T],
    *,
    idempotency_key: str,
    retry_policy: RetryPolicy | None = None,
    validate: Callable[[T], bool] | None = None,
    sleep_fn: Callable[[float], None] = sleep,
) -> ConnectorCallResult[T]:
    """Execute with bounded retries while preserving one mutation identity.

    The operation must accept the idempotency key and should forward it to the
    provider whenever the provider supports idempotent mutations.
    """
    if not idempotency_key:
        raise ValueError("idempotency_key is required")
    policy = retry_policy or RetryPolicy()
    if policy.max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    faults: list[str] = []
    for attempt in range(1, policy.max_attempts + 1):
        try:
            value = operation(idempotency_key)
            if validate is not None and not validate(value):
                raise ConnectorCallError("Connector response failed validation", kind=FaultKind.PARTIAL)
            return ConnectorCallResult(
                value=value,
                attempts=attempt,
                faults=tuple(faults),
                idempotency_key=idempotency_key,
            )
        except ConnectorCallError as exc:
            faults.append(exc.kind.value)
            if exc.kind not in RETRYABLE or attempt >= policy.max_attempts:
                raise
            delay = exc.retry_after if exc.retry_after is not None else policy.delay_for(attempt)
            sleep_fn(max(0.0, delay))
        except TimeoutError as exc:
            faults.append(FaultKind.TIMEOUT.value)
            if attempt >= policy.max_attempts:
                raise ConnectorCallError(
                    str(exc) or "Connector timed out",
                    kind=FaultKind.TIMEOUT,
                ) from exc
            sleep_fn(policy.delay_for(attempt))

    raise AssertionError("unreachable")
