"""SYNTHETIC in-process ports: wiring tests, never official-engine acceptance."""

import json
from copy import deepcopy
from unittest.mock import Mock

import pandas as pd
import pytest

from tradepulse.agents.prompts import analyst_messages
from tradepulse.contracts import REPO_ROOT, assert_payload
from tradepulse.engines import EngineBridge, EngineIntegrationError, configured_engines
from tradepulse.trace import Tracer

AS_OF = "2026-10-21"
EDGE = {"edge_id": "synthetic-edge", "src_symbol": "SYN-A", "dst_symbol": "SYN-B",
        "relation": "peer", "weight": 0.5, "source": "seed", "evidence_ref": None,
        "status": "validated", "lead_lag_t": 2.5, "valid_from": AS_OF}
EVENT = {"event_id": "synthetic-event", "doc_sha256": "0" * 64,
         "accession_number": "SYNTHETIC", "symbol": "SYN-A", "event_type": "guidance_raise",
         "direction": 1, "counterparty": None, "counterparty_symbol": None, "magnitude_usd": None,
         "novelty": "new", "demand_signals": [], "quote": "SYNTHETIC source quote.",
         "available_at": AS_OF + "T20:00:00Z", "extractor_model": "SYNTHETIC", "schema_version": "1.0"}


class FakeEngines:
    def __init__(self):
        self.calls, self.events, self.edges, self.records = [], [], [], []
        self.recalled = []

    def ingest_events(self, events):
        self.calls.append("ingest_events")
        self.events = deepcopy(events)
        return {"ingested": len(events), "duplicates": 0}

    def upsert_edges(self, edges):
        self.calls.append("upsert_edges")
        self.edges = deepcopy(edges)
        return {"upserted": len(edges)}

    def snapshot(self, as_of):
        self.calls.append("snapshot")
        return {"as_of": as_of, "events": deepcopy(self.events), "edges": deepcopy(self.edges)}

    def recall(self, symbol, as_of, k):
        self.calls.append("recall")
        return deepcopy(self.recalled)

    def remember(self, records):
        self.calls.append("remember")
        self.records = deepcopy(records)
        return {"added": len(records)}

    def settle(self, record_id, outcome):
        self.calls.append(("settle", record_id, outcome))
        return {"updated": 1}


@pytest.fixture
def bridge(tmp_path):
    tracer = Tracer("synthetic-engines-001", "SYNTHETIC", tmp_path, echo=False)
    return EngineBridge(FakeEngines(), AS_OF, tracer)


def pending_record():
    return {"id": "synthetic-memory", "symbol": "SYN-A", "as_of": "2026-10-16",
            "tier": "OVERWEIGHT", "horizon_days": 1,
            "content": {"execution_lag_days": 1},
            "provenance": {"run_id": "synthetic-run", "evidence_ids": []}}


def test_world_writes_grounded_events_and_only_validated_edges_then_reads_snapshot(bridge):
    rejected = dict(EDGE, edge_id="synthetic-rejected", status="rejected")
    events, edges = bridge.world_snapshot([EVENT], [EDGE, rejected])
    assert events == [EVENT] and edges == [EDGE]
    assert bridge.port.calls == ["ingest_events", "upsert_edges", "snapshot"]
    assert bridge.port.edges == [EDGE]
    events[0]["quote"] = "changed copy"
    assert bridge.port.events[0]["quote"] == EVENT["quote"]


@pytest.mark.parametrize("kind", ["event", "edge", "duplicate", "schema"])
def test_invalid_or_future_local_world_data_never_leaves_process(bridge, kind):
    events, edges = [deepcopy(EVENT)], [deepcopy(EDGE)]
    if kind == "event":
        events[0]["available_at"] = "2026-10-22T00:00:00Z"
    elif kind == "edge":
        edges[0]["valid_from"] = "2026-10-22"
    elif kind == "duplicate":
        events.append(deepcopy(EVENT))
    else:
        edges[0]["relation"] = "unagreed-field-value"
    with pytest.raises(EngineIntegrationError):
        bridge.world_snapshot(events, edges)
    assert bridge.port.calls == []


