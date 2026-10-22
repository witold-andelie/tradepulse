"""Polite HTTP: contact User-Agent, rate limiting and bounded retries (task A1-A6)."""

from __future__ import annotations

import time
from typing import Callable

import requests

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


class IngestHTTPError(RuntimeError):
    """Raised when a request still fails after the last retry."""


class RateLimiter:
    """Guarantee at least 1 / max_per_second seconds between consecutive wait() returns.

    clock and sleep are injectable so tests can use a fake clock.
    The first call never sleeps.
    """

    def __init__(self, max_per_second: float, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        raise NotImplementedError("A1: implement RateLimiter.__init__")

    def wait(self) -> None:
        raise NotImplementedError("A1: implement RateLimiter.wait")


def build_session(user_agent: str) -> requests.Session:
    """Return a Session whose User-Agent header is user_agent.

    Raise ValueError when user_agent is empty or contains no e-mail address ('@'):
    SEC and Wikimedia require contact details.
    """
    raise NotImplementedError("A1: implement build_session")


def get_with_retries(session, url: str, limiter: RateLimiter, *, timeout: float = 30.0,
                     attempts: int = 3, backoff: float = 1.0,
                     sleep: Callable[[float], None] = time.sleep, **kwargs) -> requests.Response:
    """GET url, waiting on limiter before every attempt.

    - Status in RETRY_STATUSES, requests.Timeout or requests.ConnectionError -> retry after
      sleep(backoff * 2**i) for i = 0, 1, ... (so 1 s, 2 s with the defaults), up to `attempts`
      attempts in total.
    - Any other status (including 404) -> return the response immediately; the caller decides.
    - Still failing after the last attempt -> raise IngestHTTPError naming the url and last status.
    """
    raise NotImplementedError("A1: implement get_with_retries")
