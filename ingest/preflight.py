"""Redacted configuration checks and bounded provider smoke requests."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from ingest import edgar, macro, pageviews, prices, universe
from ingest.common import ConfigurationError, environment, report
from ingest.net import IngestHTTPError, RateLimiter, build_session, fetch_response
from tradepulse.contracts import REPO_ROOT, assert_table


def configuration_status():
    rows = []
    for name in ("SEC_USER_AGENT", "WIKIMEDIA_USER_AGENT"):
        try:
            environment(name)
            status = "PASS"
        except ConfigurationError:
            status = "BLOCKED"
        rows.append({"check": name, "status": status})
    crypto = pd.read_csv(REPO_ROOT / "config/universe/crypto.csv")
    for name, passed in (
        ("crypto_count_35_to_45", 35 <= len(crypto) <= 45),
        ("crypto_symbols_complete", crypto.symbol.notna().all()),
        ("crypto_titles_90_percent", crypto.wikipedia_title.notna().mean() >= 0.9),
        ("crypto_symbols_unique", not crypto.symbol.dropna().duplicated().any()),
    ):
        rows.append({"check": name, "status": "PASS" if passed else "BLOCKED"})
    return pd.DataFrame(rows)


def fetch_wikipedia_probe(as_of):
    paths = [
        ("List_of_S%26P_500_companies", universe.parse_sp500),
        ("Nasdaq-100", universe.parse_nasdaq100),
        ("EURO_STOXX_50", universe.parse_eurostoxx50),
    ]
    total = 0
    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        limiter = RateLimiter(2)
        for path, parse in paths:
            html = fetch_response(session, "https://en.wikipedia.org/wiki/" + path, limiter).text
            if path == "Nasdaq-100":
                from bs4 import BeautifulSoup

                if BeautifulSoup(html, "lxml").find("table", id="constituents") is None:
                    html = fetch_response(
                        session,
                        "https://en.wikipedia.org/wiki/List_of_NASDAQ-100_companies",
                        limiter,
                    ).text
            data = parse(html)
            if data.empty:
                raise ValueError("Empty constituent response")
            total += len(data)
    return total


def fetch_sec_probe(as_of):
    with build_session(environment("SEC_USER_AGENT")) as session:
        limiter = RateLimiter(2)
        payload = edgar.fetch_sec(
            session, limiter, "https://data.sec.gov/submissions/CIK0000320193.json"
        ).json()
        filings = edgar.parse_submissions(payload, "AAPL")
        facts_payload = edgar.fetch_sec(
            session, limiter, "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
        ).json()
        facts = edgar.parse_companyfacts(facts_payload, "AAPL")
        assert_table(filings, "filing")
        assert_table(facts, "fundamental_fact")
        if filings.empty or facts.empty:
            raise ValueError("Empty SEC response")
        recent = filings.sort_values("acceptance_datetime").iloc[-1]
        index = edgar.fetch_sec(
            session, limiter, edgar._index_url(recent.cik, recent.accession_number)
        ).text
        if not edgar.html_to_text(index):
            raise ValueError("Empty SEC archive response")
    return len(filings) + len(facts)


def fetch_pageviews_probe(as_of):
    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        payload = pageviews.fetch_pageviews(
            session,
            RateLimiter(2),
            "Apple_Inc.",
            as_of - dt.timedelta(days=7),
            as_of - dt.timedelta(days=1),
        )
    if payload is None:
        raise ValueError("Smoke article unavailable")
    data = pageviews.parse_pageviews(payload, "us_equity", "AAPL", "Apple_Inc.")
    assert_table(data, "pageview", as_of)
    if data.empty:
        raise ValueError("Empty pageview response")
    return len(data)


def fetch_yahoo_probe(as_of):
    raw = prices.fetch_prices(["SPY"], as_of - dt.timedelta(days=7), as_of)
    data = prices.to_price_bars(raw, "reference", {"SPY": "USD"}, pd.Timestamp.now(tz="UTC"))
    assert_table(data, "price_bar", as_of)
    if data.empty:
        raise ValueError("Empty Yahoo response")
    return len(data)


def fetch_fred_probe(as_of):
    # Restrict this smoke request to a short observation interval.
    url = macro.FRED_CSV.format(series_id="BAMLH0A0HYM2")
    url += f"&cosd={as_of - dt.timedelta(days=14)}&coed={as_of - dt.timedelta(days=1)}"
    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        text = fetch_response(session, url, RateLimiter(2)).text
    data = macro.parse_fred_csv(text, "BAMLH0A0HYM2")
    assert_table(data, "macro_point", as_of)
    if data.empty:
        raise ValueError("Empty FRED response")
    return len(data)


def smoke(as_of: dt.date, root: Path | None = None, provider: str | None = None):
    """No bulk acquisition; save only status, counts and sanitized error categories."""
    probes = [
        ("wikipedia", "WIKIMEDIA_USER_AGENT", fetch_wikipedia_probe),
        ("sec", "SEC_USER_AGENT", fetch_sec_probe),
        ("wikimedia", "WIKIMEDIA_USER_AGENT", fetch_pageviews_probe),
        ("yahoo", "WIKIMEDIA_USER_AGENT", fetch_yahoo_probe),
        ("fred", "WIKIMEDIA_USER_AGENT", fetch_fred_probe),
    ]
    selected_provider = provider
    rows = []
    for source_name, setting, probe in probes:
        if selected_provider and source_name != selected_provider:
            continue
        row = {
            "provider": source_name,
            "status": "BLOCKED",
            "rows": 0,
            "detail": "contact_configuration_required",
            "as_of": as_of.isoformat(),
        }
        try:
            environment(setting)
            count = probe(as_of)
            row.update(status="PASS", rows=count, detail="parsed_nonempty_response")
        except ConfigurationError:
            pass
        except Exception as exc:  # noqa: BLE001 -- continue independent probes without leaking headers
            detail = type(exc).__name__
            if isinstance(exc, IngestHTTPError) and exc.status_code is not None:
                detail += f":HTTP_{exc.status_code}"
            row.update(status="FAIL", detail=detail)
        rows.append(row)
    result = pd.DataFrame(rows)
    report(result, "provider_smoke.csv", root)
    return result
