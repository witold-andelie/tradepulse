"""End-to-end through the real DuckDBAdapter over a contract-valid synthetic parquet lake."""

import numpy as np
import pandas as pd
import pytest

from integrations.zetaris.adapter import DuckDBAdapter
from tradepulse.contracts import table_path, validate_payload, validate_table
from tradepulse.pipeline import run_pipeline
from tradepulse.tests.test_pipeline import AS_OF, ScriptedLLM, _lake

NOW = pd.Timestamp("2026-10-21 22:00", tz="UTC")


def _write(root, name, df):
    assert validate_table(df, name) == [], (name, validate_table(df, name))
    path = table_path(name, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


@pytest.fixture(scope="module")
def lake_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("lake")
    bars, views, members, macro = _lake()
    px = bars["adj_close"].astype(float)
    _write(root, "price_bar", pd.DataFrame({
        "pool": bars["pool"], "symbol": bars["symbol"], "date": pd.to_datetime(bars["date"]),
        "open": px, "high": px * 1.01, "low": px * 0.99, "close": px, "adj_close": px,
        "volume": bars["volume"].astype(float), "currency": "USD", "source": "yahoo", "ingested_at": NOW,
    }).reset_index(drop=True))
    _write(root, "universe_member", pd.DataFrame({
        "pool": members["pool"], "symbol": members["symbol"], "name": members["name"], "sector": members["sector"],
        "country": None, "currency": "USD", "cik": None, "wikipedia_title": None,
        "index_membership": "SYNTHETIC", "snapshot_date": AS_OF,
    }))
    _write(root, "pageview", pd.DataFrame({
        "pool": views["pool"], "symbol": views["symbol"], "wikipedia_title": "Synthetic",
        "date": pd.to_datetime(views["date"]), "views": views["views"].astype("int64"),
        "available_at": (pd.to_datetime(views["date"]) + pd.Timedelta(days=1)).dt.tz_localize("UTC"),
    }).reset_index(drop=True))
    _write(root, "macro_point", pd.DataFrame({
        "series_id": macro["series_id"], "date": pd.to_datetime(macro["date"]), "value": macro["value"].astype(float),
        "source": "fred", "available_at": (pd.to_datetime(macro["date"]) + pd.Timedelta(days=1)).dt.tz_localize("UTC"),
    }))
    _write(root, "filing", pd.DataFrame({
        "cik": ["0000000001"], "symbol": ["U01"], "accession_number": ["0000000001-26-000001"], "form": ["8-K"],
        "items": ["2.02"], "filing_date": [pd.Timestamp("2026-10-15")],
        "acceptance_datetime": [pd.Timestamp("2026-10-15 20:05", tz="UTC")], "report_date": [pd.NaT],
        "primary_document": ["x.htm"], "primary_doc_url": ["https://www.sec.gov/Archives/x.htm"],
    }))
    return root


def test_pipeline_runs_on_duckdb(lake_root, tmp_path):
    adapter = DuckDBAdapter(lake_root)
    request = {"as_of": "2026-10-21", "pools": ["us_equity", "crypto"], "tickers": [], "horizon_days": 5, "top_k": 2}
    out = run_pipeline(request, query=adapter, llm=ScriptedLLM(), log_dir=tmp_path)
    assert validate_payload(out, "RunOutput") == []
    assert len([r for r in out["recommendations"] if r["pool"] == "crypto"]) == 22
    assert out["explanations"] and all(e["verdict"] == "explained" for e in out["explanations"])
    # every verified claim was re-run by the verifier through DuckDB with an identical hash
    checks = [c for e in out["explanations"] for cl in e["claims"] for c in cl["checks"]]
    assert any(c["name"] == "rerun_hash_match" and c["passed"] for c in checks)
    assert np.isfinite([r["score"] for r in out["recommendations"]]).all()
