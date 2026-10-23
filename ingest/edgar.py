"""filing, fundamental_fact and filing_text tables (tasks A4, A5)."""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

import pandas as pd
from bs4 import BeautifulSoup

from ingest._common import (
    concat_tables,
    project_root,
    report_path,
    table_frame,
    user_agent,
    window_start,
)
from ingest.lake import read_table, write_table
from ingest.net import RateLimiter, build_session, get_with_retries
from tradepulse.contracts import load_table_spec

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
    value = str(cik).strip()
    if not value.isascii() or not value.isdigit() or len(value) > 10:
        raise ValueError("CIK must contain at most 10 decimal digits")
    return value.zfill(10)


def acceptance_to_utc(raw: str) -> pd.Timestamp:
    """Convert EDGAR submissions 'acceptanceDateTime' to a UTC Timestamp.

    The field looks like '2025-08-05T16:05:12.000Z' but the clock time is US/Eastern
    (see data-sources.md and the timezone check in TASK.md). Ignore the 'Z', localise to
    America/New_York (DST-aware), convert to UTC.
    """
    stamp = pd.Timestamp(raw.removesuffix("Z"))
    if stamp.tzinfo is not None:
        raise ValueError("Expected an EDGAR Eastern clock time with an optional trailing Z")
    return stamp.tz_localize("America/New_York").tz_convert("UTC")


def parse_submissions(payload: dict, symbol: str) -> pd.DataFrame:
    """Turn submissions JSON (filings.recent column arrays) into filing rows for `symbol`.

    - Keep only forms in FORMS.
    - items: the raw string, or None when empty.
    - report_date: None when empty.
    - primary_doc_url = f"{ARCHIVES}/{int(cik)}/{accession without dashes}/{primaryDocument}".
    - Columns in contract order, sorted by acceptance_datetime.
    """
    cik = cik10(payload["cik"])
    recent = pd.DataFrame(payload.get("filings", {}).get("recent", {}))
    rows = []
    for filing in recent.to_dict("records"):
        if filing["form"] not in FORMS:
            continue
        accession = filing["accessionNumber"]
        document = filing["primaryDocument"]
        rows.append(
            {
                "cik": cik,
                "symbol": symbol,
                "accession_number": accession,
                "form": filing["form"],
                "items": filing.get("items") or None,
                "filing_date": filing["filingDate"],
                "acceptance_datetime": acceptance_to_utc(filing["acceptanceDateTime"]),
                "report_date": filing.get("reportDate") or None,
                "primary_document": document,
                "primary_doc_url": f"{ARCHIVES}/{int(cik)}/{accession.replace('-', '')}/{document}",
            }
        )
    return table_frame("filing", rows).sort_values("acceptance_datetime").reset_index(drop=True)


def parse_companyfacts(payload: dict, symbol: str) -> pd.DataFrame:
    """Turn companyfacts JSON into fundamental_fact rows for the tags in FACT_TAGS only.

    Each element of facts[taxonomy][tag]["units"][unit] becomes one row:
    value=val, period_start=start (None for instant facts), period_end=end, fiscal_year=fy,
    fiscal_period=fp, form, filed, accession_number=accn, frame (None if absent).
    Exact duplicate rows (same primary key) are dropped. Columns in contract order.
    """
    cik = cik10(payload["cik"])
    rows = []
    for taxonomy, tag in FACT_TAGS:
        units = payload.get("facts", {}).get(taxonomy, {}).get(tag, {}).get("units", {})
        for unit, facts in units.items():
            for fact in facts:
                rows.append(
                    {
                        "cik": cik,
                        "symbol": symbol,
                        "taxonomy": taxonomy,
                        "tag": tag,
                        "unit": unit,
                        "value": fact["val"],
                        "period_start": fact.get("start"),
                        "period_end": fact["end"],
                        "fiscal_year": fact.get("fy"),
                        "fiscal_period": fact.get("fp"),
                        "form": fact["form"],
                        "filed": fact["filed"],
                        "accession_number": fact["accn"],
                        "frame": fact.get("frame"),
                    }
                )
    frame = table_frame("fundamental_fact", rows)
    return frame.drop_duplicates(load_table_spec("fundamental_fact")["primary_key"]).reset_index(
        drop=True
    )


def find_exhibit_url(index_html: str, exhibit_type: str = "EX-99.1") -> str | None:
    """Find the document of type `exhibit_type` in a filing index page (*-index.htm).

    The page has a table with columns Seq, Description, Document, Type, Size. Return the absolute
    URL ("https://www.sec.gov" + href) of the first row whose Type equals exhibit_type.
    Inline-XBRL viewer links ('/ix?doc=/Archives/...') must be turned into the plain
    '/Archives/...' path. Return None when no row matches.
    """
    soup = BeautifulSoup(index_html, "lxml")
    for table in soup.find_all("table"):
        headers = []
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            values = [cell.get_text(" ", strip=True) for cell in cells]
            if "Type" in values and "Document" in values:
                headers = values
                continue
            if not headers or len(cells) != len(headers):
                continue
            if values[headers.index("Type")] != exhibit_type:
                continue
            link = cells[headers.index("Document")].find("a", href=True)
            if link is None:
                continue
            href = link["href"]
            parts = urlsplit(href)
            if parts.path.rstrip("/") in {"/ix", "/ixviewer/doc/action"}:
                href = parse_qs(parts.query).get("doc", [""])[0]
            url = urljoin("https://www.sec.gov", href)
            parts = urlsplit(url)
            if parts.scheme != "https" or parts.netloc != "www.sec.gov":
                raise ValueError("Filing document must be hosted on the SEC archive")
            if not parts.path.startswith("/Archives/"):
                raise ValueError("Filing document is outside the SEC archive")
            return url
    return None


