import datetime as dt

import pandas as pd
import pytest

from ingest.universe import combine_us, eu_yahoo_symbol, parse_nasdaq100, parse_sp500, to_yahoo_symbol_us
from tradepulse.contracts import validate_table


@pytest.mark.parametrize("raw, expected", [
    ("AAPL", "AAPL"), ("BRK.B", "BRK-B"), ("BF.B", "BF-B"), (" msft ", "MSFT"),
])
def test_to_yahoo_symbol_us(raw, expected):
    assert to_yahoo_symbol_us(raw) == expected


@pytest.mark.parametrize("ticker, exchange, expected", [
    ("SAP", "Xetra", "SAP.DE"),
    ("MC", "Euronext Paris", "MC.PA"),
    ("ASML", "Euronext Amsterdam", "ASML.AS"),
    ("ABI", "Euronext Brussels", "ABI.BR"),
    ("ISP", "Borsa Italiana", "ISP.MI"),
    ("ITX", "Bolsa de Madrid", "ITX.MC"),
    ("NOKIA", "Nasdaq Helsinki", "NOKIA.HE"),
    ("rya", "Euronext Dublin", "RYA.IR"),
])
def test_eu_yahoo_symbol(ticker, exchange, expected):
    assert eu_yahoo_symbol(ticker, exchange) == expected


def test_eu_yahoo_symbol_unknown_exchange_raises():
    with pytest.raises(ValueError):
        eu_yahoo_symbol("XYZ", "Moon Exchange")


def test_parse_sp500(fixture_text):
    df = parse_sp500(fixture_text("sp500.html")).set_index("symbol")
    assert set(df.index) == {"MMM", "AAPL", "BRK-B", "LOW"}
    assert df.loc["AAPL", "name"] == "Apple Inc."
    assert df.loc["AAPL", "sector"] == "Information Technology"
    assert df.loc["AAPL", "cik"] == "0000320193"
    assert df.loc["LOW", "cik"] == "0000060667"
    assert df.loc["AAPL", "wikipedia_title"] == "Apple_Inc."
    assert df.loc["LOW", "wikipedia_title"] == "Lowe's"


def test_parse_nasdaq100(fixture_text):
    df = parse_nasdaq100(fixture_text("nasdaq100.html")).set_index("symbol")
    assert set(df.index) == {"AAPL", "ZNDX"}
    assert df.loc["ZNDX", "sector"] == "Communication Services"
    assert pd.isna(df.loc["ZNDX", "wikipedia_title"])


def test_combine_us(fixture_text):
    sp = parse_sp500(fixture_text("sp500.html"))
    ndx = parse_nasdaq100(fixture_text("nasdaq100.html"))
    extras = pd.DataFrame({"symbol": ["ZEXT"], "name": ["Zed Extra Ltd"], "sector": ["Financials"],
                           "reason": ["crypto-linked"]})
    out = combine_us(sp, ndx, extras, {"ZNDX": "0000000123", "ZEXT": "0000000456"}, dt.date(2026, 10, 21))
    assert validate_table(out, "universe_member") == []
    out = out.set_index("symbol")
    assert len(out) == 6
    assert out.loc["AAPL", "index_membership"] == "SP500|NDX"
    assert out.loc["ZNDX", "index_membership"] == "NDX"
    assert out.loc["ZEXT", "index_membership"] == "EXTRA"
    assert out.loc["ZNDX", "cik"] == "0000000123"
    assert (out["pool"] == "us_equity").all()
    assert (out["currency"] == "USD").all()
    assert (out["country"] == "US").all()
