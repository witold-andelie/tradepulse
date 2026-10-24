"""SYNTHETIC offline regressions for the lead's post-merge ingestion fixes."""

import json

import pandas as pd
import pytest
import requests

from ingest import common, crypto, lake, prices, quality, sample
from ingest.tests.test_pipeline_regressions import AS_OF, synthetic_tables


@pytest.mark.parametrize("cached_coverage", [None, 0.0, 1.0])
@pytest.mark.parametrize("complete", [False, True])
def test_audit_uses_current_bars_instead_of_cached_coverage(
    tmp_path, cached_coverage, complete
):
    synthetic_tables(tmp_path)
    template = lake.read_table("price_bar", tmp_path)
    dates = pd.to_datetime(["2025-10-01", "2025-10-02"])
    benchmark = pd.concat(
        [template.assign(pool="reference", symbol="SPY", date=date) for date in dates],
        ignore_index=True,
    )
    member = pd.concat(
        [template.assign(date=date) for date in dates[: 2 if complete else 1]],
        ignore_index=True,
    )
    lake.write_table(pd.concat([member, benchmark], ignore_index=True), "price_bar", tmp_path)
    if cached_coverage is not None:
        common.report(
            pd.DataFrame(
                [{"pool": "us_equity", "symbol": "SYNTHETIC", "coverage": cached_coverage}]
            ),
            "prices_coverage.csv",
            tmp_path,
        )

    checks = quality.audit(AS_OF, tmp_path).set_index("check")

    assert bool(checks.loc["us_equity.price_coverage", "passed"]) is complete


def test_audit_rejects_missing_benchmark_calendar_even_with_good_cached_coverage(tmp_path):
    synthetic_tables(tmp_path)
    common.report(
        pd.DataFrame([{"pool": "us_equity", "symbol": "SYNTHETIC", "coverage": 1.0}]),
        "prices_coverage.csv",
        tmp_path,
    )

    checks = quality.audit(AS_OF, tmp_path).set_index("check")

    assert not checks.loc["us_equity.price_coverage", "passed"]
    assert "calendar" in checks.loc["us_equity.price_coverage", "actual"].lower()


def test_crypto_candidate_without_article_mapping_remains_an_explicit_gap(tmp_path, monkeypatch):
    reports = tmp_path / "data/lake/_reports"
    reports.mkdir(parents=True)
    cache = tmp_path / "data/cache/crypto"
    cache.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "id": "gatechain-token",
                "name": "SYNTHETIC Gate",
                "category": "exchange-token",
                "market_cap_rank": 20,
                "coingecko_symbol": "SYNTHETIC",
                "yahoo_candidates": json.dumps(
                    [{"symbol": "SYNTHETIC-USD", "name": "Gate USD"}]
                ),
            }
        ]
    ).to_csv(reports / "crypto_candidates.csv", index=False)

    class Response:
        status_code = 200

        def json(self):
            return {"query": {"pages": {}}}

    monkeypatch.setattr(crypto, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(crypto, "environment", lambda _: "SYNTHETIC")
    monkeypatch.setattr(crypto, "build_session", lambda _: requests.Session())
    monkeypatch.setattr(crypto, "get_with_retries", lambda *args, **kwargs: Response())
    monkeypatch.setattr(
        prices,
        "fetch_prices",
        lambda *args: pd.DataFrame(
            [{"symbol": "SYNTHETIC-USD", "Close": 1.0, "Adj Close": 1.0}]
        ),
    )

    # A tiny incomplete proposal must reach the normal acceptance guard, rather than KeyError.
    with pytest.raises(ValueError, match="Crypto proposal incomplete"):
        crypto.fetch_crypto_verification(AS_OF)

    proposed = pd.read_csv(cache / "proposed.csv")
    assert list(proposed.id) == ["gatechain-token"]
    assert proposed.wikipedia_title.isna().all()
    assert not (tmp_path / "config/universe/crypto.csv").exists()


@pytest.mark.parametrize("document_limit", [0, 1, 2])
def test_sample_document_limit_keeps_every_share_class(tmp_path, document_limit):
    source, destination = tmp_path / "source", tmp_path / "sample"
    synthetic_tables(source)
    template = lake.read_table("filing_text", source)
    exhibits = [
        template.assign(
            accession_number=f"SYNTHETIC-{number}",
            symbol=symbol,
            available_at=pd.Timestamp("2025-10-01", tz="UTC") + pd.Timedelta(hours=number),
        )
        for number in range(3)
        for symbol in ("SYNTHETIC-A", "SYNTHETIC-B")
    ]
    annual = template.assign(
        accession_number="SYNTHETIC-ANNUAL",
        symbol="SYNTHETIC-A",
        document_name="SYNTHETIC-annual.htm",
        document_type="10-K",
    )
    lake.write_table(pd.concat([*exhibits, annual], ignore_index=True), "filing_text", source)

    sample.cut_sample(source, destination, ("SYNTHETIC-A",), max_ex99_docs=document_limit)

    selected = lake.read_table("filing_text", destination)
    selected_exhibits = selected[selected.document_type == "EX-99.1"]
    expected_accessions = {f"SYNTHETIC-{number}" for number in range(3 - document_limit, 3)}
    assert set(selected_exhibits.accession_number) == expected_accessions
    assert len(selected_exhibits) == document_limit * 2
    assert all(
        set(group.symbol) == {"SYNTHETIC-A", "SYNTHETIC-B"}
        for _, group in selected_exhibits.groupby(["accession_number", "document_name"])
    )
    assert list(selected.loc[selected.document_type == "10-K", "accession_number"]) == [
        "SYNTHETIC-ANNUAL"
    ]
