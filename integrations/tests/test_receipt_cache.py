"""SYNTHETIC receipts test cache integrity and live evidence routing, not sponsor acceptance."""

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from integrations.zetaris import receipt_cache as module
from integrations.zetaris.adapter import QueryResult, rows_sha256


def result(template, params):
    frame = pd.DataFrame({"value": [1, 2]})
    return QueryResult(template, params, "SYNTHETIC", "duckdb", frame, rows_sha256(frame), 0)


def test_only_hash_matched_bulk_results_are_cached(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    path = tmp_path / "runs/queries.jsonl"
    path.parent.mkdir()
    params = {"pool": "us_equity", "start": "2026-01-01", "end": "2026-10-23"}
    expected = result("price_pool_window", params)
    path.write_text(json.dumps({"backend": "zetaris", "template": expected.template,
        "params": params, "rows": 2, "rows_sha256": expected.rows_sha256}) + "\n", encoding="utf-8")
    live_calls = []
    live = SimpleNamespace(run=lambda t, p: live_calls.append(t) or result(t, p))
    offline = SimpleNamespace(run=result)
    cache = module.ReceiptCache(live, offline, path)
    assert cache.run(expected.template, params).backend == "zetaris-verified-local-cache"
    cache.run("price_symbol_window", {"symbol": "SYNTHETIC"})
    assert live_calls == ["price_symbol_window"]
    assert cache.hits == 1


def test_cache_mismatch_fails_without_silent_live_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    path = tmp_path / "runs/queries.jsonl"
    path.parent.mkdir()
    path.write_text(json.dumps({"backend": "zetaris", "template": "facts_tag_window",
        "params": {}, "rows": 999, "rows_sha256": "0" * 64}) + "\n", encoding="utf-8")
    live = SimpleNamespace(run=lambda *_: pytest.fail("No silent fallback after an integrity error"))
    cache = module.ReceiptCache(live, SimpleNamespace(run=result), path)
    with pytest.raises(ValueError, match="prior Zetaris receipt"):
        cache.run("facts_tag_window", {})
    assert cache.integrity_failed


def test_prior_parity_is_rechecked_against_current_local_data(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "list_templates", lambda: ["price_symbol_window"])
    monkeypatch.setattr(module, "fixed_params", lambda *_: {"symbol": "SYNTHETIC"})
    expected = result("price_symbol_window", {"symbol": "SYNTHETIC"})
    cases = [{"template": expected.template, "params": expected.params, "match": True,
              "duckdb_rows": 2, "zetaris_rows": 2, "duckdb_sha256": expected.rows_sha256,
              "zetaris_sha256": expected.rows_sha256}]
    path = tmp_path / "runs/parity.json"
    path.parent.mkdir()
    path.write_text(json.dumps(cases), encoding="utf-8")
    assert module.verified_parity(path, SimpleNamespace(run=result), "2026-10-23") == cases
    cases[0]["zetaris_sha256"] = "0" * 64
    path.write_text(json.dumps(cases), encoding="utf-8")
    with pytest.raises(ValueError, match="current frozen sample"):
        module.verified_parity(path, SimpleNamespace(run=result), "2026-10-23")
