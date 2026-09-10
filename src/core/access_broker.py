from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class AccessMethod(str, Enum):
    EXISTING_CONNECTOR = "existing_connector"
    OAUTH_REFRESH = "oauth_refresh"
    SUPPORTED_APP_AUTH = "supported_app_auth"
    SCOPED_TOKEN = "scoped_token"
    SERVICE_ACCOUNT = "service_account"
    HUMAN_AUTHORIZATION = "human_authorization"


@dataclass(frozen=True)
class AccessAttempt:
    method: AccessMethod
    available: bool
    autonomous: bool
    least_privilege: bool
    reason: str


@dataclass(frozen=True)
class AccessDecision:
    resolved: bool
    escalate: bool
    selected_method: AccessMethod | None
    attempts: tuple[AccessAttempt, ...]
    escalation_reason: str | None = None


SAFE_AUTONOMOUS_METHODS = {
    AccessMethod.EXISTING_CONNECTOR,
    AccessMethod.OAUTH_REFRESH,
    AccessMethod.SUPPORTED_APP_AUTH,
    AccessMethod.SCOPED_TOKEN,
    AccessMethod.SERVICE_ACCOUNT,
}

PROHIBITED_BYPASSES = {
    "mfa_bypass", "passkey_bypass", "captcha_bypass", "session_hijack",
    "credential_stuffing", "secret_exfiltration", "unauthorized_impersonation",
}


def resolve_access(attempts: list[AccessAttempt], *, requested_bypass: str | None = None) -> AccessDecision:
    if requested_bypass in PROHIBITED_BYPASSES:
        return AccessDecision(False, True, None, tuple(attempts), "Security bypass prohibited; human authorization is required.")

    ordered = [
        AccessMethod.EXISTING_CONNECTOR,
        AccessMethod.OAUTH_REFRESH,
        AccessMethod.SUPPORTED_APP_AUTH,
        AccessMethod.SCOPED_TOKEN,
        AccessMethod.SERVICE_ACCOUNT,
    ]
    for method in ordered:
        for attempt in attempts:
            if attempt.method == method and attempt.available and attempt.autonomous and attempt.least_privilege:
                return AccessDecision(True, False, method, tuple(attempts))

    return AccessDecision(False, True, AccessMethod.HUMAN_AUTHORIZATION, tuple(attempts), "No safe delegated or machine-to-machine access path remains.")
