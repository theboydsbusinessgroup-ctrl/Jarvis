"""Owner-only, signed browser sessions; no worker credential reaches the client."""
import hashlib
import hmac
import os
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

COOKIE = "jarvis_owner"
SESSION_SECONDS = 30 * 24 * 60 * 60
_attempts = defaultdict(deque)
_lock = Lock()


def owner_key():
    return os.getenv("JARVIS_OWNER_KEY", "").strip()


def issue_session():
    expiry = str(int(time.time()) + SESSION_SECONDS)
    signature = hmac.new(owner_key().encode(), expiry.encode(), hashlib.sha256).hexdigest()
    return expiry + "." + signature


def authenticated(request: Request):
    key = owner_key()
    bearer = request.headers.get("authorization", "")
    if key and bearer:
        return hmac.compare_digest(bearer.encode(), ("Bearer " + key).encode())
    token = request.cookies.get(COOKIE, "")
    try:
        expiry, signature = token.split(".", 1)
        expected = hmac.new(key.encode(), expiry.encode(), hashlib.sha256).hexdigest()
        return bool(key) and int(expiry) > time.time() and hmac.compare_digest(signature, expected)
    except (ValueError, TypeError):
        return False


def require_same_origin(request: Request):
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Cross-origin request rejected")


def require_owner(request: Request):
    require_same_origin(request)
    if not authenticated(request):
        raise HTTPException(401, "Sign in to Jarvis first")


def rate_limit(bucket, limit=20):
    now = time.monotonic()
    with _lock:
        # Bounded process-local limiter; production currently runs one worker.
        if len(_attempts) > 4096:
            for key in list(_attempts):
                if not _attempts[key] or now - _attempts[key][-1] >= 60:
                    del _attempts[key]
        events = _attempts[bucket]
        while events and now - events[0] >= 60:
            events.popleft()
        if len(events) >= limit:
            raise HTTPException(429, "Please wait a minute before trying again")
        events.append(now)
