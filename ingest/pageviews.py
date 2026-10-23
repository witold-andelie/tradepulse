"""pageview table (task A3). See contracts/tables/pageview.json."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from urllib.parse import quote

import pandas as pd

from ingest._common import concat_tables, report_path, table_frame, user_agent, window_start
from ingest.lake import read_table, write_table
from ingest.net import RateLimiter, build_session, get_with_retries

API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"


def pageviews_url(title: str, start: dt.date, end: dt.date) -> str:
    """{API}/{quoted_title}/daily/{YYYYMMDD}/{YYYYMMDD}.

    quoted_title = urllib.parse.quote(title.replace(" ", "_"), safe="").
    """
    article = quote(title.replace(" ", "_"), safe="")
    return f"{API}/{article}/daily/{start:%Y%m%d}/{end:%Y%m%d}"


def parse_pageviews(payload: dict, pool: str, symbol: str, title: str) -> pd.DataFrame:
    """Convert the API JSON ({"items": [{"timestamp": "YYYYMMDD00", "views": n, ...}]}) into
    pageview rows: date = timestamp day (naive midnight), views int64,
    available_at = date + 1 day at 00:00 UTC. Sorted by date. Empty items -> empty frame with
    the contract columns.
    """
    rows = []
    for item in payload.get("items", []):
        date = pd.to_datetime(item["timestamp"][:8], format="%Y%m%d")
        rows.append(
            {
                "pool": pool,
                "symbol": symbol,
                "wikipedia_title": title,
                "date": date,
                "views": item["views"],
                "available_at": date.tz_localize("UTC") + pd.Timedelta(days=1),
            }
        )
    return table_frame("pageview", rows).sort_values("date").reset_index(drop=True)


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    """Fetch pageviews for every member with a wikipedia_title; log 404 titles to a report."""
    start = window_start(as_of, root)
    universe = read_table("universe_member", root)
    frames, missing = [], []
    limiter = RateLimiter(50)
    with build_session(user_agent("WIKIMEDIA_USER_AGENT", root)) as session:
        for member in universe.itertuples(index=False):
            title = member.wikipedia_title
            reason = None
            if pd.isna(title) or not str(title).strip():
                reason = "missing_title"
            else:
                response = get_with_retries(session, pageviews_url(title, start, as_of), limiter)
                if response.status_code == 404:
                    reason = "http_404"
                else:
                    response.raise_for_status()
                    frame = parse_pageviews(response.json(), member.pool, member.symbol, title)
                    frame = frame[frame["date"].between(pd.Timestamp(start), pd.Timestamp(as_of))]
                    frames.append(frame)
            if reason:
                missing.append(
                    {
                        "pool": member.pool,
                        "symbol": member.symbol,
                        "wikipedia_title": title,
                        "reason": reason,
                    }
                )
    output = concat_tables("pageview", frames)
    write_table(output, "pageview", root, as_of)
    pd.DataFrame(missing, columns=["pool", "symbol", "wikipedia_title", "reason"]).to_csv(
        report_path(root, "pageviews_missing.csv"), index=False
    )
    return output
