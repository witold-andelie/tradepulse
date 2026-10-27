"""SYNTHETIC transport receipts; no real sponsor operations or model calls."""

import pytest
import requests

from integrations.meterless.engines_client import EnginesClient, EnginesError


def event(index):
    return {"event_id": f"synthetic-{index}", "doc_sha256": "0" * 64,
            "accession_number": "SYNTHETIC", "symbol": "SYNTHETIC", "event_type": "other",
            "direction": 0, "counterparty": None, "counterparty_symbol": None,
            "magnitude_usd": None, "novelty": "new", "demand_signals": [],
            "quote": "SYNTHETIC test", "available_at": "2026-10-23T00:00:00Z",
            "extractor_model": "SYNTHETIC", "schema_version": "1.0"}


def reply(body):
    return type("Response", (), {"status_code": 200, "json": lambda _: body})()


def test_world_events_use_write_budget_and_acknowledge_existing_events(monkeypatch):
    monkeypatch.setenv("ENGINES_WRITE_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("ENGINES_WORLD_BATCH_SIZE", "50")
    calls, diagnostics = [], []

    class Session:
        def post(self, _url, *, json, timeout):
            calls.append((json["events"], timeout))
            return reply({"ingested": 0, "duplicates": len(json["events"])})

    client = EnginesClient("http://localhost:8790", timeout_s=10, session=Session())
    client.observer = diagnostics.append
    assert client.ingest_events([event(i) for i in range(732)]) == {"ingested": 0, "duplicates": 732}
    assert [len(batch) for batch, _ in calls] == [50] * 14 + [32]
    assert all(timeout == 60 for _, timeout in calls)
    assert len({item["event_id"] for batch, _ in calls for item in batch}) == 732
    assert diagnostics[-1]["batch_items"] == 32


def test_world_edges_and_snapshot_have_explicit_budgets(monkeypatch):
    monkeypatch.setenv("ENGINES_WRITE_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("ENGINES_READ_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("ENGINES_WORLD_BATCH_SIZE", "1")
    calls = []

    class Session:
        def post(self, _url, *, json, timeout):
            calls.append(("write", timeout))
            return reply({"upserted": len(json["edges"])})

        def get(self, _url, *, params, timeout):
            calls.append(("read", timeout))
            return reply({"as_of": params["as_of"], "events": [], "edges": []})

    edge = {"edge_id": "synthetic", "src_symbol": "SYNTHETIC-A", "dst_symbol": "SYNTHETIC-B",
            "relation": "peer", "weight": 0.0, "source": "seed", "evidence_ref": None,
            "status": "validated", "lead_lag_t": None, "valid_from": "2026-10-23"}
    client = EnginesClient("http://localhost:8790", timeout_s=10, session=Session())
    assert client.upsert_edges([edge, {**edge, "edge_id": "synthetic-2"}]) == {"upserted": 2}
    client.snapshot("2026-10-23")
    assert calls == [("write", 60), ("write", 60), ("read", 60)]


def test_world_timeout_stops_batches_without_automatic_retry(monkeypatch):
    monkeypatch.setenv("ENGINES_WORLD_BATCH_SIZE", "1")
    calls = []

    class Session:
        def post(self, *_args, **_kwargs):
            calls.append(1)
            if len(calls) == 2:
                raise requests.ReadTimeout("SYNTHETIC private detail")
            return reply({"ingested": 1, "duplicates": 0})

    with pytest.raises(EnginesError) as caught:
        EnginesClient("http://localhost:8790", session=Session()).ingest_events([event(i) for i in range(3)])
    assert caught.value.error_type == "ReadTimeout"
    assert len(calls) == 2


def test_world_batch_rejects_partial_acknowledgement():
    class Session:
        def post(self, *_args, **_kwargs):
            return reply({"ingested": 0, "duplicates": 0})

    with pytest.raises(EnginesError):
        EnginesClient("http://localhost:8790", session=Session()).ingest_events([event(1)])