def html_to_text(html: str, max_chars: int = 200_000) -> str:
    """Strip tags, drop <script>/<style> content, decode entities (&nbsp; -> space),
    collapse all whitespace runs to one space, strip, truncate to max_chars."""
    if max_chars < 0:
        raise ValueError("max_chars must be nonnegative")
    soup = BeautifulSoup(html, "lxml")
    for element in soup(["script", "style"]):
        element.decompose()
    return " ".join(soup.get_text(" ").split())[:max_chars]


def run_filings(as_of: dt.date, root: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch submissions and companyfacts for every US member; write filing and fundamental_fact."""
    universe = read_table("universe_member", root)
    us = universe[universe["pool"] == "us_equity"]
    if us["cik"].isna().any():
        raise ValueError("Every US member needs a CIK before fetching SEC data")
    start = pd.Timestamp(window_start(as_of, root))
    end = pd.Timestamp(as_of)
    cutoff = end.tz_localize("UTC") + pd.Timedelta(days=1)
    filings, facts = [], []
    limiter = RateLimiter(8)
    with build_session(user_agent("SEC_USER_AGENT", root)) as session:
        for cik, members in us.groupby("cik", sort=False):
            cik = cik10(cik)
            payloads = []
            for url in (
                f"https://data.sec.gov/submissions/CIK{cik}.json",
                f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
            ):
                response = get_with_retries(session, url, limiter)
                response.raise_for_status()
                payloads.append(response.json())
            for symbol in members["symbol"]:
                filing = parse_submissions(payloads[0], symbol)
                mask = filing["filing_date"].between(start, end)
                mask &= filing["acceptance_datetime"] <= cutoff
                mask &= filing["report_date"].isna() | filing["report_date"].le(end)
                filings.append(filing[mask])
                fact = parse_companyfacts(payloads[1], symbol)
                mask = fact["filed"].between(start, end) & fact["period_end"].le(end)
                mask &= fact["period_start"].isna() | fact["period_start"].le(end)
                facts.append(fact[mask])
    filing = concat_tables("filing", filings)
    fact = concat_tables("fundamental_fact", facts)
    write_table(filing, "filing", root, as_of)
    write_table(fact, "fundamental_fact", root, as_of)
    return filing, fact


def run_texts(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    """Download EX-99.1 for 8-K item 2.02 filings in the window (+ 10-K for showcase names)."""
    filings = read_table("filing", root)
    end = pd.Timestamp(as_of)
    cutoff = end.tz_localize("UTC") + pd.Timedelta(days=1)
    filings = filings[(filings["filing_date"] <= end) & (filings["acceptance_datetime"] <= cutoff)]
    start = pd.Timestamp(window_start(as_of, root, warmup=False))
    releases = filings[
        filings["form"].isin(["8-K", "8-K/A"])
        & filings["filing_date"].ge(start)
        & filings["items"]
        .fillna("")
        .str.split(",")
        .map(lambda items: "2.02" in [item.strip() for item in items])
    ]
    showcase = showcase_symbols(root)
    annual = filings[filings["form"].eq("10-K") & filings["symbol"].isin(showcase)]
    annual = annual.sort_values("acceptance_datetime").groupby("symbol", sort=False).tail(1)
    selected = pd.concat(
        [releases.assign(document_type="EX-99.1"), annual.assign(document_type="10-K")],
        ignore_index=True,
    )
    rows, missing = [], []
    cache: dict[str, tuple[str, pd.Timestamp]] = {}
    index_cache: dict[str, str | None] = {}
    limiter = RateLimiter(8)
    with build_session(user_agent("SEC_USER_AGENT", root)) as session:
        for filing in selected.itertuples(index=False):
            url = filing.primary_doc_url
            if filing.document_type == "EX-99.1":
                accession = filing.accession_number
                index_url = f"{ARCHIVES}/{int(filing.cik)}/{accession.replace('-', '')}/{accession}-index.htm"
                if index_url not in index_cache:
                    response = get_with_retries(session, index_url, limiter)
                    response.raise_for_status()
                    index_cache[index_url] = find_exhibit_url(response.text)
                url = index_cache[index_url]
                if url is None:
                    missing.append(
                        {
                            "symbol": filing.symbol,
                            "accession_number": accession,
                            "reason": "EX-99.1 not found",
                        }
                    )
                    continue
            if url not in cache:
                response = get_with_retries(session, url, limiter)
                response.raise_for_status()
                cache[url] = (html_to_text(response.text), pd.Timestamp.now(tz="UTC"))
            text, fetched_at = cache[url]
            rows.append(
                {
                    "accession_number": filing.accession_number,
                    "cik": filing.cik,
                    "symbol": filing.symbol,
                    "document_name": unquote(urlsplit(url).path.rsplit("/", 1)[-1]),
                    "document_type": filing.document_type,
                    "url": url,
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "text": text,
                    "char_count": len(text),
                    "available_at": filing.acceptance_datetime,
                    "fetched_at": fetched_at,
                }
            )
    output = table_frame("filing_text", rows)
    write_table(output, "filing_text", root, as_of)
    pd.DataFrame(missing, columns=["symbol", "accession_number", "reason"]).to_csv(
        report_path(root, "filing_text_missing.csv"), index=False
    )
    return output


def showcase_symbols(root: Path | None = None) -> tuple[str, ...]:
    """Both endpoints of the curated seed graph are showcase names."""
    edges = pd.read_csv(project_root(root) / "config" / "graph" / "seed_edges.csv")
    return tuple(dict.fromkeys([*edges["src_symbol"].dropna(), *edges["dst_symbol"].dropna()]))
