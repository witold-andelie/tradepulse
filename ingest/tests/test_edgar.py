import pandas as pd
import pytest

from ingest.edgar import (acceptance_to_utc, cik10, find_exhibit_url, html_to_text, parse_companyfacts,
                          parse_submissions)
from tradepulse.contracts import validate_table


def test_cik10():
    assert cik10(320193) == "0000320193"
    assert cik10("66740") == "0000066740"


@pytest.mark.parametrize("raw, expected", [
    ("2025-08-05T16:05:12.000Z", "2025-08-05 20:05:12"),  # EDT, UTC-4
    ("2025-01-30T16:30:00.000Z", "2025-01-30 21:30:00"),  # EST, UTC-5
])
def test_acceptance_to_utc_reads_eastern_clock_time(raw, expected):
    assert acceptance_to_utc(raw) == pd.Timestamp(expected, tz="UTC")


def test_parse_submissions(fixture_json):
    df = parse_submissions(fixture_json("submissions.json"), symbol="AAA")
    assert validate_table(df, "filing") == []
    assert list(df["accession_number"]) == [
        "0000320193-25-000012", "0000320193-25-000070", "0000320193-25-000071"]
    by_acc = df.set_index("accession_number")
    first = by_acc.loc["0000320193-25-000071"]
    assert first["cik"] == "0000320193"
    assert first["items"] == "2.02,9.01"
    assert first["acceptance_datetime"] == pd.Timestamp("2025-08-05 20:05:12", tz="UTC")
    assert first["primary_doc_url"] == (
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000071/aaa-20250805.htm")
    assert pd.isna(by_acc.loc["0000320193-25-000070", "items"])
    assert "4" not in set(df["form"])
    assert df["acceptance_datetime"].is_monotonic_increasing


def test_parse_companyfacts(fixture_json):
    df = parse_companyfacts(fixture_json("companyfacts.json"), symbol="AAA")
    assert validate_table(df, "fundamental_fact") == []
    assert set(df["tag"]) == {"EarningsPerShareDiluted", "EntityCommonStockSharesOutstanding"}
    eps = df[df["tag"] == "EarningsPerShareDiluted"]
    assert len(eps) == 3  # the exact duplicate is dropped, the re-filed prior-year value is kept
    shares = df[df["tag"] == "EntityCommonStockSharesOutstanding"].iloc[0]
    assert pd.isna(shares["period_start"])
    assert shares["unit"] == "shares"
    assert (df["cik"] == "0000320193").all()


def test_find_exhibit_url(fixture_text):
    html = fixture_text("filing_index.html")
    assert find_exhibit_url(html) == (
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000071/aaa-ex991.htm")
    assert find_exhibit_url(html, "8-K") == (
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000071/aaa-20250805.htm")
    assert find_exhibit_url(html, "EX-10.1") is None


def test_html_to_text():
    html = ("<html><head><style>p{color:red}</style></head><body><p>Demand&nbsp;&nbsp;exceeds\n"
            "supply.</p><script>var x = 1;</script><p>Q3 &amp; FY</p></body></html>")
    assert html_to_text(html) == "Demand exceeds supply. Q3 & FY"
    assert html_to_text("<p>abcdef</p>", max_chars=3) == "abc"
