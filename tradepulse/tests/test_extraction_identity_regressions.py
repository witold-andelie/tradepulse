"""SYNTHETIC documents reproduce share-class cache collisions without network calls."""

import hashlib
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from tradepulse.extract.grounding import ExtractionCache
from tradepulse.extract.runner import complete_event, run_extraction

TEXT = "SYNTHETIC: the company raised its full-year guidance."
SHA = hashlib.sha256(TEXT.encode()).hexdigest()


def document(symbol):
    return {"symbol": symbol, "sha256": SHA, "accession_number": "SYNTHETIC-ACCESSION",
            "document_type": "EX-99.1", "text": TEXT,
            "available_at": pd.Timestamp("2026-10-23T12:00:00Z")}


class Model:
    def __init__(self):
        self.calls = 0

    def complete(self, *_args, **_kwargs):
        self.calls += 1
        return SimpleNamespace(model="SYNTHETIC", text=json.dumps({"events": [
            {"event_type": "guidance_raise", "quote": TEXT, "direction": 1}]}))


def test_shared_document_does_not_reuse_another_share_class_events(tmp_path):
    docs = pd.DataFrame([document("SYNTHETIC-A"), document("SYNTHETIC-B")])
    cache = ExtractionCache(tmp_path / "cache.jsonl")
    model = Model()
    first = run_extraction(docs, model, cache, max_docs=2)
    assert model.calls == 2
    assert {e["symbol"] for e in first["events"]} == {"SYNTHETIC-A", "SYNTHETIC-B"}
    assert len({e["event_id"] for e in first["events"]}) == 2
    again = run_extraction(docs, Model(), ExtractionCache(cache.path), max_docs=0)
    assert again["cached"] == 2 and again["events"] == first["events"]


def test_legacy_cache_reuses_only_matching_provenance_without_rewriting_it(tmp_path):
    cache = ExtractionCache(tmp_path / "cache.jsonl")
    doc = document("SYNTHETIC-A")
    original = complete_event({"event_type": "guidance_raise", "quote": TEXT}, doc, "SYNTHETIC")
    cache.put(SHA, [original])
    prefix = cache.path.read_bytes()
    model = Model()
    out = run_extraction(pd.DataFrame([doc, document("SYNTHETIC-B")]), model, cache, max_docs=2)
    assert model.calls == 1 and out["cached"] == 1
    assert len({e["event_id"] for e in out["events"]}) == 2
    assert cache.path.read_bytes().startswith(prefix)
    replay_model = Model()
    replay = run_extraction(pd.DataFrame([doc, document("SYNTHETIC-B")]), replay_model,
                            ExtractionCache(cache.path), max_docs=2)
    assert replay_model.calls == 0 and replay["cached"] == 2


def test_identical_grounded_repetitions_are_counted_once(tmp_path):
    doc = document("SYNTHETIC-A")
    out = run_extraction(pd.DataFrame([doc, doc]), Model(), ExtractionCache(tmp_path / "c"), max_docs=2)
    assert len(out["events"]) == 1
    assert out["duplicate_events"] == 1


def test_conflicting_grounded_identity_is_not_silently_dropped(tmp_path):
    doc = document("SYNTHETIC-A")
    event = complete_event({"event_type": "guidance_raise", "quote": TEXT}, doc, "SYNTHETIC")
    cache = ExtractionCache(tmp_path / "c")
    cache.put(SHA, [event, {**event, "direction": -1}])
    with pytest.raises(ValueError, match="Conflicting grounded event identity"):
        run_extraction(pd.DataFrame([doc]), Model(), cache, max_docs=0)


def test_identity_conflict_is_not_downgraded_to_empty_pipeline_factors(monkeypatch, tmp_path):
    from tradepulse import pipeline
    from tradepulse.extract.grounding import ExtractionIdentityError
    from tradepulse.trace import Tracer

    monkeypatch.setattr(pipeline, "validate_edges", lambda *_args, **_kwargs: [])

    def conflict(*_args, **_kwargs):
        raise ExtractionIdentityError("Conflicting grounded event identity")

    monkeypatch.setattr(pipeline, "run_extraction", conflict)
    prices = pd.DataFrame({"SYNTHETIC-A": [1.0]}, index=pd.to_datetime(["2026-10-23"]))
    reference = pd.DataFrame({"SPY": [1.0]}, index=prices.index)
    query = SimpleNamespace(run=lambda *_args: SimpleNamespace(df=pd.DataFrame()))
    with pytest.raises(ExtractionIdentityError):
        pipeline._signal_panels({"extract": {"max_docs_per_run": 200}}, query, Model(),
                                [{"pool": "us_equity", "prices": prices}], reference,
                                "2026-01-01", "2026-10-23", tmp_path / "c",
                                Tracer("synthetic-identity-run", "SYNTHETIC", log_dir=tmp_path, echo=False), [])
