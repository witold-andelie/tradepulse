"""universe_member table (task A1). See contracts/tables/universe_member.json."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pandas as pd
from bs4 import BeautifulSoup, Tag

from ingest._common import project_root, table_frame, user_agent
from ingest.edgar import cik10
from ingest.lake import write_table
from ingest.net import RateLimiter, build_session, get_with_retries

EXCHANGES = {
    ".DE": ("xetra", "frankfurt", "deutsche börse", "deutsche boerse"),
    ".PA": ("euronext paris", "paris"),
    ".AS": ("euronext amsterdam", "amsterdam"),
    ".BR": ("euronext brussels", "brussels"),
    ".MI": ("borsa italiana", "euronext milan", "milan"),
    ".MC": ("bolsa de madrid", "bme", "madrid"),
    ".HE": ("nasdaq helsinki", "helsinki"),
    ".IR": ("euronext dublin", "dublin"),
    ".LS": ("euronext lisbon", "lisbon"),
}
COUNTRIES = {
    "germany": "DE",
    "france": "FR",
    "netherlands": "NL",
    "belgium": "BE",
    "italy": "IT",
    "spain": "ES",
    "finland": "FI",
    "ireland": "IE",
    "portugal": "PT",
    "austria": "AT",
    "luxembourg": "LU",
}


def _text(cell: Tag) -> str:
    return " ".join(cell.stripped_strings)


def _article(cell: Tag) -> str | None:
    for link in cell.select('a[href*="/wiki/"]'):
        path = urlsplit(link["href"]).path
        if path.startswith("/wiki/"):
            title = unquote(path.removeprefix("/wiki/"))
            if not title.startswith(("File:", "Help:", "Special:")):
                return title
    return None


def _rows(table: Tag) -> list[dict[str, Tag]]:
    """Read simple constituent tables; remove footnotes from cell text."""
    for note in table.select("sup.reference"):
        note.decompose()
    headers: list[str] = []
    output = []
    for row in table.select("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if not headers and cells and all(cell.name == "th" for cell in cells):
            headers = [_text(cell).casefold() for cell in cells]
        elif headers and len(cells) == len(headers) and row.find("td"):
            output.append(dict(zip(headers, cells, strict=True)))
    return output


def _cell(row: dict[str, Tag], *names: str) -> Tag:
    for name in names:
        if name in row:
            return row[name]
    raise ValueError(f"Wikipedia table missing column: {' / '.join(names)}")


def _eu_symbol(row: dict[str, Tag]) -> str:
    ticker_cell = _cell(row, "ticker", "symbol", "ticker symbol")
    ticker = _text(ticker_cell)
    for key in ("exchange", "stock exchange"):
        if key in row:
            return eu_yahoo_symbol(ticker, _text(row[key]))
    # A Yahoo suffix or a named exchange in the ticker link is explicit evidence;
    # the company's country alone is insufficient to choose a listing.
    for suffix, names in EXCHANGES.items():
        if ticker.upper().endswith(suffix):
            return eu_yahoo_symbol(ticker, names[0])
    exchange = " ".join(
        str(link.get(key, "")) for link in ticker_cell.find_all("a") for key in ("title", "href")
    )
    return eu_yahoo_symbol(ticker, unquote(exchange))


def _parse_us(html: str, *, sp500: bool) -> pd.DataFrame:
    table = BeautifulSoup(html, "lxml").find("table", id="constituents")
    if table is None:
        raise ValueError("Wikipedia constituents table not found")
    output = []
    for row in _rows(table):
        company = _cell(row, "security", "company")
        record = {
            "symbol": to_yahoo_symbol_us(_text(_cell(row, "symbol", "ticker"))),
            "name": _text(company),
            "sector": _text(_cell(row, "gics sector", "gics sector[3]")),
            "wikipedia_title": _article(company),
        }
        if sp500:
            record["cik"] = cik10(_text(_cell(row, "cik")))
        output.append(record)
    columns = ["symbol", "name", "sector"] + (["cik"] if sp500 else []) + ["wikipedia_title"]
    return pd.DataFrame(output, columns=columns)


def to_yahoo_symbol_us(ticker: str) -> str:
    """Wikipedia/SEC US ticker -> Yahoo symbol: strip, upper-case, '.' -> '-' (BRK.B -> BRK-B)."""
    return ticker.strip().upper().replace(".", "-")


def eu_yahoo_symbol(ticker: str, exchange: str) -> str:
    """European ticker + exchange text -> Yahoo symbol, using the exchange map in ingest/TASK.md.

    Matching is case-insensitive on substrings of `exchange`. The ticker is stripped and
    upper-cased; inner spaces become '-'. Unknown exchange -> ValueError (never guess).
    """
    symbol = "-".join(ticker.strip().upper().split())
    for suffix, names in EXCHANGES.items():
        if any(name in exchange.casefold() for name in names):
            return symbol if symbol.endswith(suffix) else symbol + suffix
    raise ValueError(f"Unknown European exchange: {exchange}")


def parse_sp500(html: str) -> pd.DataFrame:
    """Parse the Wikipedia S&P 500 page (table id="constituents").

    Returns columns: symbol (Yahoo form), name, sector (GICS Sector), cik (10-digit zero-padded
    string), wikipedia_title (from the company link href after /wiki/, URL-decoded; None if no link).
    Hint: pandas.read_html(..., attrs={"id": "constituents"}, extract_links="body").
    """
    return _parse_us(html, sp500=True)


def parse_nasdaq100(html: str) -> pd.DataFrame:
    """Parse the Wikipedia Nasdaq-100 page (table id="constituents").

    Returns columns: symbol (Yahoo form), name, sector, wikipedia_title. Column headers may be
    'Ticker' or 'Symbol' and 'Company' or 'Security'; accept both.
    """
    return _parse_us(html, sp500=False)


def parse_eurostoxx50(html: str) -> pd.DataFrame:
    """Parse the Wikipedia EURO STOXX 50 components table.

    Returns columns: symbol (Yahoo form via eu_yahoo_symbol), name, sector, country (ISO alpha-2),
    wikipedia_title. Inspect the live page and document the columns you rely on in a comment.
    """
    # Expected headers: Company/Name, Ticker/Symbol, Sector/Industry/ICB sector,
    # Country and Exchange/Stock exchange. Verify these against the first live page;
    # absent exchange information must fail rather than invent a Yahoo suffix.
    soup = BeautifulSoup(html, "lxml")
    for table in soup.find_all("table"):
        rows = _rows(table)
        if not rows or not ({"ticker", "symbol", "ticker symbol"} & rows[0].keys()):
            continue
        if not ({"company", "name"} & rows[0].keys()):
            continue
        output = []
        for row in rows:
            company = _cell(row, "company", "name")
            country = _text(_cell(row, "country"))
            country_code = COUNTRIES.get(country.casefold(), country.upper())
            if len(country_code) != 2:
                raise ValueError(f"Unknown country in EURO STOXX table: {country}")
            output.append(
                {
                    "symbol": _eu_symbol(row),
                    "name": _text(company),
                    "sector": _text(
                        _cell(
                            row,
                            "sector",
                            "industry",
                            "icb sector",
                            "gics sector",
                            "supersector",
                            "icb supersector",
                        )
                    ),
                    "country": country_code,
                    "wikipedia_title": _article(company),
                }
            )
        return pd.DataFrame(
            output, columns=["symbol", "name", "sector", "country", "wikipedia_title"]
        )
    raise ValueError("EURO STOXX components table not found")


def combine_us(
    sp500: pd.DataFrame,
    ndx: pd.DataFrame,
    extras: pd.DataFrame,
    ticker_ciks: dict[str, str],
    snapshot_date: dt.date,
) -> pd.DataFrame:
    """Merge the US sources into rows that satisfy the universe_member contract.

    - One row per symbol; pool "us_equity", currency "USD", country "US".
    - index_membership joins the sources the symbol appears in, in the order SP500|NDX|EXTRA.
    - name, sector and wikipedia_title come from the first source in that order that has them.
    - cik comes from sp500 when present, else from ticker_ciks[symbol], else None.
    - extras columns: symbol, name, sector (plus optional notes columns that are ignored).
    """
    members: dict[str, dict] = {}
    ciks = {to_yahoo_symbol_us(symbol): cik10(cik) for symbol, cik in ticker_ciks.items()}
    for membership, frame in (("SP500", sp500), ("NDX", ndx), ("EXTRA", extras)):
        for source in frame.to_dict("records"):
            symbol = to_yahoo_symbol_us(source["symbol"])
            row = members.setdefault(
                symbol,
                {
                    "pool": "us_equity",
                    "symbol": symbol,
                    "name": None,
                    "sector": None,
                    "country": "US",
                    "currency": "USD",
                    "cik": ciks.get(symbol),
                    "wikipedia_title": None,
                    "index_membership": "",
                    "snapshot_date": snapshot_date,
                },
            )
            memberships = row["index_membership"].split("|") if row["index_membership"] else []
            if membership not in memberships:
                row["index_membership"] = "|".join([*memberships, membership])
            for key in ("name", "sector", "wikipedia_title"):
                value = source.get(key)
                if row[key] is None and pd.notna(value) and str(value).strip():
                    row[key] = value
            if membership == "SP500" and pd.notna(source.get("cik")):
                row["cik"] = cik10(source["cik"])
    return table_frame("universe_member", list(members.values()))


def run(as_of: dt.date, root: Path | None = None) -> pd.DataFrame:
    """Fetch every source, build all three pools, write the table with lake.write_table and return it."""
    root = project_root(root)
    directory = root / "config" / "universe"
    crypto = pd.read_csv(directory / "crypto.csv", dtype="string")
    symbol_column = "yahoo_symbol" if "yahoo_symbol" in crypto else "symbol"
    if crypto[symbol_column].isna().any() or crypto[symbol_column].str.strip().eq("").any():
        raise ValueError(
            "config/universe/crypto.csv has missing Yahoo symbols; curate before running"
        )
    snapshot_date = dt.datetime.now(dt.timezone.utc).date()
    wiki_limiter, sec_limiter = RateLimiter(50), RateLimiter(8)
    with build_session(user_agent("WIKIMEDIA_USER_AGENT", root)) as wiki_session:
        pages = []
        for page in ("List_of_S%26P_500_companies", "Nasdaq-100", "EURO_STOXX_50"):
            response = get_with_retries(
                wiki_session, f"https://en.wikipedia.org/wiki/{page}", wiki_limiter
            )
            response.raise_for_status()
            pages.append(response.text)
    with build_session(user_agent("SEC_USER_AGENT", root)) as sec_session:
        response = get_with_retries(
            sec_session, "https://www.sec.gov/files/company_tickers.json", sec_limiter
        )
        response.raise_for_status()
        ticker_ciks = {
            entry["ticker"]: cik10(entry["cik_str"]) for entry in response.json().values()
        }
    us = combine_us(
        parse_sp500(pages[0]),
        parse_nasdaq100(pages[1]),
        pd.read_csv(directory / "us_extras.csv"),
        ticker_ciks,
        snapshot_date,
    )
    if us["cik"].isna().any():
        raise ValueError("SEC ticker map did not resolve every US member CIK")
    eu = parse_eurostoxx50(pages[2])
    eu["index_membership"] = "SX5E"
    extra = pd.read_csv(directory / "eu_extras.csv")
    extra["index_membership"] = "EXTRA"
    eu = pd.concat([eu, extra], ignore_index=True)
    eu["symbol"] = eu["symbol"].str.strip().str.upper()
    for symbol, group in eu.groupby("symbol", sort=False):
        eu.loc[eu["symbol"] == symbol, "index_membership"] = "|".join(
            dict.fromkeys(group["index_membership"])
        )
    eu = eu.groupby("symbol", sort=False, as_index=False).first()
    eu = eu.assign(pool="eu_equity", currency="EUR", cik=None, snapshot_date=snapshot_date)
    crypto = crypto.assign(symbol=crypto[symbol_column].str.strip().str.upper())
    crypto = crypto.rename(columns={"category": "sector"})
    crypto = crypto.assign(
        pool="crypto",
        currency="USD",
        country=None,
        cik=None,
        index_membership="CRYPTO_TOP",
        snapshot_date=snapshot_date,
    )
    output = table_frame(
        "universe_member",
        [*us.to_dict("records"), *eu.to_dict("records"), *crypto.to_dict("records")],
    )
    write_table(output, "universe_member", root, as_of)
    return output
