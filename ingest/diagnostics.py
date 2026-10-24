"""Small provider diagnostics with sanitized public payload caches."""

from __future__ import annotations

import json

import pandas as pd
from bs4 import BeautifulSoup

from ingest import universe
from ingest.common import environment, report
from ingest.net import RateLimiter, build_session, get_with_retries
from tradepulse.contracts import REPO_ROOT


def fetch_diagnostics(as_of):
    cache = REPO_ROOT / "data/cache/diagnostics"
    cache.mkdir(parents=True, exist_ok=True)
    results = []
    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        limiter = RateLimiter(2)
        for path, parser in [
            ("List_of_NASDAQ-100_companies", universe.parse_nasdaq100),
        ]:
            response = get_with_retries(session, "https://en.wikipedia.org/wiki/" + path, limiter)
            row = {"source": path, "http_status": response.status_code, "detail": ""}
            if response.status_code == 200:
                (cache / (path + ".html")).write_text(response.text, encoding="utf-8")
                headers = [
                    [
                        cell.get_text(" ", strip=True)
                        for cell in table.find_all("tr")[0].find_all(["th", "td"])
                    ]
                    for table in BeautifulSoup(response.text, "lxml").find_all("table")
                    if table.find_all("tr")
                ]
                try:
                    data = parser(response.text)
                    data.to_csv(cache / (path + ".csv"), index=False)
                    row["detail"] = f"{len(data)} rows"
                except ValueError:
                    row["detail"] = json.dumps(headers, ensure_ascii=True)
            results.append(row)
        for name, url in [
            (
                "yahoo_chart",
                "https://query1.finance.yahoo.com/v8/finance/chart/SPY?range=5d&interval=1d",
            ),
            (
                "coingecko",
                "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false",
            ),
        ]:
            try:
                response = get_with_retries(session, url, limiter)
                row = {
                    "source": name,
                    "http_status": response.status_code,
                    "detail": "received_response",
                }
                if response.status_code == 200:
                    payload = response.json()
                    (cache / (name + ".json")).write_text(json.dumps(payload), encoding="utf-8")
                    row["detail"] = f"{len(payload)} items"
                results.append(row)
            except Exception as exc:  # noqa: BLE001 -- expose only error category and status
                results.append(
                    {
                        "source": name,
                        "http_status": getattr(exc, "status_code", None),
                        "detail": type(exc).__name__,
                    }
                )
    result = pd.DataFrame(results)
    report(result, "provider_diagnostics.csv")
    return result
