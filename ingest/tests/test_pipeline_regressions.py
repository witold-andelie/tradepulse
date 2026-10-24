"""SYNTHETIC offline regressions; generated frames are never production snapshots."""

import datetime as dt
import hashlib

import pandas as pd
import pytest
import requests

from ingest import common, edgar, lake, macro, net, pageviews, prices, sample, universe
from tradepulse.contracts import (
    ContractError,
    load_table_spec,
    table_names,
    table_path,
    validate_table,
)

AS_OF = dt.date(2025, 10, 3)


def synthetic_tables(root):
    """Build tiny labelled fixtures strictly inside pytest's temporary directory."""
    for name in table_names():
        row = {}
        for col in load_table_spec(name)["columns"]:
            kind = col["dtype"]
            row[col["name"]] = {
                "string": "SYNTHETIC",
                "float": 1.0,
                "int": 1,
                "date": pd.Timestamp("2025-10-01"),
                "datetime": pd.Timestamp("2025-10-01", tz="UTC"),
            }[kind]
            if "enum" in col:
                row[col["name"]] = col["enum"][0]
        if name == "filing_text":
            row.update(
                text="SYNTHETIC " * 60,
                char_count=600,
                sha256=hashlib.sha256(("SYNTHETIC " * 60).encode()).hexdigest(),
            )
        lake.write_table(common.frame([row], name), name, root, AS_OF)


@pytest.mark.parametrize("name", table_names())
def test_empty_frames_keep_contract_dtypes(name):
    assert validate_table(common.frame([], name), name) == []


def test_failed_parquet_write_preserves_previous_table(tmp_path, monkeypatch):
    synthetic_tables(tmp_path)
    path = table_path("macro_point", tmp_path)
    previous = path.read_bytes()

    def fail(*args, **kwargs):
        raise OSError("SYNTHETIC disk failure")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fail)
    with pytest.raises(OSError):
        lake.write_table(lake.read_table("macro_point", tmp_path), "macro_point", tmp_path)
    assert path.read_bytes() == previous
    assert not list(path.parent.glob(".macro_point-*"))


def test_as_of_rejection_does_not_replace_existing(tmp_path):
    synthetic_tables(tmp_path)
    path = table_path("macro_point", tmp_path)
    previous = path.read_bytes()
    data = lake.read_table("macro_point", tmp_path)
    data["date"] = pd.Timestamp("2030-01-01")
    with pytest.raises(ContractError):
        lake.write_table(data, "macro_point", tmp_path, AS_OF)
    assert path.read_bytes() == previous


def test_cutoff_uses_availability_not_only_observation_date():
    data = macro.parse_fred_csv("DATE,BAMLH0A0HYM2\n2025-10-02,3\n2025-10-03,4\n", "BAMLH0A0HYM2")
    actual = common.before_cutoff(data, "macro_point", AS_OF)
    assert list(actual.date) == [pd.Timestamp("2025-10-02")]


