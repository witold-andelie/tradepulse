import numpy as np
import pandas as pd
import pytest

from ingest.lake import read_table, write_table
from ingest.prices import coverage_report, to_price_bars
from tradepulse.contracts import ContractError, validate_table

NOW = pd.Timestamp("2026-10-21 22:00", tz="UTC")


def _raw():
    return pd.DataFrame({
        "symbol": ["AAA", "AAA", "AAA", "^VIX"],
        "date": pd.to_datetime(["2026-10-19", "2026-10-20", "2026-10-21", "2026-10-21"]),
        "Open": [10.0, 10.5, 10.4, 20.0], "High": [11.0, 10.9, 10.8, 21.0],
        "Low": [9.8, 10.1, 10.0, 19.0], "Close": [10.5, np.nan, 10.6, 20.5],
        "Adj Close": [10.4, np.nan, 10.5, 20.5], "Volume": [1000, 1200, 900, 0],
    })


def test_to_price_bars_drops_missing_and_validates():
    out = to_price_bars(_raw()[_raw()["symbol"] == "AAA"], "us_equity", {"AAA": "USD"}, NOW)
    assert validate_table(out, "price_bar") == []
    assert len(out) == 2  # the NaN close row is dropped, never filled
    assert list(out["adj_close"]) == [10.4, 10.5]


def test_reference_zero_volume_becomes_null():
    out = to_price_bars(_raw()[_raw()["symbol"] == "^VIX"], "reference", {"^VIX": "USD"}, NOW)
    assert validate_table(out, "price_bar") == []
    assert out["volume"].isna().all()


def test_coverage_report_ignores_dates_before_listing():
    cal = pd.DatetimeIndex(pd.to_datetime(["2026-10-15", "2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21"]))
    bars = pd.DataFrame({
        "pool": ["us_equity"] * 5,
        "symbol": ["OLD", "OLD", "OLD", "NEW", "NEW"],
        "date": pd.to_datetime(["2026-10-15", "2026-10-16", "2026-10-21", "2026-10-20", "2026-10-21"]),
    })
    rep = coverage_report(bars, cal).set_index("symbol")
    assert rep.loc["NEW", "coverage"] == pytest.approx(1.0)
    assert rep.loc["OLD", "coverage"] == pytest.approx(3 / 5)
    assert rep.loc["OLD", "rows"] == 3
    assert rep.index[0] == "OLD"  # sorted by coverage ascending


def test_write_and_read_roundtrip(tmp_path):
    bars = to_price_bars(_raw()[_raw()["symbol"] == "AAA"], "us_equity", {"AAA": "USD"}, NOW)
    path = write_table(bars, "price_bar", root=tmp_path)
    assert path.exists()
    back = read_table("price_bar", root=tmp_path)
    assert validate_table(back, "price_bar") == []
    assert len(back) == 2


def test_write_refuses_invalid_data(tmp_path):
    bad = pd.DataFrame({"pool": ["us_equity"], "symbol": ["AAA"]})
    with pytest.raises(ContractError):
        write_table(bad, "price_bar", root=tmp_path)
    assert not list(tmp_path.rglob("*.parquet"))
