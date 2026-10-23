import datetime as dt
import json

import pytest

from tradepulse.contracts import validate_payload
from tradepulse.trace import REDACTED, Tracer, redact

T0 = dt.datetime(2026, 10, 22, 8, 0, 0, tzinfo=dt.timezone.utc)


@pytest.mark.parametrize("text", [
    "Authorization: Bearer abc.DEF-123",
    "key nvapi-AbC_123-xyz used",
    "api_key=sk-12345 then",
    "token: 9f8e7d",
    "PASSWORD = hunter2",
])
def test_redact_removes_secrets(text):
    out = redact(text)
    assert REDACTED in out
    for secret in ("abc.DEF-123", "nvapi-AbC_123-xyz", "sk-12345", "9f8e7d", "hunter2"):
        assert secret not in out


def test_redact_keeps_normal_text():
    assert redact("ranked 520 names in us_equity") == "ranked 520 names in us_equity"


def test_events_are_valid_sequential_and_persisted(tmp_path, capsys):
    t = Tracer("run-0001-test", "REPLAY", log_dir=tmp_path, clock=lambda: T0)
    e0 = t.event("rank", "info", message="ranked", payload={"n": 3})
    e1 = t.event("explain", "llm_call", model="m", tokens_in=10, tokens_out=2,
                 payload={"note": "Bearer abcdef123", "nested": {"list": ["token=zzz9"]}})
    assert (e0["seq"], e1["seq"]) == (0, 1)
    assert e0["ts"] == "2026-10-22T08:00:00Z" or e0["ts"].startswith("2026-10-22T08:00:00")
    assert e0["ts"].endswith("Z")
    assert t.path == tmp_path / "trace-run-0001-test.jsonl"
    lines = t.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        assert validate_payload(json.loads(line), "TraceEvent") == []
    assert "abcdef123" not in lines[1] and "zzz9" not in lines[1]
    assert t.events()[1]["model"] == "m"
    out = capsys.readouterr().out
    assert "[0000] rank info ok ranked" in out


def test_echo_can_be_disabled(tmp_path, capsys):
    Tracer("run-0002-test", "REAL", log_dir=tmp_path, echo=False).event("x", "info")
    assert capsys.readouterr().out == ""


def test_span_success(tmp_path):
    t = Tracer("run-0003-test", "SYNTHETIC", log_dir=tmp_path, echo=False)
    with t.span("settle", "settling"):
        pass
    kinds = [(e["node"], e["kind"], e["status"]) for e in t.events()]
    assert kinds == [("settle", "node_start", "ok"), ("settle", "node_end", "ok")]
    assert t.events()[1]["duration_ms"] >= 0


def test_span_error_is_traced_and_reraised(tmp_path):
    t = Tracer("run-0004-test", "SYNTHETIC", log_dir=tmp_path, echo=False)
    with pytest.raises(KeyError):
        with t.span("rank"):
            raise KeyError("api_key=abc999")
    last = t.events()[-1]
    assert last["kind"] == "error" and last["status"] == "error"
    assert last["message"].startswith("KeyError")
    assert "abc999" not in last["message"]