@pytest.mark.parametrize("snapshot", [
    {"as_of": "2026-10-22", "edges": [], "events": []},
    {"as_of": AS_OF, "edges": [], "events": [dict(EVENT, available_at="2026-10-22T00:00:00Z")]},
    {"as_of": AS_OF, "edges": [dict(EDGE, valid_from="2026-10-22")], "events": []},
    {"as_of": AS_OF, "edges": [], "events": [EVENT, EVENT]},
])
def test_bad_snapshot_is_rejected_before_factor_inputs_are_returned(bridge, snapshot):
    bridge.port.snapshot = Mock(return_value=snapshot)
    with pytest.raises(EngineIntegrationError):
        bridge.world_snapshot([], [])


def test_memory_is_bounded_unverified_context_without_raw_text_or_conflicts(bridge):
    record = pending_record()
    record["content"]["text"] = "SYNTHETIC untrusted instructions"
    bridge.port.recalled = [record]
    item = {"symbol": "SYN-A", "memory_context": None}
    enriched = bridge.prior_context([item])
    assert item["memory_context"] is None
    assert enriched[0]["memory_context"] == {"prior_record_count": 1, "verified_evidence": False}
    assert "untrusted" not in json.dumps(enriched)
    assert bridge.port.calls == ["recall"]


@pytest.mark.parametrize("mutation", ["future", "symbol", "too_many", "duplicate"])
def test_unsafe_memory_never_reaches_an_explanation(bridge, mutation):
    record = pending_record()
    if mutation == "future":
        record["as_of"] = "2026-10-22"
    elif mutation == "symbol":
        record["symbol"] = "OTHER"
    bridge.port.recalled = [record] * (11 if mutation == "too_many" else 2 if mutation == "duplicate" else 1)
    with pytest.raises(EngineIntegrationError):
        bridge.prior_context([{"symbol": "SYN-A"}])


def test_remember_preserves_values_provenance_and_stable_per_run_ids(bridge):
    output = json.loads((REPO_ROOT / "contracts/fixtures/run_output.fixture.json").read_text(encoding="utf-8"))
    output["recommendations"] = output["recommendations"][:2]
    original = deepcopy(output)
    first = bridge.remember(output, 1)
    second = bridge.remember(output, 1)
    assert first == second and output == original
    assert len({record["id"] for record in first}) == len(first)
    for record, row in zip(first, output["recommendations"]):
        assert record["content"]["recommendation"] == row
        assert record["provenance"]["run_id"] == output["run_id"]
        assert record["content"]["data_mode"] == "SYNTHETIC"
    output["run_id"] += "-new"
    assert bridge.remember(output, 1)[0]["id"] != first[0]["id"]


@pytest.mark.parametrize("tier, expected_hit", [("OVERWEIGHT", True), ("UNDERWEIGHT", False), ("NO_CALL", None)])
def test_feedback_uses_observed_entry_lag_horizon_benchmark_and_stance(bridge, tier, expected_hit):
    dates = pd.bdate_range("2026-10-16", periods=4)
    prices = pd.Series([100.0, 110.0, 120.0, 130.0], index=dates)
    benchmark = pd.Series([100.0, 101.0, 102.0, 103.0], index=dates)
    record = dict(pending_record(), tier=tier)
    assert bridge.feedback(record, prices, benchmark)
    operation, identity, outcome = bridge.port.calls[-1]
    assert operation == "settle" and identity == "synthetic-memory"
    expected = (prices.iloc[2] / prices.iloc[1] - 1) - (benchmark.iloc[2] / benchmark.iloc[1] - 1)
    assert outcome["excess_return"] == pytest.approx(expected)
    assert outcome["hit"] is expected_hit


@pytest.mark.parametrize("missing", ["immature", "benchmark", "price"])
def test_unobserved_outcome_is_deferred_without_feedback(bridge, missing):
    dates = pd.bdate_range("2026-10-16", periods=4)
    prices = pd.Series([100.0, 110.0, 120.0, 130.0], index=dates)
    benchmark = prices.copy()
    record = pending_record()
    if missing == "immature":
        record["horizon_days"] = 20
    elif missing == "benchmark":
        benchmark.iloc[2] = float("nan")
    else:
        prices.iloc[2] = float("nan")
    assert bridge.feedback(record, prices, benchmark) is False
    assert bridge.port.calls == []