def test_sample_limits_text_and_preserves_other_tables(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "sample"
    synthetic_tables(source)
    original = lake.read_table("filing_text", source)
    texts = pd.concat(
        [
            original.assign(
                accession_number=f"SYNTHETIC-{i}",
                available_at=pd.Timestamp("2025-10-01", tz="UTC") + pd.Timedelta(hours=i),
            )
            for i in range(4)
        ],
        ignore_index=True,
    )
    lake.write_table(texts, "filing_text", source)
    counts = sample.cut_sample(source, destination, ("SYNTHETIC",), max_ex99_docs=2)
    assert counts["filing_text"] == 2
    assert list(lake.read_table("filing_text", destination).accession_number) == [
        "SYNTHETIC-3",
        "SYNTHETIC-2",
    ]
    for name in set(table_names()) - {"filing_text"}:
        pd.testing.assert_frame_equal(
            lake.read_table(name, source), lake.read_table(name, destination)
        )


def test_oversize_sample_never_replaces_existing(tmp_path, monkeypatch):
    source, destination = tmp_path / "source", tmp_path / "sample"
    synthetic_tables(source)
    sample.cut_sample(source, destination)
    before = table_path("macro_point", destination).read_bytes()
    monkeypatch.setattr(sample, "MAX_SAMPLE_MB", 0)
    with pytest.raises(RuntimeError):
        sample.cut_sample(source, destination)
    assert table_path("macro_point", destination).read_bytes() == before


def test_euro_actual_source_layout():
    html = """<table><tr><th>Ticker</th><th>Main listing</th><th>Name</th>
    <th>Registered office</th><th>Sector</th></tr><tr><td>SYN.MI</td><td>BIT: SYN</td>
    <td><a href="/wiki/Synthetic">Synthetic</a></td><td>Netherlands</td><td>Industrials</td></tr></table>"""
    result = universe.parse_eurostoxx50(html).iloc[0]
    assert result.symbol == "SYN.MI"
    assert result.country == "IT"
    assert result.wikipedia_title == "Synthetic"


def test_no_external_exhibit_url():
    html = '<table><tr><th>Document</th><th>Type</th></tr><tr><td><a href="https://other.invalid/x">x</a></td><td>EX-99.1</td></tr></table>'
    with pytest.raises(ValueError):
        edgar.find_exhibit_url(html)


def test_conflicting_fact_values_are_not_silently_dropped(fixture_json):
    payload = fixture_json("companyfacts.json")
    records = payload["facts"]["us-gaap"]["EarningsPerShareDiluted"]["units"]["USD/shares"]
    records.append(dict(records[0], val=999))
    with pytest.raises(ValueError, match="Conflicting"):
        edgar.parse_companyfacts(payload, "SYNTHETIC")


def test_timezone_mismatch_stops_live_filings(tmp_path, fixture_json, monkeypatch):
    payload = fixture_json("submissions.json")

    class Response:
        text = "<div>Accepted 2025-08-05 12:05:12</div>"

    monkeypatch.setattr(edgar, "fetch_sec", lambda *args: Response())
    with pytest.raises(ValueError, match="team-lead"):
        edgar.fetch_timezone_checks(None, None, payload, tmp_path)
    evidence = pd.read_csv(tmp_path / "data/lake/_reports/edgar_timezone.csv")
    assert len(evidence) == 3
    assert not evidence.matches.all()


def test_missing_user_agent_fails_without_network(monkeypatch, tmp_path):
    monkeypatch.setattr(common, "REPO_ROOT", tmp_path)
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with pytest.raises(ValueError, match="SEC_USER_AGENT"):
        common.environment("SEC_USER_AGENT")


def test_connection_failure_is_bounded_and_redacted():
    class Session:
        calls = 0

        def get(self, *args, **kwargs):
            self.calls += 1
            raise requests.ConnectionError("SYNTHETIC private-header")

    session = Session()
    limiter = net.RateLimiter(1000, sleep=lambda _: None)
    with pytest.raises(net.IngestHTTPError) as error:
        net.get_with_retries(
            session, "https://example.invalid/path?secret=SYNTHETIC", limiter, sleep=lambda _: None
        )
    assert session.calls == 3
    assert "private-header" not in str(error.value)
    assert "secret" not in str(error.value)


def test_pageview_run_records_404_and_missing_title(tmp_path, monkeypatch):
    synthetic_tables(tmp_path)
    members = lake.read_table("universe_member", tmp_path)
    members = pd.concat(
        [
            members.assign(symbol="SYNTHETIC-A", wikipedia_title="SYNTHETIC"),
            members.assign(symbol="SYNTHETIC-B", wikipedia_title=None),
        ],
        ignore_index=True,
    )
    lake.write_table(members, "universe_member", tmp_path)
    monkeypatch.setattr(pageviews, "environment", lambda _: "SYNTHETIC")
    monkeypatch.setattr(pageviews, "build_session", lambda _: requests.Session())
    monkeypatch.setattr(pageviews, "fetch_pageviews", lambda *args: None)
    result = pageviews.run(AS_OF, tmp_path)
    assert result.empty
    report = pd.read_csv(tmp_path / "data/lake/_reports/pageviews_missing.csv")
    assert set(report.reason) == {"HTTP_404", "missing_title"}


def test_download_flattens_batches_and_includes_end_date(monkeypatch):
    import yfinance

    calls = []

    def download(symbols, **kwargs):
        calls.append((symbols, kwargs))
        columns = pd.MultiIndex.from_product(
            [symbols, ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
        )
        return pd.DataFrame(1.0, columns=columns, index=pd.to_datetime(["2025-10-01"]))

    monkeypatch.setattr(yfinance, "download", download)
    monkeypatch.setattr(prices, "_yahoo_session", lambda: requests.Session())
    monkeypatch.setattr(prices.time, "sleep", lambda _: None)
    result = prices.fetch_prices([f"SYN{i}" for i in range(51)], dt.date(2025, 10, 1), AS_OF)
    assert len(result) == 51
    assert [len(c[0]) for c in calls] == [50, 1]
    assert calls[0][1]["end"] == "2025-10-04"
    assert calls[0][1]["auto_adjust"] is False


def test_complete_offline_pipeline_uses_contracts(tmp_path, monkeypatch, fixture_json):
    """SYNTHETIC provider responses exercise stage dependencies without real HTTP."""
    synthetic_tables(tmp_path)
    members = lake.read_table("universe_member", tmp_path).assign(
        symbol="SYNTHETIC", cik="0000320193", wikipedia_title="SYNTHETIC"
    )
    lake.write_table(members, "universe_member", tmp_path)
    for module in (prices, pageviews, macro, edgar):
        monkeypatch.setattr(module, "environment", lambda _: "SYNTHETIC")
    for module in (pageviews, macro, edgar):
        monkeypatch.setattr(module, "build_session", lambda _: requests.Session())

    def download(symbols, start, end):
        return pd.DataFrame(
            [
                dict(
                    symbol=s,
                    date=pd.Timestamp("2025-10-01"),
                    Open=10.0,
                    High=12.0,
                    Low=9.0,
                    Close=11.0,
                    **{"Adj Close": 11.0, "Volume": 100.0},
                )
                for s in symbols
            ]
        )

    monkeypatch.setattr(prices, "fetch_prices", download)
    prices.run(AS_OF, tmp_path)
    monkeypatch.setattr(pageviews, "fetch_pageviews", lambda *args: fixture_json("pageviews.json"))
    pageviews.run(AS_OF, tmp_path)
    monkeypatch.setattr(macro, "fetch_macro", lambda *args: "DATE,BAMLH0A0HYM2\n2025-10-01,3\n")
    macro.run(AS_OF, tmp_path)
    submissions = fixture_json("submissions.json")
    accepted = dict(
        zip(
            submissions["filings"]["recent"]["accessionNumber"],
            submissions["filings"]["recent"]["acceptanceDateTime"],
        )
    )

    class Response:
        def __init__(self, text="", payload=None):
            self.text, self.payload = text, payload

        def json(self):
            return self.payload

    def sec(session, limiter, url):
        if "/submissions/" in url:
            return Response(payload=submissions)
        if "/companyfacts/" in url:
            return Response(payload=fixture_json("companyfacts.json"))
        if url.endswith("-index.htm"):
            accession = url.rsplit("/", 1)[1].removesuffix("-index.htm")
            clock = accepted[accession].replace("T", " ")[:19]
            html = f'<div>Accepted {clock}</div><table><tr><th>Document</th><th>Type</th></tr><tr><td><a href="/Archives/SYNTHETIC.htm">release</a></td><td>EX-99.1</td></tr></table>'
            return Response(text=html)
        return Response(text="<p>" + "SYNTHETIC " * 100 + "</p>")

    monkeypatch.setattr(edgar, "fetch_sec", sec)
    edgar.run_filings(AS_OF, tmp_path)
    edgar.run_texts(AS_OF, tmp_path)
    for name in table_names():
        data = lake.read_table(name, tmp_path)
        assert not data.empty, name
        assert validate_table(data, name, AS_OF) == [], name
    from ingest.quality import audit

    checks = audit(AS_OF, tmp_path).set_index("check")
    assert checks.loc["texts.hashes", "passed"]
    assert checks.loc["edgar.timezone", "passed"]
    assert not checks.loc["us_equity.size", "passed"]
    assert not checks.passed.all()
    counts = sample.cut_sample(tmp_path, tmp_path / "offline", ("SYNTHETIC",))
    assert set(counts) == set(table_names())


def test_cli_continues_independent_macro_after_universe_failure(monkeypatch):
    from ingest import __main__ as cli

    called = []

    def fail(*args):
        called.append("universe")
        raise ValueError("SYNTHETIC failure")

    monkeypatch.setattr(universe, "run", fail)
    monkeypatch.setattr(macro, "run", lambda *args: called.append("macro"))
    monkeypatch.setattr(cli, "_validate_all", lambda *args: 1)
    assert cli.main(["all", "--as-of", "2025-10-03"]) == 1
    assert called == ["universe", "macro"]


def test_empty_source_cannot_be_published_as_sample(tmp_path):
    synthetic_tables(tmp_path / "source")
    lake.write_table(common.frame([], "filing"), "filing", tmp_path / "source")
    with pytest.raises(ValueError, match="empty"):
        sample.cut_sample(tmp_path / "source", tmp_path / "sample")
    assert not table_path("filing", tmp_path / "sample").exists()


def test_policy_session_limits_transport_and_sets_timeout(monkeypatch):
    limiter_calls, timeouts = [], []
    session = net.PolicySession()

    class Limiter:
        def wait(self):
            limiter_calls.append(True)

    session.limiter = Limiter()

    def send(self, request, **kwargs):
        timeouts.append(kwargs["timeout"])
        response = requests.Response()
        response.status_code = 200
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    session.get("https://synthetic.invalid/")
    assert limiter_calls == [True]
    assert timeouts == [30.0]


def test_yahoo_session_retries_posts_and_uses_supported_session(monkeypatch):
    from yfinance._http import is_supported_session

    calls = []

    def request(self, method, url, **kwargs):
        calls.append((method, kwargs["timeout"]))
        response = requests.Response()
        response.status_code = 503 if len(calls) < 3 else 200
        return response

    monkeypatch.setattr(requests.Session, "request", request)
    monkeypatch.setattr(prices, "environment", lambda _: "SYNTHETIC")
    monkeypatch.setattr(prices, "build_session", lambda _: net.PolicySession())
    monkeypatch.setattr(prices.time, "sleep", lambda _: None)
    with prices._yahoo_session() as session:
        assert is_supported_session(session)
        response = session.post("https://synthetic.invalid/", timeout=None)
    assert response.status_code == 200
    assert calls == [("POST", 30)] * 3


def test_hash_mismatch_rejected_before_write(tmp_path):
    synthetic_tables(tmp_path)
    original = table_path("filing_text", tmp_path).read_bytes()
    data = lake.read_table("filing_text", tmp_path)
    data["sha256"] = "0" * 64
    with pytest.raises(ContractError, match="SHA-256"):
        lake.write_table(data, "filing_text", tmp_path)
    assert table_path("filing_text", tmp_path).read_bytes() == original


@pytest.mark.parametrize("status", [403, 429, 503])
def test_sec_provider_blocks_are_not_treated_as_missing(monkeypatch, status):
    def fail(*args):
        raise net.IngestHTTPError("SYNTHETIC provider failure", status)

    monkeypatch.setattr(edgar, "fetch_sec", fail)
    with pytest.raises(net.IngestHTTPError):
        edgar.fetch_optional_sec(None, None, "https://synthetic.invalid/")


def test_sec_404_is_a_reportable_missing_document(monkeypatch):
    def missing(*args):
        raise net.IngestHTTPError("SYNTHETIC missing document", 404)

    monkeypatch.setattr(edgar, "fetch_sec", missing)
    assert edgar.fetch_optional_sec(None, None, "https://synthetic.invalid/") is None
