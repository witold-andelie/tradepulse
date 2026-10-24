"""Bounded, rate-limited HTTP with contact identification."""

from __future__ import annotations

import math
import threading
import time
from collections.abc import Callable
from urllib.parse import urlsplit

import requests

RETRY_STATUSES = frozenset({429, *range(500, 600)})


class IngestHTTPError(RuntimeError):
    """A provider request failed after bounded retries."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class RateLimiter:
    def __init__(
        self,
        max_per_second: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not math.isfinite(max_per_second) or max_per_second <= 0:
            raise ValueError("max_per_second must be finite and positive")
        self.interval = 1 / max_per_second
        self.clock, self.sleep, self.last = clock, sleep, None
        self.lock = threading.Lock()

    def wait(self) -> None:
        with self.lock:
            now = self.clock()
            if self.last is not None:
                delay = self.last + self.interval - now
                if delay > 0:
                    self.sleep(delay)
            self.last = self.clock()


class PolicySession(requests.Session):
    """Apply timeouts and spacing to every transport send, including redirects."""

    def __init__(self):
        super().__init__()
        self.limiter = RateLimiter(1)
        self.max_redirects = 5

    def send(self, request, **kwargs):
        kwargs["timeout"] = kwargs.get("timeout") or 30.0
        self.limiter.wait()
        return super().send(request, **kwargs)


def build_session(user_agent: str) -> requests.Session:
    if not user_agent.strip() or "@" not in user_agent:
        raise ValueError("A contact User-Agent is required")
    session = PolicySession()
    session.headers["User-Agent"] = user_agent
    return session


def get_with_retries(
    session,
    url: str,
    limiter: RateLimiter,
    *,
    timeout: float = 30.0,
    attempts: int = 3,
    backoff: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
    **kwargs,
) -> requests.Response:
    if not isinstance(attempts, int) or not 1 <= attempts <= 3:
        raise ValueError("attempts must be between 1 and 3")
    if not math.isfinite(timeout) or not 0 < timeout <= 30:
        raise ValueError("timeout must be finite, positive and at most 30 seconds")
    if not math.isfinite(backoff) or backoff < 0:
        raise ValueError("backoff must be finite and nonnegative")
    last = "unknown"
    if isinstance(session, PolicySession):
        session.limiter = limiter
    for i in range(attempts):
        if not isinstance(session, PolicySession):
            limiter.wait()
        try:
            response = session.get(url, timeout=timeout, **kwargs)
            last = response.status_code
            if last not in RETRY_STATUSES:
                return response
        except (requests.Timeout, requests.ConnectionError) as exc:
            last = type(exc).__name__
        if i + 1 < attempts:
            sleep(backoff * 2**i)
    parsed = urlsplit(url)
    raise IngestHTTPError(
        f"GET {parsed.hostname}{parsed.path} failed: {last}",
        last if isinstance(last, int) else None,
    ) from None


def fetch_response(session, url, limiter):
    response = get_with_retries(session, url, limiter)
    if response.status_code != 200:
        raise IngestHTTPError(
            f"Provider returned HTTP {response.status_code}", response.status_code
        )
    return response
