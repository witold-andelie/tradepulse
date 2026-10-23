"""price_bar table (task A2). See contracts/tables/price_bar.json."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import time

import pandas as pd

from ingest._common import (
    concat_tables,
    project_root,
    report_path,
    table_frame,
    user_agent,
    window_start,
)
from ingest.lake import read_table, write_table
from ingest.net import RateLimiter, YahooAdapter, build_session

REFERENCE_SYMBOLS = ("SPY", "^VIX", "^VIX3M", "^STOXX50E", "BTC-USD")
RAW_COLUMNS = ("symbol", "date", "Open", "High", "Low", "Close", "Adj Close", "Volume")


def _session_date(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize(None).normalize() if stamp.tzinfo else stamp.normalize()


def to_price_bars(
    raw: pd.DataFrame, pool: str, currency_by_symbol: dict[str, str], ingested_at: pd.Timestamp
) -> pd.DataFrame:
    """Convert a long raw frame into price_bar rows.

    raw columns: symbol, date, Open, High, Low, Close, Adj Close, Volume (yfinance names, one row
    per symbol and date). Output columns follow the contract in contract order; source = "yahoo".
    - Rows with a missing Close or Adj Close are dropped (never filled).
    - date becomes a timezone-naive midnight datetime64.
    - Volume 0 or missing on a 'reference' symbol becomes null (indices have no volume).
    - Output sorted by symbol, date with a fresh RangeIndex.
    """
    frame = raw.dropna(subset=["Close", "Adj Close"]).copy()
    frame = frame.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )
    frame["date"] = frame["date"].map(_session_date)
    frame["currency"] = frame["symbol"].map(currency_by_symbol)
    if frame["currency"].isna().any():
        raise ValueError("Missing price currency for a requested symbol")
    if pool == "reference":
        frame["volume"] = frame["volume"].mask(frame["volume"].eq(0))
    frame = frame.assign(pool=pool, source="yahoo", ingested_at=ingested_at)
    return table_frame("price_bar", frame).sort_values(["symbol", "date"]).reset_index(drop=True)


def coverage_report(bars: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """One row per (pool, symbol): rows, first_date, last_date, coverage.

    coverage = (number of calendar dates between first_date and the calendar's last date that the
    symbol has a bar for) / (number of calendar dates in that same range). A symbol listed recently
    is therefore not punished for dates before it existed. Sorted by coverage ascending.
    """
    calendar = pd.DatetimeIndex([_session_date(value) for value in calendar]).unique().sort_values()
    output = []
    for (pool, symbol), group in bars.groupby(["pool", "symbol"], sort=True):
        dates = pd.DatetimeIndex(group["date"].map(_session_date)).unique().sort_values()
        eligible = calendar[calendar >= dates.min()]
        coverage = len(dates.intersection(eligible)) / len(eligible) if len(eligible) else 0.0
        output.append(
            {
                "pool": pool,
                "symbol": symbol,
                "rows": len(dates),
                "first_date": dates.min(),
                "last_date": dates.max(),
                "coverage": coverage,
            }
        )
    return (
        pd.DataFrame(
            output, columns=["pool", "symbol", "rows", "first_date", "last_date", "coverage"]
        )
        .sort_values("coverage", kind="stable")
        .reset_index(drop=True)
    )


def fetch_prices(symbols: list[str], start: dt.date, end: dt.date) -> pd.DataFrame:
    """Download daily bars with yfinance (auto_adjust=False) in batches of 50; return the raw long frame."""
    import yfinance as yf

    if start > end:
        raise ValueError("start must be on or before end")
    symbols = list(dict.fromkeys(symbols))
    if not symbols:
        return pd.DataFrame(columns=RAW_COLUMNS)
    frames = []
    limiter = RateLimiter(2)
    # Yahoo has no separate contact setting; reuse the Wikimedia contact identity.
    with build_session(user_agent("WIKIMEDIA_USER_AGENT")) as session:
        adapter = YahooAdapter(limiter)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        # Newer yfinance can retry internally too. Transport retries own that budget.
        network = getattr(getattr(yf, "config", None), "network", None)
        old_retries = getattr(network, "retries", None)
        if old_retries is not None:
            network.retries = 0
        try:
            for offset in range(0, len(symbols), 50):
                if offset:
                    time.sleep(1.0)
                batch = symbols[offset : offset + 50]
                raw = yf.download(
                    batch,
                    start=start,
                    end=end + dt.timedelta(days=1),
                    interval="1d",
                    auto_adjust=False,
                    group_by="ticker",
                    threads=False,
                    progress=False,
                    timeout=30,
                    session=session,
                )
                if raw is None or raw.empty:
                    continue
                for symbol in batch:
                    if isinstance(raw.columns, pd.MultiIndex):
                        level = next(
                            (
                                index
                                for index in range(raw.columns.nlevels)
                                if symbol in raw.columns.get_level_values(index)
                            ),
                            None,
                        )
                        if level is None:
                            continue
                        part = raw.xs(symbol, axis=1, level=level).copy()
                    elif len(batch) == 1:
                        part = raw.copy()
                    else:
                        raise ValueError("Unexpected yfinance columns for multiple symbols")
                    # DatetimeIndex.map can retain its original timezone even when
                    # the function returns naive timestamps; construct explicitly.
                    part["date"] = pd.DatetimeIndex([_session_date(value) for value in part.index])
                    part["symbol"] = symbol
                    part = part.reindex(columns=RAW_COLUMNS)
                    part = part[part["date"].between(pd.Timestamp(start), pd.Timestamp(end))]
                    frames.append(part.reset_index(drop=True))
        finally:
            if old_retries is not None:
                network.retries = old_retries
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=RAW_COLUMNS)


def _calendar(bars: pd.DataFrame, pool: str, start: dt.date, end: dt.date) -> pd.DatetimeIndex:
    if pool == "crypto":
        return pd.date_range(start, end, freq="D")
    benchmark = {"us_equity": "SPY", "eu_equity": "^STOXX50E"}[pool]
    dates = bars.loc[(bars["pool"] == pool) | bars["symbol"].eq(benchmark), "date"]
    return pd.DatetimeIndex(dates).unique().sort_values()


def _coverage(
    bars: pd.DataFrame, requested: pd.DataFrame, start: dt.date, end: dt.date
) -> pd.DataFrame:
    reports = []
    for pool, members in requested.groupby("pool", sort=False):
        pool_bars = bars[bars["pool"] == pool]
        if pool == "reference":
            parts = []
            for symbol in members["symbol"]:
                market = (
                    "crypto"
                    if symbol == "BTC-USD"
                    else ("eu_equity" if symbol == "^STOXX50E" else "us_equity")
                )
                parts.append(
                    coverage_report(
                        pool_bars[pool_bars["symbol"] == symbol],
                        _calendar(bars, market, start, end),
                    )
                )
            report = pd.concat(parts, ignore_index=True)
        else:
            report = coverage_report(pool_bars, _calendar(bars, pool, start, end))
        report = members[["pool", "symbol"]].merge(report, how="left", on=["pool", "symbol"])
        report["rows"] = report["rows"].fillna(0).astype("int64")
        report["coverage"] = report["coverage"].fillna(0.0)
        reports.append(report)
    return pd.concat(reports, ignore_index=True).sort_values("coverage", kind="stable")


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    """Fetch all pools and reference symbols, write price_bar and the coverage report."""
    root = project_root(root)
    # Load root-local contact settings before fetch_prices uses the process environment.
    user_agent("WIKIMEDIA_USER_AGENT", root)
    universe = read_table("universe_member", root)
    start = window_start(as_of, root)
    symbols = list(dict.fromkeys([*universe["symbol"], *REFERENCE_SYMBOLS]))
    raw = fetch_prices(symbols, start, as_of)
    raw = raw[pd.to_datetime(raw["date"]).between(pd.Timestamp(start), pd.Timestamp(as_of))]
    ingested_at = pd.Timestamp.now(tz="UTC")
    frames = []
    requested = universe[["pool", "symbol", "currency"]].copy()
    references = pd.DataFrame(
        {
            "pool": "reference",
            "symbol": REFERENCE_SYMBOLS,
            "currency": ["USD", "USD", "USD", "EUR", "USD"],
        }
    )
    requested = pd.concat([requested, references], ignore_index=True)
    for pool, members in requested.groupby("pool", sort=False):
        currencies = dict(zip(members["symbol"], members["currency"], strict=True))
        frames.append(
            to_price_bars(raw[raw["symbol"].isin(currencies)], pool, currencies, ingested_at)
        )
    output = concat_tables("price_bar", frames)
    report = _coverage(output, requested, start, as_of)
    write_table(output, "price_bar", root, as_of)
    report.to_csv(report_path(root, "prices_coverage.csv"), index=False)
    return output
