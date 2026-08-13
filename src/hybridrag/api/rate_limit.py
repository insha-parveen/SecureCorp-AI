"""Simple in-memory rate limiter for the API.

This is a lightweight, dependency-free rate limiter suitable for a
single-process deployment. It uses a sliding window per user/IP.

For multi-process deployments, swap this for a Redis-based limiter
(e.g., ``slowapi`` with a Redis backend) without changing the route
handlers — the interface is the same.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Sliding-window rate limiter keyed by an arbitrary string."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        """Raise 429 if ``key`` has exceeded the rate limit."""
        now = time.monotonic()
        window_start = now - self._window_seconds

        # Drop expired timestamps.
        hits = self._hits[key]
        while hits and hits[0] < window_start:
            hits.popleft()

        if len(hits) >= self._max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

        hits.append(now)

    def reset(self, key: str) -> None:
        """Clear the rate-limit state for ``key`` (e.g., on logout)."""
        self._hits.pop(key, None)


# Module-level singleton. In a multi-process deployment this would be
# replaced by a Redis-backed limiter.
_rate_limiter = InMemoryRateLimiter(max_requests=60, window_seconds=60)


def rate_limit() -> Callable[[Request], None]:
    """FastAPI dependency that enforces a per-client rate limit.

    The client key is derived from the ``X-Forwarded-For`` header (when
    present) or the client IP. In production behind a proxy, the proxy
    must set ``X-Forwarded-For``.
    """

    def _dependency(request: Request) -> None:
        # Use the forwarded IP if available, else the direct client IP.
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"
        _rate_limiter.check(f"{client_ip}:{request.url.path}")

    return _dependency
