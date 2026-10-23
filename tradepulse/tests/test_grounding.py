import datetime as dt
import hashlib

import pytest

from tradepulse.extract.grounding import (ExtractionCache, demand_language_score, grounding_problems,
                                          make_event_id, normalize_text, quote_in_document)

DOC = ("Q3 results. Demand for our 1.6T optical modules continues to exceed   supply, and we have "
       "raised our full-year guidance. Customers “want more” — lead times are 40 weeks.")
SHA = hashlib.sha256(DOC.encode()).hexdigest()
AVAIL = dt.datetime(2026, 10, 20, 20, 5, tzinfo=dt.timezone.utc)


def _event(**kw):
    quote = "Demand for our 1.6T optical modules continues to exceed supply"
    ev = {
        "event_id": make_event_id(SHA, "COHR", "guidance_raise", quote), "doc_sha256": SHA,
        "accession_number": "0000000000-26-000001", "symbol": "COHR", "event_type": "guidance_raise",
        "direction": 1, "counterparty": None, "counterparty_symbol": None, "magnitude_usd": None,
        "novelty": "new",
        "demand_signals": [{"type": "demand_exceeds_supply", "polarity": 1, "quote": quote},
                           {"type": "guidance_raised", "polarity": 1, "quote": "raised our full-year guidance"}],
        "quote": quote, "available_at": "2026-10-20T20:05:00Z", "extractor_model": "meterless/fast",
        "schema_version": "1.0",
    }
    ev.update(kw)
    return ev


def test_normalize_and_quote_lookup():
    assert normalize_text("  “Want  More” — ok ") == '"want more" - ok'
    assert quote_in_document('customers "want more" - lead times', DOC)
    assert quote_in_document("continues to exceed supply", DOC)
    assert not quote_in_document("demand collapsed", DOC)
    assert not quote_in_document("   ", DOC)


def test_event_id_is_stable():
    a = make_event_id(SHA, "COHR", "guidance_raise", "Exceed  Supply")
    assert a == make_event_id(SHA, "COHR", "guidance_raise", "exceed supply") and len(a) == 24


def test_grounded_event_passes():
    assert grounding_problems(_event(), DOC, SHA, AVAIL) == []


@pytest.mark.parametrize("kw, prefix", [
    (dict(quote="Demand collapsed in Q3"), "quote:"),
    (dict(doc_sha256="f" * 64), "doc_sha256:"),
    (dict(available_at="2026-10-20T19:00:00Z"), "available_at:"),
    (dict(event_id="0" * 24), "event_id:"),
    (dict(demand_signals=[{"type": "demand_exceeds_supply", "polarity": -1, "quote": "raised our full-year guidance"}]), "polarity:"),
    (dict(demand_signals=[{"type": "price_increase", "polarity": 1, "quote": "prices rose 10%"}]), "demand_quote:"),
])
def test_grounding_problems(kw, prefix):
    ev = _event(**kw)
    if "quote" in kw:
        ev["event_id"] = make_event_id(SHA, "COHR", "guidance_raise", kw["quote"])
    problems = grounding_problems(ev, DOC, SHA, AVAIL)
    assert any(p.startswith(prefix) for p in problems), problems


def test_schema_failure_short_circuits():
    problems = grounding_problems(_event(event_type="moon_landing", quote="not in doc"), DOC, SHA, AVAIL)
    assert len(problems) == 1 and problems[0].startswith("schema:")


def test_demand_language_score():
    assert demand_language_score([]) is None
    assert demand_language_score([_event(demand_signals=[])]) is None
    assert demand_language_score([_event()]) == pytest.approx(2 / 3)
    neg = _event(demand_signals=[{"type": "guidance_cut", "polarity": -1, "quote": "x"}])
    assert demand_language_score([_event(), neg]) == pytest.approx((2 - 1) / 4)


def test_cache(tmp_path):
    c = ExtractionCache(tmp_path / "x.jsonl")
    assert not c.has(SHA)
    with pytest.raises(KeyError):
        c.get(SHA)
    c.put(SHA, [_event()])
    c.put(SHA, [])
    again = ExtractionCache(tmp_path / "x.jsonl")
    assert again.has(SHA) and again.get(SHA) == []
