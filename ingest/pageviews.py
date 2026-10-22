"""pageview table (task A3). See contracts/tables/pageview.json."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"


def pageviews_url(title: str, start: dt.date, end: dt.date) -> str:
    """{API}/{quoted_title}/daily/{YYYYMMDD}/{YYYYMMDD}.

    quoted_title = urllib.parse.quote(title.replace(" ", "_"), safe="").
    """
    raise NotImplementedError("A3")


def parse_pageviews(payload: dict, pool: str, symbol: str, title: str) -> pd.DataFrame:
    """Convert the API JSON ({"items": [{"timestamp": "YYYYMMDD00", "views": n, ...}]}) into
    pageview rows: date = timestamp day (naive midnight), views int64,
    available_at = date + 1 day at 00:00 UTC. Sorted by date. Empty items -> empty frame with
    the contract columns.
    """
    raise NotImplementedError("A3")


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    """Fetch pageviews for every member with a wikipedia_title; log 404 titles to a report."""
    raise NotImplementedError("A3")
