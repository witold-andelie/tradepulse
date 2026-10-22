"""filing, fundamental_fact and filing_text tables (tasks A4, A5)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
FACT_TAGS = (
    ("us-gaap", "EarningsPerShareDiluted"),
    ("us-gaap", "Revenues"),
    ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
    ("dei", "EntityCommonStockSharesOutstanding"),
)
FORMS = ("8-K", "8-K/A", "10-Q", "10-Q/A", "10-K", "10-K/A")


def cik10(cik: int | str) -> str:
    """Zero-pad a CIK to 10 digits: 320193 -> '0000320193'."""
    raise NotImplementedError("A4")


def acceptance_to_utc(raw: str) -> pd.Timestamp:
    """Convert EDGAR submissions 'acceptanceDateTime' to a UTC Timestamp.

    The field looks like '2025-08-05T16:05:12.000Z' but the clock time is US/Eastern
    (see data-sources.md and the timezone check in TASK.md). Ignore the 'Z', localise to
    America/New_York (DST-aware), convert to UTC.
    """
    raise NotImplementedError("A4")


def parse_submissions(payload: dict, symbol: str) -> pd.DataFrame:
    """Turn submissions JSON (filings.recent column arrays) into filing rows for `symbol`.

    - Keep only forms in FORMS.
    - items: the raw string, or None when empty.
    - report_date: None when empty.
    - primary_doc_url = f"{ARCHIVES}/{int(cik)}/{accession without dashes}/{primaryDocument}".
    - Columns in contract order, sorted by acceptance_datetime.
    """
    raise NotImplementedError("A4")


def parse_companyfacts(payload: dict, symbol: str) -> pd.DataFrame:
    """Turn companyfacts JSON into fundamental_fact rows for the tags in FACT_TAGS only.

    Each element of facts[taxonomy][tag]["units"][unit] becomes one row:
    value=val, period_start=start (None for instant facts), period_end=end, fiscal_year=fy,
    fiscal_period=fp, form, filed, accession_number=accn, frame (None if absent).
    Exact duplicate rows (same primary key) are dropped. Columns in contract order.
    """
    raise NotImplementedError("A4")


def find_exhibit_url(index_html: str, exhibit_type: str = "EX-99.1") -> str | None:
    """Find the document of type `exhibit_type` in a filing index page (*-index.htm).

    The page has a table with columns Seq, Description, Document, Type, Size. Return the absolute
    URL ("https://www.sec.gov" + href) of the first row whose Type equals exhibit_type.
    Inline-XBRL viewer links ('/ix?doc=/Archives/...') must be turned into the plain
    '/Archives/...' path. Return None when no row matches.
    """
    raise NotImplementedError("A5")


def html_to_text(html: str, max_chars: int = 200_000) -> str:
    """Strip tags, drop <script>/<style> content, decode entities (&nbsp; -> space),
    collapse all whitespace runs to one space, strip, truncate to max_chars."""
    raise NotImplementedError("A5")


def run_filings(as_of: dt.date, root: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch submissions and companyfacts for every US member; write filing and fundamental_fact."""
    raise NotImplementedError("A4")


def run_texts(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    """Download EX-99.1 for 8-K item 2.02 filings in the window (+ 10-K for showcase names)."""
    raise NotImplementedError("A5")
