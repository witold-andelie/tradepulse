"""Daily Yahoo bars and explicit per-member coverage reports."""

from __future__ import annotations

import datetime as dt
import time
from pathlib import Path

import pandas as pd

from ingest.common import environment, frame, report, window_start
from ingest.lake import read_table, write_table
from ingest.net import RETRY_STATUSES, IngestHTTPError, RateLimiter, build_session
from tradepulse.contracts import REPO_ROOT

REFERENCE_SYMBOLS = ("SPY", "^VIX", "^VIX3M", "^STOXX50E", "BTC-USD")
RAW_COLUMNS = ["symbol", "date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]


def to_price_bars(
    raw: pd.DataFrame, pool: str, currency_by_symbol: dict[str, str], ingested_at: pd.Timestamp
) -> pd.DataFrame:
    out = raw.dropna(subset=["Close", "Adj Close"]).copy()
    out = out.rename(columns={k: k.lower().replace(" ", "_") for k in RAW_COLUMNS})
    out["date"] = out["date"].map(lambda v: pd.Timestamp(v).tz_localize(None).normalize())
    out["pool"], out["currency"], out["source"], out["ingested_at"] = (
        pool,
        out.symbol.map(currency_by_symbol),
        "yahoo",
        ingested_at,
    )
    if pool == "reference":
        out["volume"] = out["volume"].replace(0, float("nan"))
    return (
        frame(out.to_dict("records"), "price_bar")
        .sort_values(["symbol", "date"])
        .reset_index(drop=True)
    )


def coverage_report(bars: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    calendar = pd.DatetimeIndex(calendar).normalize().unique().sort_values()
    result = []
    for (pool, symbol), group in bars.groupby(["pool", "symbol"]):
        dates = pd.DatetimeIndex(group.date).normalize().unique()
        first, last = dates.min(), dates.max()
        expected = calendar[calendar >= first]
        result.append(
            {
                "pool": pool,
                "symbol": symbol,
                "rows": len(group),
                "first_date": first,
                "last_date": last,
                "coverage": len(expected.intersection(dates)) / len(expected)
                if len(expected)
                else 0.0,
            }
        )
    return (
        pd.DataFrame(
            result, columns=["pool", "symbol", "rows", "first_date", "last_date", "coverage"]
        )
        .sort_values("coverage", kind="stable")
        .reset_index(drop=True)
    )


def _yahoo_session():
    """Use the shared Session policy, including yfinance's GET and POST requests.

    Verified offline against yfinance 1.7.0, which accepts requests.Session.
    Versions requiring only curl_cffi must fail rather than bypass this transport.
    """
    import requests

    session = build_session(environment("WIKIMEDIA_USER_AGENT"))
    original_request = session.request
    limiter = RateLimiter(2)
    session.limiter = limiter

    def request(method, url, **kwargs):
        kwargs["timeout"] = 30
        last = None
        response = None
        for attempt in range(3):
            try:
                response = original_request(method, url, **kwargs)
                last = response.status_code
                if response.status_code not in RETRY_STATUSES:
                    return response
            except (requests.Timeout, requests.ConnectionError) as exc:
                last = type(exc).__name__
            if attempt < 2:
                time.sleep(2**attempt)
        if response is not None:
            # yfinance interprets cookie/crumb endpoint status itself; preserve the response
            # so its supported unauthenticated chart path can decide whether a crumb is needed.
            return response
        raise IngestHTTPError(
            f"Yahoo request failed after 3 attempts: {last}",
            last if isinstance(last, int) else None,
        ) from None

    session.request = request
    session.max_redirects = 5
    return session


def fetch_prices(symbols: list[str], start: dt.date, end: dt.date) -> pd.DataFrame:
    import yfinance as yf

    cache = REPO_ROOT / "data/cache/yfinance"
    cache.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(cache))

    if end < start:
        raise ValueError("Price window is reversed")
    symbols = list(dict.fromkeys(symbols))
    parts = []
    network = getattr(getattr(yf, "config", None), "network", None)
    old_retries = getattr(network, "retries", None)
    if old_retries is not None:
        network.retries = 0
    try:
        with _yahoo_session() as session:
            for offset in range(0, len(symbols), 50):
                batch = symbols[offset : offset + 50]
                print(
                    f"Yahoo batch {offset // 50 + 1}/{(len(symbols) + 49) // 50}: {len(batch)} symbols",
                    flush=True,
                )
                raw = yf.download(
                    batch,
                    start=start.isoformat(),
                    end=(end + dt.timedelta(days=1)).isoformat(),
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                    timeout=30,
                    group_by="ticker",
                    session=session,
                )
                for symbol in batch:
                    if isinstance(raw.columns, pd.MultiIndex):
                        if symbol not in raw.columns.get_level_values(0):
                            continue
                        one = raw[symbol].copy()
                    else:
                        one = raw.copy()
                    if one.empty:
                        continue
                    one["date"] = one.index
                    one["symbol"] = symbol
                    parts.append(one.reset_index(drop=True).reindex(columns=RAW_COLUMNS))
                if offset + 50 < len(symbols):
                    time.sleep(1)
    finally:
        if old_retries is not None:
            network.retries = old_retries
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=RAW_COLUMNS)


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    members = read_table("universe_member", root)
    reference = pd.DataFrame(
        {
            "symbol": REFERENCE_SYMBOLS,
            "pool": "reference",
            "currency": ["USD", "USD", "USD", "EUR", "USD"],
        }
    )
    requested = pd.concat([members[["pool", "symbol", "currency"]], reference], ignore_index=True)
    raw = fetch_prices(requested.symbol.unique().tolist(), window_start(as_of), as_of)
    parts = []
    now = pd.Timestamp.now(tz="UTC")
    for pool, group in requested.groupby("pool"):
        parts.append(
            to_price_bars(
                raw[raw.symbol.isin(group.symbol)],
                pool,
                dict(zip(group.symbol, group.currency)),
                now,
            )
        )
    result = frame(pd.concat(parts).to_dict("records"), "price_bar")
    result = result[result.date.between(pd.Timestamp(window_start(as_of)), pd.Timestamp(as_of))]
    write_coverage(result, requested, as_of, root)
    write_table(result, "price_bar", root, as_of)
    return result


