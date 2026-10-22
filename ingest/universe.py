"""universe_member table (task A1). See contracts/tables/universe_member.json."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd


def to_yahoo_symbol_us(ticker: str) -> str:
    """Wikipedia/SEC US ticker -> Yahoo symbol: strip, upper-case, '.' -> '-' (BRK.B -> BRK-B)."""
    raise NotImplementedError("A1")


def eu_yahoo_symbol(ticker: str, exchange: str) -> str:
    """European ticker + exchange text -> Yahoo symbol, using the exchange map in ingest/TASK.md.

    Matching is case-insensitive on substrings of `exchange`. The ticker is stripped and
    upper-cased; inner spaces become '-'. Unknown exchange -> ValueError (never guess).
    """
    raise NotImplementedError("A1")


def parse_sp500(html: str) -> pd.DataFrame:
    """Parse the Wikipedia S&P 500 page (table id="constituents").

    Returns columns: symbol (Yahoo form), name, sector (GICS Sector), cik (10-digit zero-padded
    string), wikipedia_title (from the company link href after /wiki/, URL-decoded; None if no link).
    Hint: pandas.read_html(..., attrs={"id": "constituents"}, extract_links="body").
    """
    raise NotImplementedError("A1")


def parse_nasdaq100(html: str) -> pd.DataFrame:
    """Parse the Wikipedia Nasdaq-100 page (table id="constituents").

    Returns columns: symbol (Yahoo form), name, sector, wikipedia_title. Column headers may be
    'Ticker' or 'Symbol' and 'Company' or 'Security'; accept both.
    """
    raise NotImplementedError("A1")


def parse_eurostoxx50(html: str) -> pd.DataFrame:
    """Parse the Wikipedia EURO STOXX 50 components table.

    Returns columns: symbol (Yahoo form via eu_yahoo_symbol), name, sector, country (ISO alpha-2),
    wikipedia_title. Inspect the live page and document the columns you rely on in a comment.
    """
    raise NotImplementedError("A1")


def combine_us(sp500: pd.DataFrame, ndx: pd.DataFrame, extras: pd.DataFrame,
               ticker_ciks: dict[str, str], snapshot_date: dt.date) -> pd.DataFrame:
    """Merge the US sources into rows that satisfy the universe_member contract.

    - One row per symbol; pool "us_equity", currency "USD", country "US".
    - index_membership joins the sources the symbol appears in, in the order SP500|NDX|EXTRA.
    - name, sector and wikipedia_title come from the first source in that order that has them.
    - cik comes from sp500 when present, else from ticker_ciks[symbol], else None.
    - extras columns: symbol, name, sector (plus optional notes columns that are ignored).
    """
    raise NotImplementedError("A1")


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    """Fetch every source, build all three pools, write the table with lake.write_table and return it."""
    raise NotImplementedError("A1")
