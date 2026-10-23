"""Polite HTTP: contact User-Agent, rate limiting and bounded retries (task A1-A6)."""

from __future__ import annotations

import math
import threading
import time
from typing import Callable

import requests

RETRY_STATUSES = frozenset({429, *range(500, 600)})


class IngestHTTPError(RuntimeError):
    """Raised when a request still fails after the last retry."""


class RateLimiter:
    """Guarantee at least 1 / max_per_second seconds between consecutive wait() returns.

    clock and sleep are injectable so tests can use a fake clock.
    The first call never sleeps.
    """

    def __init__(
        self,
        max_per_second: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not math.isfinite(max_per_second) or max_per_second <= 0:
            raise ValueError("max_per_second must be positive and finite")
        self._interval = 1.0 / max_per_second
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = self._clock()
            if self._last is not None:
                delay = self._last + self._interval - now
                if delay > 0:
                    self._sleep(delay)
            self._last = self._clock()


def build_session(user_agent: str) -> requests.Session:
    """Return a Session whose User-Agent header is user_agent.

    Raise ValueError when user_agent is empty or contains no e-mail address ('@'):
    SEC and Wikimedia require contact details.
    """
    if not user_agent.strip() or "@" not in user_agent:
        raise ValueError("A contact User-Agent is required in the provider environment variable")
    session = requests.Session()
    session.headers["User-Agent"] = user_agent
    session.max_redirects = 5
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
    """GET url, waiting on limiter before every attempt.

    - Status in RETRY_STATUSES, requests.Timeout or requests.ConnectionError -> retry after
      sleep(backoff * 2**i) for i = 0, 1, ... (so 1 s, 2 s with the defaults), up to `attempts`
      attempts in total.
    - Any other status (including 404) -> return the response immediately; the caller decides.
    - Still failing after the last attempt -> raise IngestHTTPError naming the url and last status.
    """
    if attempts < 1 or attempts > 3:
        raise ValueError("attempts must be between 1 and 3")
    if not math.isfinite(timeout) or timeout <= 0 or timeout > 30:
        raise ValueError("timeout must be positive and at most 30 seconds")
    if not math.isfinite(backoff) or backoff < 0:
        raise ValueError("backoff must be nonnegative and finite")
    # Return non-retry statuses literally, including redirects. Automatic redirect
    # requests would bypass the limiter; providers use canonical URLs in callers.
    kwargs.setdefault("allow_redirects", False)
    last = "unknown"
    for attempt in range(attempts):
        limiter.wait()
        try:
            response = session.get(url, timeout=timeout, **kwargs)
        except (requests.Timeout, requests.ConnectionError) as error:
            last = type(error).__name__
        else:
            if response.status_code not in RETRY_STATUSES:
                return response
            last = str(response.status_code)
            if hasattr(response, "close"):
                response.close()
        if attempt + 1 < attempts:
            sleep(backoff * 2**attempt)
    raise IngestHTTPError(f"GET {url} failed after {attempts} attempts; last status: {last}")


class YahooAdapter(requests.adapters.HTTPAdapter):
    """Apply the same policy to all yfinance transport calls, including cookies and POSTs.

    yfinance owns its protocol and parsing; the adapter limits each actual HTTP attempt.
    urllib3 retries are disabled to avoid multiplying the bounded retry budget.
    """

    def __init__(self, limiter: RateLimiter) -> None:
        super().__init__(max_retries=0)
        self._limiter = limiter

    def send(self, request: requests.PreparedRequest, **kwargs) -> requests.Response:
        kwargs["timeout"] = 30.0
        last = "unknown"
        for attempt in range(3):
            self._limiter.wait()
            try:
                response = super().send(request, **kwargs)
            except (requests.Timeout, requests.ConnectionError) as error:
                last = type(error).__name__
            else:
                if response.status_code not in RETRY_STATUSES:
                    return response
                last = str(response.status_code)
                response.close()
            if attempt < 2:
                time.sleep(2**attempt)
        raise IngestHTTPError(f"Yahoo request failed after 3 attempts; last status: {last}")
