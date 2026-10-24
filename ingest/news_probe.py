"""Bounded GDELT history probe; no news factor or shared table is introduced."""

from __future__ import annotations

import datetime as dt
import json
from urllib.parse import urlencode

import pandas as pd

from ingest.common import environment, report
from ingest.net import RateLimiter, build_session, get_with_retries
from tradepulse.contracts import REPO_ROOT


def fetch_news_probe(as_of, selected_symbol=None):
    import time

    existing_report = REPO_ROOT / "data/lake/_reports/gdelt_probe.csv"
    if selected_symbol and existing_report.exists():
        prior = pd.read_csv(existing_report)
        blocked = prior[prior.symbol == selected_symbol]
        if blocked.detail.astype(str).str.contains("429", regex=False).any():
            remaining = max(0, min(300, existing_report.stat().st_mtime + 300 - time.time()))
            if remaining:
                print(f"GDELT cooldown: {remaining:.0f} seconds", flush=True)
            for _ in range(10):
                if remaining <= 0:
                    break
                delay = min(30, remaining)
                time.sleep(delay)
                remaining -= delay
    start = as_of - dt.timedelta(days=365)
    end = as_of - dt.timedelta(days=1)
    cache = REPO_ROOT / "data/cache/gdelt"
    cache.mkdir(parents=True, exist_ok=True)
    rows = []
    queries = {
        "NVDA": "(NVDA OR NVIDIA)",
        "AMD": '(AMD OR "Advanced Micro Devices")',
        "COHR": "(COHR OR Coherent)",
    }
    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        limiter = RateLimiter(0.2)
        selected = [
            (key, value)
            for key, value in queries.items()
            if selected_symbol is None or key == selected_symbol
        ]
        for symbol, query in selected:
            params = {
                "query": query,
                "mode": "timelinetone",
                "format": "json",
                "timelinesmooth": 0,
                "startdatetime": start.strftime("%Y%m%d") + "000000",
                "enddatetime": end.strftime("%Y%m%d") + "235959",
            }
            url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(params)
            row = {
                "symbol": symbol,
                "query_url": url,
                "requested_start": str(start),
                "requested_end": str(end),
                "status": "BLOCKED",
                "rows": 0,
                "first": None,
                "last": None,
                "detail": "",
            }
            try:
                response = get_with_retries(
                    session, url, limiter, attempts=1 if selected_symbol else 3
                )
                row["http_status"] = response.status_code
                (cache / f"{symbol}.response.txt").write_text(response.text, encoding="utf-8")
                if response.status_code != 200:
                    row["detail"] = f"HTTP_{response.status_code}"
                else:
                    try:
                        payload = response.json()
                    except ValueError:
                        row["status"] = "NO"
                        row["detail"] = " ".join(response.text.split())[:400]
                    else:
                        (cache / f"{symbol}.json").write_text(json.dumps(payload), encoding="utf-8")
                        points = [
                            p
                            for series in payload.get("timeline", [])
                            for p in series.get("data", [])
                        ]
                        dates = pd.to_datetime([p["date"][:8] for p in points], format="%Y%m%d")
                        unique = pd.DatetimeIndex(dates).unique().sort_values()
                        if len(unique):
                            row.update(
                                rows=len(unique),
                                first=str(unique.min().date()),
                                last=str(unique.max().date()),
                            )
                            complete = unique.min().date() <= start and unique.max().date() >= end
                            daily = len(unique) == len(points) and all(
                                p["date"][8:] in ("T000000Z", "000000") for p in points
                            )
                            row["status"] = "YES" if complete and daily else "NO"
                            row["detail"] = (
                                "year_spanning_daily_observations_with_explicit_gaps"
                                if complete and daily
                                else "incomplete_or_nondaily_window"
                            )
                        else:
                            row.update(status="NO", detail="no_timeline_points")
            except Exception as exc:  # noqa: BLE001 -- never print transport credentials
                from ingest.net import IngestHTTPError

                row["detail"] = str(exc) if isinstance(exc, IngestHTTPError) else type(exc).__name__
            rows.append(row)
            print(f"GDELT {symbol}: {row['status']}; {row['detail']}", flush=True)
    result = pd.DataFrame(rows)
    existing = REPO_ROOT / "data/lake/_reports/gdelt_probe.csv"
    if len(selected) == 1 and existing.exists():
        prior = pd.read_csv(existing)
        result = pd.concat([prior[~prior.symbol.isin(result.symbol)], result], ignore_index=True)
    report(result, "gdelt_probe.csv")
    return summarize_news_probe(as_of)


def summarize_news_probe(as_of):
    """Distinguish daily observations with gaps from complete calendar-day coverage."""
    path = REPO_ROOT / "data/lake/_reports/gdelt_probe.csv"
    result = pd.read_csv(path)
    start, end = as_of - dt.timedelta(days=365), as_of - dt.timedelta(days=1)
    for index, row in result.iterrows():
        source = REPO_ROOT / "data/cache/gdelt" / f"{row.symbol}.json"
        if not source.exists():
            continue
        payload = json.loads(source.read_text())
        series = payload.get("timeline", [])
        points = next((s.get("data", []) for s in series if s.get("series") == "Average Tone"), [])
        if not points:
            continue
        raw_dates = [p["date"] for p in points]
        dates = pd.to_datetime([date[:8] for date in raw_dates], format="%Y%m%d")
        unique = pd.DatetimeIndex(dates).unique().sort_values()
        daily = len(unique) == len(points) and all(
            date[8:] in ("T000000Z", "000000") for date in raw_dates
        )
        spans = unique.min().date() <= start and unique.max().date() >= end
        result.loc[index, "daily_observations"] = bool(daily)
        result.loc[index, "calendar_day_coverage"] = len(unique) / ((end - start).days + 1)
        result.loc[index, "missing_calendar_days"] = (end - start).days + 1 - len(unique)
        result.loc[index, "status"] = "YES" if daily and spans else "NO"
        result.loc[index, "detail"] = (
            "year_spanning_daily_observations_with_explicit_gaps"
            if daily and spans
            else "window_or_resolution_not_verified"
        )
    report(result, "gdelt_probe.csv")
    return result
