"""Daily pageviews with explicit next-day availability."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from urllib.parse import quote

import pandas as pd

from ingest.common import before_cutoff, environment, frame, report, window_start
from ingest.lake import read_table, write_table
from ingest.net import IngestHTTPError, RateLimiter, build_session, get_with_retries

API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"


def pageviews_url(title: str, start: dt.date, end: dt.date) -> str:
    return f"{API}/{quote(title.replace(' ', '_'), safe='')}/daily/{start:%Y%m%d}/{end:%Y%m%d}"


def parse_pageviews(payload: dict, pool: str, symbol: str, title: str) -> pd.DataFrame:
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
    return frame(rows, "pageview").sort_values("date").reset_index(drop=True)


def fetch_pageviews(session, limiter, title, start, end):
    import hashlib
    import json

    from tradepulse.contracts import REPO_ROOT

    if end < start:
        raise ValueError("Pageview date range is reversed")
    items = []
    cache_root = REPO_ROOT / "data/cache/pageviews"
    legacy_urls = [
        pageviews_url(
            title,
            start + dt.timedelta(days=offset),
            min(end, start + dt.timedelta(days=offset + 364)),
        )
        for offset in range(0, (end - start).days + 1, 365)
    ]
    has_legacy = any(
        (cache_root / (hashlib.sha256(url.encode()).hexdigest() + ".json")).exists()
        for url in legacy_urls
    )
    chunk_days = 365 if has_legacy else 1000
    for offset in range(0, (end - start).days + 1, chunk_days):
        first = start + dt.timedelta(days=offset)
        last = min(end, first + dt.timedelta(days=chunk_days - 1))
        url = pageviews_url(title, first, last)
        cache = (
            REPO_ROOT
            / "data/cache/pageviews"
            / (hashlib.sha256(url.encode()).hexdigest() + ".json")
        )
        if cache.exists():
            payload = json.loads(cache.read_text())
        else:
            response = get_with_retries(session, url, limiter)
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise IngestHTTPError(
                    f"Wikimedia returned HTTP {response.status_code}", response.status_code
                )
            payload = response.json()
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(payload), encoding="utf-8")
        items.extend(payload.get("items", []))
    return {"items": items}


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    members = read_table("universe_member", root)
    frames, missing, cache = [], [], {}
    from concurrent.futures import ThreadPoolExecutor

    user_agent = environment("WIKIMEDIA_USER_AGENT")
    limiter = RateLimiter(1)
    failures = {}
    import time

    from tradepulse.contracts import REPO_ROOT

    failure_path = Path(root or REPO_ROOT) / "data/lake/_reports/pageviews_request_failures.csv"
    if failure_path.exists():
        previous = pd.read_csv(failure_path)
        if previous.reason.eq("HTTP_429").any():
            remaining = max(0, failure_path.stat().st_mtime + 300 - time.time())
            if remaining:
                print(
                    f"Wikimedia cooldown: {remaining:.0f} seconds; cached results retained",
                    flush=True,
                )
            for _ in range(10):
                if remaining <= 0:
                    break
                delay = min(30, remaining)
                time.sleep(delay)
                remaining -= delay
    titles = members.wikipedia_title.dropna().unique().tolist()

    def collect(title):
        with build_session(user_agent) as session:
            try:
                return title, fetch_pageviews(session, limiter, title, window_start(as_of), as_of)
            except IngestHTTPError as exc:
                failures[title] = f"HTTP_{exc.status_code}" if exc.status_code else "request_failed"
                if exc.status_code in (403, 429) or len(failures) >= 10:
                    report(
                        pd.DataFrame(
                            [{"title": key, "reason": value} for key, value in failures.items()]
                        ),
                        "pageviews_request_failures.csv",
                        root,
                    )
                    raise
                return title, None

    with ThreadPoolExecutor(max_workers=2) as executor:
        for number, (title, payload) in enumerate(executor.map(collect, titles), 1):
            cache[title] = payload
            if number % 50 == 0 or number == len(titles):
                print(f"Wikimedia articles {number}/{len(titles)}", flush=True)
    for row in members.itertuples():
        title = row.wikipedia_title
        if pd.isna(title):
            missing.append(
                {"pool": row.pool, "symbol": row.symbol, "title": None, "reason": "missing_title"}
            )
            continue
        payload = cache[title]
        if payload is None:
            missing.append(
                {
                    "pool": row.pool,
                    "symbol": row.symbol,
                    "title": title,
                    "reason": failures.get(title, "HTTP_404"),
                }
            )
            continue
        frames.append(parse_pageviews(payload, row.pool, row.symbol, title))
    result = frame(pd.concat(frames).to_dict("records") if frames else [], "pageview")
    result = before_cutoff(result, "pageview", as_of)
    result = result[result.date >= pd.Timestamp(window_start(as_of))]
    report(
        pd.DataFrame(missing, columns=["pool", "symbol", "title", "reason"]),
        "pageviews_missing.csv",
        root,
    )
    write_table(result, "pageview", root, as_of)
    return result