def requested_coverage(result, requested, as_of):
    """Compute coverage from current bars, including requested symbols with no observations.

    References use their own market calendar, never a crypto union. This calculation is
    shared by collection reports and acceptance audits so a stale CSV cannot certify new bars.
    """
    reports = []
    benchmarks = {"us_equity": "SPY", "eu_equity": "^STOXX50E", "crypto": "BTC-USD"}
    for pool, group in requested.groupby("pool"):
        if pool == "crypto":
            calendar = pd.date_range(window_start(as_of), as_of)
        elif pool in benchmarks:
            calendar = pd.DatetimeIndex(
                result.loc[
                    (result.pool == "reference") & (result.symbol == benchmarks[pool]), "date"
                ]
            )
            if calendar.empty:
                raise ValueError(f"Missing benchmark calendar for {pool}")
        else:
            for symbol in group.symbol:
                if symbol == "BTC-USD":
                    calendar = pd.date_range(window_start(as_of), as_of)
                else:
                    benchmark = "^STOXX50E" if symbol == "^STOXX50E" else "SPY"
                    calendar = pd.DatetimeIndex(
                        result.loc[
                            (result.pool == "reference") & (result.symbol == benchmark), "date"
                        ]
                    )
                one = coverage_report(
                    result[(result.pool == "reference") & (result.symbol == symbol)], calendar
                )
                one = group.loc[group.symbol == symbol, ["pool", "symbol"]].merge(
                    one, on=["pool", "symbol"], how="left"
                )
                one[["rows", "coverage"]] = one[["rows", "coverage"]].fillna(0)
                reports.append(one)
            continue
        coverage = coverage_report(result[result.pool == pool], calendar)
        coverage = group[["pool", "symbol"]].merge(coverage, on=["pool", "symbol"], how="left")
        coverage[["rows", "coverage"]] = coverage[["rows", "coverage"]].fillna(0)
        reports.append(coverage)
    if not reports:
        return pd.DataFrame(
            columns=["pool", "symbol", "rows", "first_date", "last_date", "coverage"]
        )
    return pd.concat(reports, ignore_index=True).sort_values(["coverage", "pool", "symbol"])


def write_coverage(result, requested, as_of, root=None):
    """Recompute the saved report from the supplied bars and requested membership."""
    report(requested_coverage(result, requested, as_of), "prices_coverage.csv", root)
