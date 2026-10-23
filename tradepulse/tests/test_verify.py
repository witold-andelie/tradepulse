import datetime as dt
from types import SimpleNamespace


from tradepulse.contracts import validate_payload
from tradepulse.verify import (check_cause_before_move, check_contributions_sum, check_no_future_data,
                               check_rerun_hash, failure_reasons, verify_claim)

AS_OF = dt.date(2026, 10, 21)
H1, H2 = "a" * 64, "b" * 64
UTC = dt.timezone.utc


def _ev(eid, sha=H1, **params):
    return {"evidence_id": eid, "query_template": "price_symbol_window",
            "params": params or {"symbol": "NVDA", "start": "2026-09-01", "end": "2026-10-21"},
            "rows_sha256": sha, "source_table": "price_bar", "as_of": "2026-10-21", "url": None}


class FakeAdapter:
    backend = "duckdb"

    def __init__(self, sha=H1, fail=False):
        self.sha, self.fail, self.calls = sha, fail, []

    def run(self, template, params):
        self.calls.append((template, params))
        if self.fail:
            raise ConnectionError("secret host 10.0.0.1")
        return SimpleNamespace(rows_sha256=self.sha)


def test_rerun_hash():
    assert check_rerun_hash(_ev("e1"), FakeAdapter())["passed"] is True
    bad = check_rerun_hash(_ev("e1"), FakeAdapter(sha=H2))
    assert bad["name"] == "rerun_hash_match" and bad["passed"] is False
    err = check_rerun_hash(_ev("e1"), FakeAdapter(fail=True))
    assert err["passed"] is False and "ConnectionError" in err["detail"] and "10.0.0.1" not in err["detail"]


def test_no_future_data():
    assert check_no_future_data(_ev("e1"), AS_OF)["passed"] is True
    late = _ev("e1", symbol="NVDA", start="2026-09-01", end="2026-10-22")
    assert check_no_future_data(late, AS_OF)["passed"] is False
    late_asof = dict(_ev("e1"), as_of="2026-10-22")
    assert check_no_future_data(late_asof, AS_OF)["passed"] is False


def test_cause_before_move():
    cause = dt.datetime(2026, 10, 20, 21, 0, tzinfo=UTC)
    move = dt.datetime(2026, 10, 21, 13, 30, tzinfo=UTC)
    assert check_cause_before_move(cause, move)["passed"] is True
    assert check_cause_before_move(move, cause)["passed"] is False
    missing = check_cause_before_move(None, move)
    assert missing["passed"] is False and missing["detail"] == "timing unknown"
    naive = check_cause_before_move(dt.datetime(2026, 10, 20), move)
    assert naive["passed"] is False


def test_contributions_sum():
    c = [{"factor": "a", "z": 1.0, "weight": 0.6, "contribution": 0.6}, {"factor": "b", "z": 0.5, "weight": 0.4, "contribution": 0.2}]
    assert check_contributions_sum(c, 0.8)["passed"] is True
    assert check_contributions_sum(c, 0.9)["passed"] is False


def test_verify_factor_claim():
    draft = {"claim_id": "c1", "text": "Momentum drives the score.", "kind": "factor", "evidence_ids": ["e1"]}
    adapter = FakeAdapter()
    claim = verify_claim(draft, {"e1": _ev("e1")}, adapter=adapter, as_of=AS_OF, score=0.8,
                         contributions=[{"factor": "a", "z": 1.0, "weight": 0.8, "contribution": 0.8}])
    assert validate_payload(claim, "Claim") == []
    assert claim["status"] == "verified"
    assert {c["name"] for c in claim["checks"]} == {"rerun_hash_match", "no_future_data", "contributions_sum"}
    assert adapter.calls == [("price_symbol_window", _ev("e1")["params"])]
    assert failure_reasons(claim) == []


def test_verify_rejects_unknown_evidence_and_missing_timing():
    draft = {"claim_id": "c2", "text": "A supplier reported a constraint.", "kind": "relation",
             "evidence_ids": ["e1", "ghost"]}
    claim = verify_claim(draft, {"e1": _ev("e1")}, adapter=FakeAdapter(), as_of=AS_OF)
    assert validate_payload(claim, "Claim") == []
    assert claim["status"] == "rejected"
    assert [e["evidence_id"] for e in claim["evidence"]] == ["e1"]
    reasons = failure_reasons(claim)
    assert any(r.startswith("schema:") and "ghost" in r for r in reasons)
    assert "cause_before_move: timing unknown" in reasons


def test_verify_rejects_empty_evidence_and_bad_hash():
    empty = verify_claim({"claim_id": "c3", "text": "x", "kind": "price", "evidence_ids": []}, {},
                         adapter=FakeAdapter(), as_of=AS_OF)
    assert empty["status"] == "rejected" and failure_reasons(empty)[0].startswith("schema:")
    hashed = verify_claim({"claim_id": "c4", "text": "x", "kind": "price", "evidence_ids": ["e1"]},
                          {"e1": _ev("e1")}, adapter=FakeAdapter(sha=H2), as_of=AS_OF)
    assert hashed["status"] == "rejected"
    assert any(r.startswith("rerun_hash_match:") for r in failure_reasons(hashed))


def test_verify_timed_claim_passes_with_timing():
    draft = {"claim_id": "c5", "text": "The 8-K preceded the move.", "kind": "event", "evidence_ids": ["e1"]}
    claim = verify_claim(draft, {"e1": _ev("e1")}, adapter=FakeAdapter(), as_of=AS_OF,
                         cause_time=dt.datetime(2026, 10, 20, 21, 0, tzinfo=UTC),
                         move_start=dt.datetime(2026, 10, 21, 13, 30, tzinfo=UTC))
    assert claim["status"] == "verified"
