"""Yahoo's public daily chart transport, with source-native adjusted prices and session dates."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from urllib.parse import quote, urlencode

import pandas as pd

from ingest.common import environment
from ingest.net import IngestHTTPError, RateLimiter, build_session, get_with_retries
from tradepulse.contracts import REPO_ROOT

RAW_COLUMNS = ["symbol", "date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]


def parse_chart(payload, symbol):
    """Preserve the provider's OHLC/adjusted-close values; never infer adjusted prices."""
    chart = payload.get("chart", {})
    results = chart.get("result") or []
    if chart.get("error") or len(results) != 1:
        raise ValueError("Yahoo chart has no usable result")
    item = results[0]
    timestamps = item.get("timestamp") or []
    if not timestamps:
        return pd.DataFrame(columns=RAW_COLUMNS)
    timezone = item.get("meta", {}).get("exchangeTimezoneName")
    if not timezone:
        raise ValueError("Yahoo chart is missing the exchange timezone")
    indicators = item.get("indicators", {})
    quotes = (indicators.get("quote") or [{}])[0]
    adjusted = (indicators.get("adjclose") or [{}])[0].get("adjclose")
    arrays = {name.title(): quotes.get(name) for name in ("open", "high", "low", "close")}
    arrays["Adj Close"] = adjusted
    arrays["Volume"] = quotes.get("volume", [None] * len(timestamps))
    if any(values is None or len(values) != len(timestamps) for values in arrays.values()):
        raise ValueError("Yahoo chart price arrays are missing or misaligned")
    dates = pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(timezone)
    result = pd.DataFrame(arrays)
    result["date"] = dates.tz_localize(None).normalize()
    result["symbol"] = symbol
    return result[RAW_COLUMNS]


def fetch_public_prices(symbols, start, end):
    """Cache successful raw responses and enforce the same bounded HTTP policy as other sources."""
    if end < start:
        raise ValueError("Price window is reversed")
    symbols = list(dict.fromkeys(symbols))
    if not symbols:
        return pd.DataFrame(columns=RAW_COLUMNS)
    cache = REPO_ROOT / "data/cache/yahoo-chart"
    cache.mkdir(parents=True, exist_ok=True)
    params = {
        "period1": int(pd.Timestamp(start, tz="UTC").timestamp()),
        "period2": int(pd.Timestamp(end + dt.timedelta(days=1), tz="UTC").timestamp()),
        "interval": "1d",
        "events": "div,splits",
        "includeAdjustedClose": "true",
    }
    parts = []
    with build_session(environment("WIKIMEDIA_USER_AGENT")) as session:
        limiter = RateLimiter(2)
        for number, symbol in enumerate(symbols, 1):
            url = (
                "https://query1.finance.yahoo.com/v8/finance/chart/"
                + quote(symbol, safe="")
                + "?"
                + urlencode(params)
            )
            path = cache / (hashlib.sha256(url.encode()).hexdigest() + ".json")
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                data = parse_chart(payload, symbol)
            else:
                response = get_with_retries(session, url, limiter)
                if response.status_code != 200:
                    raise IngestHTTPError(
                        f"Yahoo public chart returned HTTP {response.status_code}",
                        response.status_code,
                    )
                payload = response.json()
                data = parse_chart(payload, symbol)
                path.write_text(json.dumps(payload), encoding="utf-8")
            parts.append(data[data.date.between(pd.Timestamp(start), pd.Timestamp(end))])
            if number % 50 == 0 or number == len(symbols):
                print(f"Yahoo public charts {number}/{len(symbols)}", flush=True)
    return pd.concat(parts, ignore_index=True)
