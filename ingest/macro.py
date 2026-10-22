"""macro_point table (task A6). See contracts/tables/macro_point.json."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"


def parse_fred_csv(text: str, series_id: str) -> pd.DataFrame:
    """Parse a FRED CSV download into macro_point rows.

    Header is either 'DATE,<series_id>' or 'observation_date,<series_id>'. Rows whose value is '.'
    are dropped. source = 'fred'; available_at = date + 1 day at 00:00 UTC. Sorted by date.
    """
    raise NotImplementedError("A6")


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    """Download BAMLH0A0HYM2, keep dates <= as_of, write macro_point."""
    raise NotImplementedError("A6")
