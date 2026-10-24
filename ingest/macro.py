"""FRED observations; downloaded vintages retain revision risk."""

from __future__ import annotations

import datetime as dt
from io import StringIO
from pathlib import Path

import pandas as pd

from ingest.common import before_cutoff, environment, frame, window_start
from ingest.lake import write_table
from ingest.net import RateLimiter, build_session, fetch_response

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"


def parse_fred_csv(text: str, series_id: str) -> pd.DataFrame:
    raw = pd.read_csv(StringIO(text), na_values=["."])
    date_col = "DATE" if "DATE" in raw else "observation_date"
    raw = raw.dropna(subset=[series_id])
    dates = pd.to_datetime(raw[date_col])
    return (
        frame(
            pd.DataFrame(
                {
                    "series_id": series_id,
                    "date": dates,
                    "value": pd.to_numeric(raw[series_id]),
                    "source": "fred",
                    "available_at": dates.dt.tz_localize("UTC") + pd.Timedelta(days=1),
                }
            ).to_dict("records"),
            "macro_point",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )


def fetch_macro(series_id):
    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        return fetch_response(session, FRED_CSV.format(series_id=series_id), RateLimiter(2)).text


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    result = before_cutoff(
        parse_fred_csv(fetch_macro("BAMLH0A0HYM2"), "BAMLH0A0HYM2"), "macro_point", as_of
    )
    result = result[result.date >= pd.Timestamp(window_start(as_of))]
    write_table(result, "macro_point", root, as_of)
    return result
