import datetime as dt

import pandas as pd

from ingest.macro import parse_fred_csv
from ingest.pageviews import pageviews_url, parse_pageviews
from tradepulse.contracts import validate_table

API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"


def test_pageviews_url_encodes_title():
    assert pageviews_url("Apple Inc.", dt.date(2025, 10, 1), dt.date(2025, 10, 3)) == (
        f"{API}/Apple_Inc./daily/20251001/20251003")
    assert pageviews_url("Solana (blockchain platform)", dt.date(2025, 1, 1), dt.date(2025, 1, 2)) == (
        f"{API}/Solana_%28blockchain_platform%29/daily/20250101/20250102")


def test_parse_pageviews(fixture_json):
    df = parse_pageviews(fixture_json("pageviews.json"), "us_equity", "AAPL", "Apple_Inc.")
    assert validate_table(df, "pageview") == []
    assert list(df["views"]) == [12034, 11877, 15002]
    assert df["date"].iloc[0] == pd.Timestamp("2025-10-01")
    assert df["available_at"].iloc[0] == pd.Timestamp("2025-10-02", tz="UTC")


def test_parse_pageviews_empty():
    df = parse_pageviews({"items": []}, "crypto", "BTC-USD", "Bitcoin")
    assert df.empty
    assert "available_at" in df.columns


def test_parse_fred_csv_both_headers():
    for header in ("DATE", "observation_date"):
        text = f"{header},BAMLH0A0HYM2\n2025-10-01,2.95\n2025-10-02,.\n2025-10-03,3.01\n"
        df = parse_fred_csv(text, "BAMLH0A0HYM2")
        assert validate_table(df, "macro_point") == []
        assert list(df["value"]) == [2.95, 3.01]
        assert df["available_at"].iloc[-1] == pd.Timestamp("2025-10-04", tz="UTC")
