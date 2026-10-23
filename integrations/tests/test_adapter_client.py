import numpy as np
import pandas as pd
import pytest

from integrations.zetaris.adapter import DuckDBAdapter, rows_sha256
from integrations.zetaris.client import coerce_frame, ensure_single_statement
from tradepulse.contracts import table_path, validate_table


def test_rows_sha256_ignores_order_and_dtype():
    a = pd.DataFrame({"symbol": ["AAA", "BBB"], "date": pd.to_datetime(["2025-01-02", "2025-01-03"]),
                      "close": [1.5, 150.0], "volume": [np.nan, 10.0]})
    b = pd.DataFrame({"SYMBOL": ["BBB", "AAA"], "DATE": ["2025-01-03", "2025-01-02"],
                      "CLOSE": ["1.5E+2", "1.50"], "VOLUME": ["10", None]})
    b["DATE"] = pd.to_datetime(b["DATE"]).dt.date
    assert rows_sha256(a) == rows_sha256(b)
    c = a.copy()
    c.loc[0, "close"] = 1.6
    assert rows_sha256(c) != rows_sha256(a)
    assert len(rows_sha256(a)) == 64


def _write_lake(root):
    now = pd.Timestamp("2026-10-21 22:00", tz="UTC")
    bars = pd.DataFrame({
        "pool": ["us_equity"] * 4, "symbol": ["AAA", "AAA", "BBB", "BBB"],
        "date": pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-02", "2025-01-03"]),
        "open": [1.0, 1.1, 2.0, 2.1], "high": [1.2, 1.2, 2.2, 2.2], "low": [0.9, 1.0, 1.9, 2.0],
        "close": [1.1, 1.15, 2.1, 2.05], "adj_close": [1.1, 1.15, 2.1, 2.05], "volume": [100.0, 120.0, 50.0, 55.0],
        "currency": "USD", "source": "yahoo", "ingested_at": now,
    })
    assert validate_table(bars, "price_bar") == []
    path = table_path("price_bar", root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    bars.to_parquet(path, index=False)
    return bars


def test_duckdb_adapter_runs_templates(tmp_path):
    _write_lake(tmp_path)
    adapter = DuckDBAdapter(tmp_path)
    res = adapter.run("price_symbol_window", {"symbol": "AAA", "start": "2025-01-01", "end": "2025-01-31"})
    assert res.backend == "duckdb"
    assert list(res.df["close"]) == pytest.approx([1.1, 1.15])
    assert res.rows_sha256 == rows_sha256(res.df)
    assert res.template == "price_symbol_window" and "SELECT" in res.sql.upper()
    again = adapter.run("price_symbol_window", {"symbol": "AAA", "start": "2025-01-01", "end": "2025-01-31"})
    assert again.rows_sha256 == res.rows_sha256  # the verifier relies on this
    multi = adapter.run("price_symbols_window", {"symbols": ["AAA", "BBB"], "start": "2025-01-03", "end": "2025-01-03"})
    assert sorted(multi.df["symbol"]) == ["AAA", "BBB"]


def test_ensure_single_statement():
    assert ensure_single_statement("  SELECT 1;  ") == "SELECT 1"
    assert ensure_single_statement("SELECT ';' AS x") == "SELECT ';' AS x"
    with pytest.raises(ValueError):
        ensure_single_statement("SELECT 1; DROP TABLE t")


def test_coerce_frame():
    raw = pd.DataFrame({"close": ["1.5E+2", "", "3"], "date": ["2025-01-02", "2025-01-03", "null"],
                        "ts": ["2025-01-02T21:00:00Z", None, "2025-01-03 21:00:00"], "name": ["a", "b", "c"]})
    out = coerce_frame(raw, {"close": "float", "date": "date", "ts": "datetime"})
    assert out["close"].iloc[0] == pytest.approx(150.0) and np.isnan(out["close"].iloc[1])
    assert out["date"].iloc[0] == pd.Timestamp("2025-01-02") and pd.isna(out["date"].iloc[2])
    assert str(out["ts"].dt.tz) == "UTC" and pd.isna(out["ts"].iloc[1])
    assert list(out["name"]) == ["a", "b", "c"]


def test_duckdb_adapter_is_thread_safe(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    _write_lake(tmp_path)
    adapter = DuckDBAdapter(tmp_path)
    params = {"symbol": "AAA", "start": "2025-01-01", "end": "2025-01-31"}
    expected = adapter.run("price_symbol_window", params).rows_sha256
    with ThreadPoolExecutor(max_workers=8) as pool:
        hashes = list(pool.map(lambda _: adapter.run("price_symbol_window", dict(params)).rows_sha256, range(200)))
    assert set(hashes) == {expected}