def test_transport_failure_is_terminal_and_private_detail_never_enters_trace(bridge):
    detail = "SYNTHETIC private provider diagnostic"
    bridge.port.snapshot = Mock(side_effect=RuntimeError(detail))
    with pytest.raises(EngineIntegrationError) as caught:
        bridge.world_snapshot([], [])
    assert detail not in str(caught.value)
    assert detail not in bridge.tracer.path.read_text(encoding="utf-8")
    for event in bridge.tracer.events():
        assert_payload(event, "TraceEvent")


def test_sample_mode_never_constructs_an_environment_http_client(monkeypatch):
    monkeypatch.setenv("ENGINES_ENABLED", "true")
    monkeypatch.setenv("ENGINES_URL", "https://synthetic.invalid")
    constructor = Mock(side_effect=AssertionError("network client constructed"))
    monkeypatch.setattr("integrations.meterless.engines_client.EnginesClient", constructor)
    assert configured_engines(True) is None
    constructor.assert_not_called()


@pytest.mark.parametrize("url", ["", "http://remote.invalid", "ftp://localhost", "https://synthetic-user@synthetic.invalid"])
def test_invalid_live_engine_configuration_is_rejected(monkeypatch, url):
    monkeypatch.setenv("ENGINES_ENABLED", "true")
    monkeypatch.setenv("ENGINES_URL", url)
    with pytest.raises(ValueError):
        configured_engines(False)


def test_live_factory_is_explicit_bounded_and_uses_existing_client(monkeypatch):
    monkeypatch.setenv("ENGINES_ENABLED", "true")
    monkeypatch.setenv("ENGINES_URL", "https://synthetic.invalid/engines")
    constructor = Mock()
    monkeypatch.setattr("integrations.meterless.engines_client.EnginesClient", constructor)
    assert configured_engines(False) is constructor.return_value
    constructor.assert_called_once_with("https://synthetic.invalid/engines", timeout_s=10.0)


def test_pipeline_really_commits_snapshots_recalls_and_remembers(tmp_path, monkeypatch):
    from tradepulse import pipeline
    from tradepulse.tests.test_pipeline import LakeQuery, ScriptedLLM

    monkeypatch.setenv("SAMPLE_MODE", "true")
    monkeypatch.setattr(pipeline, "SAMPLE_ROOT", tmp_path)
    engine = FakeEngines()
    request = {"as_of": AS_OF, "pools": ["us_equity"], "tickers": [], "top_k": 1, "horizon_days": 5}
    output = pipeline.run_pipeline(request, query=LakeQuery(), llm=ScriptedLLM(), engines=engine,
                                   log_dir=tmp_path / "logs")
    assert_payload(output, "RunOutput")
    assert "ingest_events" in engine.calls and "snapshot" in engine.calls
    assert "recall" in engine.calls and engine.calls[-1] == "remember"
    assert len(engine.records) == len(output["recommendations"])
    assert engine.events and all(record["provenance"]["run_id"] == output["run_id"] for record in engine.records)


def test_prompt_marks_only_memory_counts_as_unverified_context():
    item = {"pool": "crypto", "symbol": "SYN-A", "name": "SYNTHETIC", "tier": "NO_CALL", "score": 0,
            "rank": 1, "n": 1, "as_of": AS_OF, "contributions": [],
            "memory_context": {"prior_record_count": 1, "verified_evidence": False}}
    content = analyst_messages(item, "SYNTHETIC evidence", [])[1]["content"]
    assert '"prior_record_count": 1' in content
    assert "not evidence" in content


@pytest.mark.parametrize("kind", ["events", "edges"])
def test_acknowledged_writes_must_appear_in_the_snapshot(bridge, kind):
    bridge.port.snapshot = Mock(return_value={"as_of": AS_OF, "events": [], "edges": []})
    with pytest.raises(EngineIntegrationError):
        bridge.world_snapshot([EVENT] if kind == "events" else [], [EDGE] if kind == "edges" else [])


def test_recall_budget_is_enforced_without_dropping_focus_items(bridge):
    from tradepulse.engines import MAX_FOCUS

    items = [{"symbol": "SYN-A"}] * (MAX_FOCUS + 1)
    enriched = bridge.prior_context(items)
    assert len(enriched) == len(items)
    assert bridge.port.calls.count("recall") == MAX_FOCUS
    assert "memory_context" not in enriched[-1]
    assert any(event["message"] == "Recall work limit reached" for event in bridge.tracer.events())
