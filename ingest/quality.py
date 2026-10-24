"""Compute acceptance metrics and a reproducible Member D hand-off manifest."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import pandas as pd

from ingest.common import report
from ingest.lake import read_table
from ingest.prices import REFERENCE_SYMBOLS, requested_coverage
from tradepulse.contracts import REPO_ROOT, table_names, table_path, validate_table


def audit(as_of: dt.date, root: Path | None = None):
    tables, checks, manifest = {}, [], []
    contracts_valid = True

    def check(name, passed, actual):
        checks.append({"check": name, "passed": bool(passed), "actual": str(actual)})

    for name in table_names():
        path = table_path(name, root)
        if not path.exists():
            check(f"{name}.exists", False, "missing")
            contracts_valid = False
            continue
        data = read_table(name, root)
        tables[name] = data
        errors = validate_table(data, name, as_of)
        contracts_valid = contracts_valid and not errors
        check(
            f"{name}.contract",
            not errors and not data.empty,
            "; ".join(errors) or f"{len(data)} rows",
        )
        manifest.append(
            {
                "table": name,
                "rows": len(data),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "columns": list(data.columns),
            }
        )
    if len(tables) == len(table_names()) and contracts_valid:
        universe = tables["universe_member"]
        for pool, lower, upper in [
            ("us_equity", 500, 530),
            ("eu_equity", 50, 65),
            ("crypto", 35, 45),
        ]:
            members = universe[universe.pool == pool]
            check(f"{pool}.size", lower <= len(members) <= upper, len(members))
            titles = members.wikipedia_title.notna().mean()
            check(f"{pool}.titles", titles >= 0.9, titles)
            views = tables["pageview"]
            share = members.symbol.isin(views.loc[views.pool == pool, "symbol"]).mean()
            check(f"{pool}.pageview_members", share >= 0.9, share)
        us = universe[universe.pool == "us_equity"]
        check("us.cik", us.cik.notna().all(), int(us.cik.isna().sum()))
        bars = tables["price_bar"]
        reference = set(bars.loc[bars.pool == "reference", "symbol"])
        check("prices.references", set(REFERENCE_SYMBOLS) <= reference, sorted(reference))
        for pool in ["us_equity", "eu_equity", "crypto"]:
            required = universe.loc[universe.pool == pool, ["pool", "symbol"]]
            if required.empty:
                check(f"{pool}.price_coverage", False, "no members")
                continue
            try:
                values = requested_coverage(bars, required, as_of)
            except ValueError as exc:
                check(f"{pool}.price_coverage", False, str(exc))
                continue
            share = (values.coverage >= 0.95).mean()
            check(f"{pool}.price_coverage", share >= 0.95, share)
        filing = tables["filing"]
        from tradepulse.config import load_config

        start = pd.Timestamp(as_of) - pd.Timedelta(days=load_config()["backtest"]["window_days"])
        items = (
            filing["items"]
            .fillna("")
            .str.split(",")
            .map(lambda v: "2.02" in [x.strip() for x in v])
        )
        count = filing.loc[
            (filing.form == "8-K") & items & (filing.filing_date >= start), "symbol"
        ].nunique()
        check("filings.earnings_members", count >= 450, count)
        facts = tables["fundamental_fact"]
        count = facts.loc[facts.tag == "EarningsPerShareDiluted", "symbol"].nunique()
        check("facts.eps_members", count >= 450, count)
        texts = tables["filing_text"]
        hashes = texts.text.map(lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest())
        check("texts.hashes", (hashes == texts.sha256).all(), int((hashes != texts.sha256).sum()))
        check(
            "texts.lengths",
            ((texts.text.str.len() == texts.char_count) & (texts.char_count <= 200000)).all(),
            len(texts),
        )
        exhibits = texts[texts.document_type == "EX-99.1"]
        check(
            "texts.exhibit_size",
            not exhibits.empty and (exhibits.char_count > 500).all(),
            len(exhibits),
        )
        expected = set(
            zip(
                filing.loc[
                    (filing.form == "8-K") & items & (filing.filing_date >= start),
                    "accession_number",
                ],
                filing.loc[
                    (filing.form == "8-K") & items & (filing.filing_date >= start), "symbol"
                ],
            )
        )
        actual = set(zip(exhibits.accession_number, exhibits.symbol))
        check("texts.earnings_complete", expected <= actual, f"{len(expected - actual)} missing")
        exception_path = Path(root or REPO_ROOT) / "data/lake/_reports/filing_text_missing.csv"
        accounted = set()
        if exception_path.exists():
            exceptions = pd.read_csv(exception_path, dtype={"accession": str})
            required = {"policy", "index_verified", "index_url", "reason", "accession", "symbol"}
            if required <= set(exceptions.columns):
                approved = exceptions[
                    exceptions.policy.eq("approved_source_exception")
                    & exceptions.index_verified.eq(True)
                    & exceptions.reason.eq("missing_exhibit")
                    & exceptions.index_url.fillna("").str.startswith(
                        "https://www.sec.gov/Archives/"
                    )
                ]
                accounted = set(zip(approved.accession, approved.symbol))
        check(
            "texts.earnings_accounted_with_approved_exceptions",
            expected <= actual | accounted,
            f"{len(expected - actual)} missing; {len((expected - actual) & accounted)} approved source exceptions; "
            f"{len(expected - actual - accounted)} unresolved",
        )
    timezone_path = Path(root or REPO_ROOT) / "data/lake/_reports/edgar_timezone.csv"
    verified_path = timezone_path.with_name("edgar_timezone_verification.csv")
    if verified_path.exists():
        timezone_path = verified_path
    if timezone_path.exists():
        tz = pd.read_csv(timezone_path)
        check("edgar.timezone", len(tz) >= 3 and tz.matches.eq(True).all(), len(tz))
    else:
        check("edgar.timezone", False, "not verified")
    # Membership classification requires provenance, not a heuristic ticker blacklist.
    review_path = Path(root or REPO_ROOT) / "data/lake/_reports/crypto_review.json"
    reviewed = False
    if (
        review_path.exists()
        and "universe_member" in tables
        and not validate_table(tables["universe_member"], "universe_member", as_of)
    ):
        review = json.loads(review_path.read_text(encoding="utf-8"))
        members = tables["universe_member"]
        symbols = set(members.loc[members.pool == "crypto", "symbol"])
        reviewed_rows = review.get("assets", [])
        reviewed = (
            bool(review.get("source_url"))
            and bool(review.get("reviewed_at"))
            and {r.get("symbol") for r in reviewed_rows} == symbols
            and len(reviewed_rows) == len(symbols)
            and all(
                r.get("excluded_type") is False
                and r.get("yahoo_verified") is True
                and isinstance(r.get("market_cap_rank"), int)
                and r["market_cap_rank"] > 0
                for r in reviewed_rows
            )
        )
    check(
        "crypto.curated_review",
        reviewed,
        "Review evidence present" if reviewed else "Dated market-cap and exclusion review required",
    )
    sample_root = Path(root or REPO_ROOT) / "data/sample"
    sample_bytes = sum(p.stat().st_size for p in sample_root.rglob("*") if p.is_file())
    sample_complete = True
    for name in table_names():
        path = table_path(name, sample_root)
        if not path.exists():
            sample_complete = False
            continue
        data = read_table(name, sample_root)
        if data.empty or validate_table(data, name, as_of):
            sample_complete = False
    check("sample.complete", sample_complete, "Seven nonempty valid tables required")
    check("sample.size", sample_complete and sample_bytes < 25 * 1024 * 1024, sample_bytes)
    result = pd.DataFrame(checks)
    path = report(result, "acceptance.csv", root)
    path.with_name("handoff_manifest.json").write_text(
        json.dumps(
            {
                "as_of": as_of.isoformat(),
                "tables": manifest,
                "acceptance_passed": bool(result.passed.all()),
                "acceptance_with_approved_source_exceptions": bool(
                    result.loc[result.check != "texts.earnings_complete", "passed"].all()
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return result
