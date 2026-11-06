"""Minimal, dependency-free API protection (P2.2).

Two small pieces, both injected as FastAPI dependencies from ``create_app``:

* :class:`SlidingWindowRateLimiter` — an in-memory sliding window keyed by API
  key (when configured) or client IP. **Process-local only**: workers/replicas
  do not share state, so this is a single-process abuse guard, not a
  distributed rate limiter.
* :func:`build_auth_dependency` / :func:`build_rate_limit_dependency` — closures
  bound to the app's :class:`~openmetaphysics.core.config.Settings`.

Compatibility contract: when ``Settings.api_key`` is unset (the default),
both dependencies are no-ops, so existing callers see exactly the same
responses as before (no auth headers, no 429s).
"""

from __future__ import annotations

import hmac
import math
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request

from ..core.config import Settings

#: How long a sliding window covers. Kept as a module constant so tests can
#: reason about ``Retry-After`` without reaching into private attributes.
RATE_LIMIT_WINDOW_SECONDS = 60.0


class SlidingWindowRateLimiter:
    """In-memory sliding-window limiter (one process; not distributed).

    ``now`` is injectable so tests can advance a virtual clock instead of
    sleeping; production uses ``time.monotonic``.
    """

    def __init__(
        self,
        window_seconds: float = RATE_LIMIT_WINDOW_SECONDS,
        now: Callable[[], float] | None = None,
    ) -> None:
        self.window_seconds = window_seconds
        self.now = now or time.monotonic
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, identity: str, limit: int) -> tuple[bool, int]:
        """Record one hit; return ``(allowed, retry_after_seconds)``.

        ``retry_after_seconds`` is 0 when allowed and a positive number of
        whole seconds (suitable for the ``Retry-After`` header) when limited.
        """
        if limit <= 0:
            return True, 0
        current = self.now()
        cutoff = current - self.window_seconds
        with self._lock:
            events = self._events.setdefault(identity, deque())
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, math.ceil(self.window_seconds - (current - events[0])))
                return False, retry_after
            events.append(current)
            return True, 0

    def reset(self) -> None:
        """Drop all recorded events (used by tests and graceful shutdown)."""
        with self._lock:
            self._events.clear()


def _extract_key(request: Request) -> str:
    """API key from ``X-API-Key`` or ``Authorization: Bearer`` (empty if absent)."""
    header = request.headers.get("x-api-key")
    if header:
        return header.strip()
    authorization = request.headers.get("authorization", "")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() == "bearer":
        return value.strip()
    return ""


def _client_identity(request: Request) -> str:
    client = request.client
    return client.host if client is not None else "unknown"


def build_auth_dependency(settings: Settings) -> Callable[[Request], None]:
    """Require an API key only when ``settings.api_key`` is configured.

    Missing key -> 401 (with ``WWW-Authenticate: Bearer``); wrong key -> 403.
    When no key is configured the dependency is a no-op (legacy compatibility).
    """

    expected = (settings.api_key or "").strip()

    def require_api_key(request: Request) -> None:
        if not expected:
            return
        supplied = _extract_key(request)
        if not supplied:
            raise HTTPException(
                status_code=401,
                detail="missing API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not hmac.compare_digest(supplied, expected):
            raise HTTPException(status_code=403, detail="invalid API key")

    return require_api_key


def build_rate_limit_dependency(
    settings: Settings,
    limiter: SlidingWindowRateLimiter,
) -> Callable[[Request], None]:
    """Apply the sliding-window limit only in API-key-protected mode.

    Without ``api_key`` the dependency is a no-op so unconfigured deployments
    keep the exact pre-P2.2 behaviour. ``rate_limit_per_minute <= 0`` disables
    limiting even when a key is configured.
    """

    limit = settings.rate_limit_per_minute
    enabled = bool((settings.api_key or "").strip()) and limit > 0

    def enforce_rate_limit(request: Request) -> None:
        if not enabled:
            return
        api_key = _extract_key(request) or _client_identity(request)
        allowed, retry_after = limiter.hit(api_key, limit)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )

    return enforce_rate_limit


def redact_birth_data(value: Any) -> Any:
    """Recursively drop ``born_at`` / ``born_location`` keys from a JSON value.

    Returns a new structure; the stored session is never mutated. Used only
    when ``Settings.session_redact_birth`` is true (default false = unchanged).
    """
    if isinstance(value, dict):
        return {
            key: redact_birth_data(item)
            for key, item in value.items()
            if key not in {"born_at", "born_location"}
        }
    if isinstance(value, list):
        return [redact_birth_data(item) for item in value]
    return value
