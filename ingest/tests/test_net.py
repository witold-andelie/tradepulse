import pytest
import requests

from ingest.net import IngestHTTPError, RateLimiter, build_session, get_with_retries


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.slept = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def test_rate_limiter_spaces_calls():
    fake = FakeClock()
    limiter = RateLimiter(4, clock=fake.clock, sleep=fake.sleep)
    for _ in range(5):
        limiter.wait()
    assert sum(fake.slept) == pytest.approx(1.0)


def test_rate_limiter_does_not_sleep_when_time_passed():
    fake = FakeClock()
    limiter = RateLimiter(2, clock=fake.clock, sleep=fake.sleep)
    limiter.wait()
    fake.now += 10
    limiter.wait()
    assert sum(fake.slept) == pytest.approx(0.0)


def test_build_session_sets_user_agent():
    session = build_session("tradepulse-dev contact@example.com")
    assert session.headers["User-Agent"] == "tradepulse-dev contact@example.com"


@pytest.mark.parametrize("ua", ["", "tradepulse-dev", "   "])
def test_build_session_requires_contact(ua):
    with pytest.raises(ValueError):
        build_session(ua)


class FakeResponse:
    def __init__(self, status):
        self.status_code = status


class FakeSession:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def get(self, url, timeout=None, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return FakeResponse(outcome)


def _limiter():
    fake = FakeClock()
    return RateLimiter(1000, clock=fake.clock, sleep=fake.sleep)


def test_retries_then_succeeds_with_backoff():
    session = FakeSession([429, 503, 200])
    slept = []
    resp = get_with_retries(session, "https://x", _limiter(), sleep=slept.append)
    assert resp.status_code == 200
    assert session.calls == 3
    assert slept == [1.0, 2.0]


def test_retries_on_timeout():
    session = FakeSession([requests.Timeout(), 200])
    resp = get_with_retries(session, "https://x", _limiter(), sleep=lambda s: None)
    assert resp.status_code == 200


def test_not_found_is_returned_without_retry():
    session = FakeSession([404])
    resp = get_with_retries(session, "https://x", _limiter(), sleep=lambda s: None)
    assert resp.status_code == 404
    assert session.calls == 1


def test_gives_up_after_attempts():
    session = FakeSession([500, 500, 500])
    with pytest.raises(IngestHTTPError):
        get_with_retries(session, "https://x", _limiter(), sleep=lambda s: None)
    assert session.calls == 3
