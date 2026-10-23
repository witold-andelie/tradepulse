"""macro_point table (task A6). See contracts/tables/macro_point.json."""

from __future__ import annotations

import datetime as dt
from io import StringIO
from pathlib import Path

import pandas as pd

from ingest._common import table_frame, user_agent
from ingest.lake import write_table
from ingest.net import RateLimiter, build_session, get_with_retries

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"


def parse_fred_csv(text: str, series_id: str) -> pd.DataFrame:
    """Parse a FRED CSV download into macro_point rows.

    Header is either 'DATE,<series_id>' or 'observation_date,<series_id>'. Rows whose value is '.'
    are dropped. source = 'fred'; available_at = date + 1 day at 00:00 UTC. Sorted by date.
    """
    frame = pd.read_csv(StringIO(text), dtype="string")
    header = "DATE" if "DATE" in frame else "observation_date"
    frame = frame[frame[series_id].notna() & frame[series_id].ne(".")].copy()
    frame["date"] = pd.to_datetime(frame[header])
    frame["value"] = pd.to_numeric(frame[series_id])
    frame["available_at"] = frame["date"].dt.tz_localize("UTC") + pd.Timedelta(days=1)
    frame = frame.assign(series_id=series_id, source="fred")
    return table_frame("macro_point", frame).sort_values("date").reset_index(drop=True)


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    """Download BAMLH0A0HYM2, keep dates <= as_of, write macro_point."""
    series = "BAMLH0A0HYM2"
    with build_session(user_agent("WIKIMEDIA_USER_AGENT", root)) as session:
        response = get_with_retries(session, FRED_CSV.format(series_id=series), RateLimiter(2))
        response.raise_for_status()
        output = parse_fred_csv(response.text, series)
    output = output[output["date"] <= pd.Timestamp(as_of)].reset_index(drop=True)
    write_table(output, "macro_point", root, as_of)
    return output
