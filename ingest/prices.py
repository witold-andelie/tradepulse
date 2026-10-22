"""price_bar table (task A2). See contracts/tables/price_bar.json."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

REFERENCE_SYMBOLS = ("SPY", "^VIX", "^VIX3M", "^STOXX50E", "BTC-USD")


def to_price_bars(raw: pd.DataFrame, pool: str, currency_by_symbol: dict[str, str],
                  ingested_at: pd.Timestamp) -> pd.DataFrame:
    """Convert a long raw frame into price_bar rows.

    raw columns: symbol, date, Open, High, Low, Close, Adj Close, Volume (yfinance names, one row
    per symbol and date). Output columns follow the contract in contract order; source = "yahoo".
    - Rows with a missing Close or Adj Close are dropped (never filled).
    - date becomes a timezone-naive midnight datetime64.
    - Volume 0 or missing on a 'reference' symbol becomes null (indices have no volume).
    - Output sorted by symbol, date with a fresh RangeIndex.
    """
    raise NotImplementedError("A2")


def coverage_report(bars: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """One row per (pool, symbol): rows, first_date, last_date, coverage.

    coverage = (number of calendar dates between first_date and the calendar's last date that the
    symbol has a bar for) / (number of calendar dates in that same range). A symbol listed recently
    is therefore not punished for dates before it existed. Sorted by coverage ascending.
    """
    raise NotImplementedError("A2")


def fetch_prices(symbols: list[str], start: dt.date, end: dt.date) -> pd.DataFrame:
    """Download daily bars with yfinance (auto_adjust=False) in batches of 50; return the raw long frame."""
    raise NotImplementedError("A2")


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    """Fetch all pools and reference symbols, write price_bar and the coverage report."""
    raise NotImplementedError("A2")
