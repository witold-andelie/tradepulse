"""Build the current membership snapshot from provider lists and curated extras."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import pandas as pd
from bs4 import BeautifulSoup

from ingest.common import environment, frame
from ingest.lake import write_table
from ingest.net import RateLimiter, build_session, fetch_response
from tradepulse.contracts import REPO_ROOT


def to_yahoo_symbol_us(ticker: str) -> str:
    return ticker.strip().upper().replace(".", "-")


def eu_yahoo_symbol(ticker: str, exchange: str) -> str:
    mapping = [
        ("xetra|frankfurt|deutsche börse", ".DE"),
        ("paris", ".PA"),
        ("amsterdam", ".AS"),
        ("brussels", ".BR"),
        ("milan|borsa italiana", ".MI"),
        ("madrid|bme", ".MC"),
        ("helsinki", ".HE"),
        ("dublin", ".IR"),
        ("lisbon", ".LS"),
    ]
    for aliases, suffix in mapping:
        if any(alias in exchange.lower() for alias in aliases.split("|")):
            return "-".join(ticker.strip().upper().split()) + suffix
    raise ValueError(f"Unsupported exchange: {exchange}")


def _table_rows(table):
    rows = table.find_all("tr")
    if not rows:
        return []
    headers = [_text(c) for c in rows[0].find_all(["th", "td"])]
    output = []
    for row in rows[1:]:
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) == len(headers):
            output.append(dict(zip(headers, cells)))
    return output


def _cell(row, *keys):
    for key in keys:
        if key in row:
            return row[key]
    raise ValueError(f"Missing source column: {keys}")


def _text(cell):
    for note in cell.select("sup"):
        note.decompose()
    return cell.get_text(" ", strip=True)


def _title(cell):
    for link in cell.find_all("a", href=True):
        url = urlsplit(urljoin("https://en.wikipedia.org/wiki/", link["href"]))
        if url.hostname == "en.wikipedia.org" and url.path.startswith("/wiki/"):
            return unquote(url.path[6:])
    return None


def _parse_us(html, sp500):
    table = BeautifulSoup(html, "lxml").find("table", id="constituents")
    if table is None:
        raise ValueError("Constituents table missing; provider layout changed")
    rows = []
    for source in _table_rows(table):
        company = _cell(source, "Security", "Company")
        row = {
            "symbol": to_yahoo_symbol_us(_text(_cell(source, "Symbol", "Ticker"))),
            "name": _text(company),
            "sector": _text(source["GICS Sector"]) if "GICS Sector" in source else None,
            "wikipedia_title": _title(company),
        }
        if sp500:
            row["cik"] = str(int(_text(_cell(source, "CIK")))).zfill(10)
        rows.append(row)
    columns = ["symbol", "name", "sector"] + (["cik"] if sp500 else []) + ["wikipedia_title"]
    return pd.DataFrame(rows, columns=columns)


def parse_sp500(html: str) -> pd.DataFrame:
    return _parse_us(html, True)


def parse_nasdaq100(html: str) -> pd.DataFrame:
    return _parse_us(html, False)


def parse_eurostoxx50(html: str) -> pd.DataFrame:
    # Wikipedia inspected 2026-10-23: Ticker, Main listing, Name, Corporate form,
    # Registered office, Sector, Founded. Main listing supplies the exchange; registered
    # office is NOT the listing country. Also accept the explicit Exchange/Country layout.
    countries = {
        "Germany": "DE",
        "France": "FR",
        "Netherlands": "NL",
        "Belgium": "BE",
        "Italy": "IT",
        "Spain": "ES",
        "Finland": "FI",
        "Ireland": "IE",
        "Portugal": "PT",
        "Luxembourg": "LU",
    }
    for table in BeautifulSoup(html, "lxml").find_all("table"):
        records = _table_rows(table)
        if not records or not ("Exchange" in records[0] or "Main listing" in records[0]):
            continue
        result = []
        for row in records:
            company = _cell(row, "Company", "Name")
            listing = _text(_cell(row, "Exchange", "Main listing"))
            # The abbreviated exchange labels are explicit links on the source page.
            exchange = {"FWB": "Frankfurt", "BMAD": "Madrid", "BIT": "Borsa Italiana"}.get(
                listing.split(":")[0].strip(), listing
            )
            ticker = _text(_cell(row, "Ticker", "Symbol"))
            # Ticker may already carry a Yahoo suffix. Derive the suffix from the exchange.
            symbol = eu_yahoo_symbol(ticker.rsplit(".", 1)[0], exchange)
            country = {
                ".DE": "DE",
                ".PA": "FR",
                ".AS": "NL",
                ".BR": "BE",
                ".MI": "IT",
                ".MC": "ES",
                ".HE": "FI",
                ".IR": "IE",
                ".LS": "PT",
            }[symbol[-3:]]
            if "Country" in row:
                raw_country = _text(row["Country"])
                if raw_country not in countries and raw_country not in countries.values():
                    raise ValueError(f"Unknown country: {raw_country}")
                country = countries.get(raw_country, raw_country)
            result.append(
                {
                    "symbol": symbol,
                    "name": _text(company),
                    "sector": _text(_cell(row, "Industry", "Sector")),
                    "country": country,
                    "wikipedia_title": _title(company),
                }
            )
        return pd.DataFrame(result)
    raise ValueError("EU components table requires explicit Exchange and Country columns")


def combine_us(
    sp500: pd.DataFrame,
    ndx: pd.DataFrame,
    extras: pd.DataFrame,
    ticker_ciks: dict[str, str],
    snapshot_date: dt.date,
) -> pd.DataFrame:
    merged = {}
    for label, source in [("SP500", sp500), ("NDX", ndx), ("EXTRA", extras)]:
        for item in source.to_dict("records"):
            symbol = to_yahoo_symbol_us(item["symbol"])
            row = merged.setdefault(
                symbol,
                {
                    "pool": "us_equity",
                    "symbol": symbol,
                    "name": None,
                    "sector": None,
                    "country": "US",
                    "currency": "USD",
                    "cik": None,
                    "wikipedia_title": None,
                    "index_membership": "",
                    "snapshot_date": snapshot_date,
                },
            )
            memberships = row["index_membership"].split("|") if row["index_membership"] else []
            if label not in memberships:
                row["index_membership"] = "|".join(memberships + [label])
            for key in ("name", "sector", "wikipedia_title"):
                if pd.isna(row[key]) and pd.notna(item.get(key)) and item.get(key):
                    row[key] = item[key]
            if label == "SP500" and pd.notna(item.get("cik")):
                row["cik"] = str(int(item["cik"])).zfill(10)
    for symbol, row in merged.items():
        if row["cik"] is None and symbol in ticker_ciks:
            row["cik"] = str(int(ticker_ciks[symbol])).zfill(10)
    return (
        frame(list(merged.values()), "universe_member").sort_values("symbol").reset_index(drop=True)
    )


def fetch_universe_sources():
    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        limiter = RateLimiter(50)
        pages = [
            fetch_response(session, "https://en.wikipedia.org/wiki/" + path, limiter).text
            for path in ["List_of_S%26P_500_companies", "Nasdaq-100", "EURO_STOXX_50"]
        ]
        if BeautifulSoup(pages[1], "lxml").find("table", id="constituents") is None:
            # The index article now links to a dedicated constituents article.
            soup = BeautifulSoup(pages[1], "lxml")
            link = soup.find(
                "a",
                href=lambda href: (
                    bool(href) and href.endswith("/wiki/List_of_NASDAQ-100_companies")
                ),
            )
            if link is None:
                raise ValueError(
                    "Nasdaq constituent table and linked component article are missing"
                )
            pages[1] = fetch_response(
                session, "https://en.wikipedia.org/wiki/List_of_NASDAQ-100_companies", limiter
            ).text
    with build_session(environment("SEC_USER_AGENT")) as session:
        tickers = fetch_response(
            session, "https://www.sec.gov/files/company_tickers.json", RateLimiter(8)
        ).json()
    return pages, {
        to_yahoo_symbol_us(v["ticker"]): str(v["cik_str"]).zfill(10) for v in tickers.values()
    }


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    pages, tickers = fetch_universe_sources()
    base = REPO_ROOT / "config/universe"
    # Current constituents cannot be represented as a historical membership snapshot.
    snapshot = dt.datetime.now(dt.UTC).date()
    us = combine_us(
        parse_sp500(pages[0]),
        parse_nasdaq100(pages[1]),
        pd.read_csv(base / "us_extras.csv"),
        tickers,
        snapshot,
    )
    if us.sector.isna().any():
        source_sectors = fetch_gics_sectors()
        missing = us.sector.isna()
        us.loc[missing, "sector"] = us.loc[missing, "symbol"].map(source_sectors)
        from ingest.common import report

        report(
            pd.DataFrame(
                [
                    {
                        "symbol": symbol,
                        "sector": source_sectors.get(symbol),
                        "source": GICS_HOLDINGS_URL,
                        "taxonomy": "GICS",
                    }
                    for symbol in us.loc[missing, "symbol"]
                ]
            ),
            "universe_sector_sources.csv",
            root,
        )
        if us.sector.isna().any():
            raise ValueError(
                "US members still lack verified GICS sectors; see universe_sector_sources.csv"
            )
    eu = parse_eurostoxx50(pages[2]).assign(index_membership="SX5E")
    extras = pd.read_csv(base / "eu_extras.csv").assign(index_membership="EXTRA")
    eu = pd.concat([eu, extras], ignore_index=True)
    eu["index_membership"] = eu.groupby("symbol")["index_membership"].transform(
        lambda s: "|".join(dict.fromkeys(s))
    )
    eu = eu.drop_duplicates("symbol").assign(
        pool="eu_equity", currency="EUR", cik=None, snapshot_date=snapshot
    )
    crypto = pd.read_csv(base / "crypto.csv").rename(columns={"category": "sector"})
    if crypto.symbol.isna().any():
        raise ValueError(
            "Complete missing symbols in config/universe/crypto.csv before live ingestion"
        )
    crypto = crypto.assign(
        pool="crypto",
        country=None,
        currency="USD",
        cik=None,
        index_membership="CRYPTO_TOP",
        snapshot_date=snapshot,
    )
    result = frame(pd.concat([us, eu, crypto]).to_dict("records"), "universe_member")
    write_table(result, "universe_member", root, as_of)
    return result


GICS_HOLDINGS_URL = (
    "https://www.ishares.com/uk/individual/en/products/253741/"
    "ishares-nasdaq-100-ucits-etf/latest-holdings.csv"
)


def fetch_gics_sectors():
    """Use the issuer's Nasdaq holdings sector data, never translate ICB labels."""
    from io import StringIO

    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        text = fetch_response(session, GICS_HOLDINGS_URL, RateLimiter(1)).text
    cache = REPO_ROOT / "data/cache/diagnostics/CNDX_holdings.csv"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    lines = text.lstrip("\ufeff").splitlines()
    header = next(
        (i for i, line in enumerate(lines) if line.startswith(("Ticker,", '"Ticker",'))), None
    )
    if header is None:
        raise ValueError("iShares holdings CSV header missing")
    data = pd.read_csv(StringIO("\n".join(lines[header:])))
    data = data[data["Asset Class"] == "Equity"].copy()
    # BlackRock abbreviates this GICS sector as "Communication" in its CSV.
    data["Sector"] = data["Sector"].replace({"Communication": "Communication Services"})
    allowed = {
        "Information Technology",
        "Health Care",
        "Consumer Discretionary",
        "Consumer Staples",
        "Communication Services",
        "Industrials",
        "Energy",
        "Financials",
        "Real Estate",
        "Utilities",
        "Materials",
    }
    if not set(data.Sector) <= allowed:
        raise ValueError("Issuer holdings sector labels are not the required GICS vocabulary")
    return dict(zip(data.Ticker, data.Sector))
