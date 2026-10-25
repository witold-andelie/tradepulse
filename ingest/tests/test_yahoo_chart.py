"""SYNTHETIC offline checks for the explicitly selected Yahoo chart transport."""

import datetime as dt

import pandas as pd
import pytest
import requests

from ingest import prices, yahoo_chart


def payload():
    return {
        "chart": {
            "error": None,
            "result": [
                {
                    "meta": {"exchangeTimezoneName": "America/New_York"},
                    "timestamp": [int(pd.Timestamp("2025-10-02 00:30Z").timestamp())],
                    "indicators": {
                        "quote": [
                            {"open": [10.0], "high": [12.0], "low": [9.0],
                             "close": [11.0], "volume": [100.0]}
                        ],
                        "adjclose": [{"adjclose": [10.5]}],
                    },
                }
            ],
        }
    }


def test_chart_preserves_adjustment_and_exchange_session_date():
    raw = yahoo_chart.parse_chart(payload(), "SYNTHETIC")
    assert raw.date.iloc[0] == pd.Timestamp("2025-10-01")
    assert raw.Close.iloc[0] == 11.0
    assert raw["Adj Close"].iloc[0] == 10.5
    assert list(raw.columns) == prices.RAW_COLUMNS


@pytest.mark.parametrize("missing", ["adjclose", "timezone", "array_length"])
def test_chart_rejects_incomplete_provider_measurements(missing):
    source = payload()
    item = source["chart"]["result"][0]
    if missing == "adjclose":
        item["indicators"].pop("adjclose")
    elif missing == "timezone":
        item["meta"].clear()
    else:
        item["indicators"]["quote"][0]["close"] = []
    with pytest.raises(ValueError):
        yahoo_chart.parse_chart(source, "SYNTHETIC")


def test_public_transport_caches_source_and_filters_dates(tmp_path, monkeypatch):
    requests_made = []

    class Response:
        status_code = 200

        def json(self):
            return payload()

    def fetch(session, url, limiter):
        requests_made.append(url)
        return Response()

    monkeypatch.setattr(yahoo_chart, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(yahoo_chart, "environment", lambda _: "SYNTHETIC")
    monkeypatch.setattr(yahoo_chart, "build_session", lambda _: requests.Session())
    monkeypatch.setattr(yahoo_chart, "get_with_retries", fetch)
    monkeypatch.setenv("YAHOO_TRANSPORT", "public_chart")
    first = prices.fetch_prices(["SYNTHETIC", "SYNTHETIC"], dt.date(2025, 10, 1), dt.date(2025, 10, 1))
    second = prices.fetch_prices(["SYNTHETIC"], dt.date(2025, 10, 1), dt.date(2025, 10, 1))
    assert len(requests_made) == 1
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 1
    assert "period2=1759363200" in requests_made[0]
