"""Command line: py -3 -m ingest <command> [--as-of YYYY-MM-DD]."""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path
from zipfile import BadZipFile

from tradepulse.contracts import table_names, validate_table


def _validate_all(as_of: dt.date | None) -> int:
    from ingest.lake import read_table

    failures = 0
    for name in table_names():
        try:
            df = read_table(name)
        except FileNotFoundError:
            print(f"[missing] {name}")
            failures += 1
            continue
        errors = validate_table(df, name, as_of=as_of)
        if df.empty:
            errors.append(f"{name}: table is empty")
        print(f"[{'ok' if not errors else 'FAIL'}] {name}: {len(df)} rows")
        for e in errors:
            print(f"    {e}")
        failures += bool(errors)
    print("all tables valid" if not failures else f"{failures} table(s) missing or invalid")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ingest", description="Build the TradePulse data lake.")
    parser.add_argument(
        "command",
        choices=[
            "universe",
            "prices",
            "pageviews",
            "filings",
            "texts",
            "macro",
            "validate",
            "sample",
            "audit",
            "handoff",
            "package",
            "verify-package",
            "config",
            "smoke",
            "diagnose",
            "crypto-research",
            "timezone",
            "sectors",
            "crypto-verify",
            "news-probe",
            "coverage",
            "news-report",
            "all",
        ],
    )
    parser.add_argument("--as-of", type=dt.date.fromisoformat, default=None)
    parser.add_argument("--provider", choices=["wikipedia", "sec", "wikimedia", "yahoo", "fred"])
    parser.add_argument("--symbol", choices=["NVDA", "AMD", "COHR"])
    parser.add_argument("--output", type=Path, help="New private ZIP destination for package")
    parser.add_argument("--archive", type=Path, help="Existing private ZIP for verify-package")
    parser.add_argument("--allow-source-exceptions", action="store_true")
    args = parser.parse_args(argv)
    as_of = args.as_of or dt.datetime.now(dt.UTC).date()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.command in ("package", "verify-package"):
        import json

        from ingest.handoff import package_lake, verify_package

        if args.command == "package" and (args.output is None or args.as_of is None):
            parser.error("package requires --as-of and --output")
        if args.command == "verify-package" and args.archive is None:
            parser.error("verify-package requires --archive")
        try:
            result = (
                package_lake(as_of, args.output, allow_source_exceptions=args.allow_source_exceptions)
                if args.command == "package" else verify_package(args.archive)
            )
        except (OSError, ValueError, KeyError, BadZipFile) as exc:
            print(f"[FAIL] private handoff: {type(exc).__name__}; no upload occurred")
            return 1
        print(json.dumps(result, indent=2))
        return 0

    from ingest import edgar, macro, pageviews, prices, sample, universe

    if args.command == "news-report":
        from ingest.news_probe import summarize_news_probe

        result = summarize_news_probe(as_of)
        print(
            result[
                [
                    "symbol",
                    "status",
                    "rows",
                    "first",
                    "last",
                    "calendar_day_coverage",
                    "missing_calendar_days",
                ]
            ].to_string(index=False)
        )
        return 0 if result.status.eq("YES").all() else 1

    if args.command == "coverage":
        import pandas as pd

        from ingest.lake import read_table

        members = read_table("universe_member")
        refs = pd.DataFrame({"pool": "reference", "symbol": prices.REFERENCE_SYMBOLS})
        prices.write_coverage(
            read_table("price_bar"), pd.concat([members[["pool", "symbol"]], refs]), as_of
        )
        print("Coverage report recomputed from existing price data")
        return 0

    if args.command == "news-probe":
        from ingest.news_probe import fetch_news_probe

        result = fetch_news_probe(as_of, selected_symbol=args.symbol)
        return 0 if result.status.eq("YES").all() else 1

    if args.command == "crypto-verify":
        from ingest.crypto import fetch_crypto_verification

        result = fetch_crypto_verification(as_of)
        print(
            f"Verified crypto assets: {len(result)}; article coverage {result.wikipedia_title.notna().mean():.1%}"
        )
        return 0

    if args.command == "sectors":
        sectors = universe.fetch_gics_sectors()
        print(f"Issuer sector source: {len(sectors)} equities; GICS labels validated")
        return 0

    if args.command == "timezone":
        from tradepulse.contracts import table_path

        if table_path("filing").exists():
            result = edgar.verify_saved_timestamps(as_of)
            print(result.to_string(index=False))
            return 0
        from ingest.common import environment
        from ingest.net import RateLimiter, build_session

        with build_session(environment("SEC_USER_AGENT")) as session:
            limiter = RateLimiter(2)
            payload = edgar.fetch_sec(
                session, limiter, "https://data.sec.gov/submissions/CIK0000320193.json"
            ).json()
            try:
                edgar.fetch_timezone_checks(session, limiter, payload)
            except ValueError:
                print(
                    "[BLOCKED] SEC timezone comparison disagrees or is incomplete; see edgar_timezone.csv"
                )
                return 1
        print("Three real SEC timezone comparisons passed")
        return 0

    if args.command == "crypto-research":
        from ingest.crypto import fetch_crypto_research

        result = fetch_crypto_research(as_of)
        print(f"Researched {len(result)} source-backed candidates; see crypto_candidates.csv")
        return 0

    if args.command == "diagnose":
        from ingest.diagnostics import fetch_diagnostics

        print(fetch_diagnostics(as_of).to_string(index=False))
        return 0

    if args.command in ("config", "smoke"):
        from ingest.preflight import configuration_status, smoke

        result = (
            configuration_status()
            if args.command == "config"
            else smoke(as_of, provider=args.provider)
        )
        print(result.to_string(index=False))
        return 0 if result.status.eq("PASS").all() else 1

    steps = {
        "universe": lambda: universe.run(as_of),
        "prices": lambda: prices.run(as_of),
        "pageviews": lambda: pageviews.run(as_of),
        "filings": lambda: edgar.run_filings(as_of),
        "texts": lambda: edgar.run_texts(as_of),
        "macro": lambda: macro.run(as_of),
    }
    if args.command == "validate":
        return _validate_all(args.as_of)
    if args.command == "sample":
        try:
            if _validate_all(as_of):
                print("[FAIL] sample: source lake does not validate for the requested as_of")
                return 1
            print(sample.cut_sample())
            return 0
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            print(
                f"[FAIL] sample: {type(exc).__name__}; build and validate the complete lake first"
            )
            return 1
    if args.command in ("audit", "handoff"):
        from ingest.quality import audit

        result = audit(as_of)
        print(result.to_string(index=False))
        return 0 if result.passed.all() else 1
    order = list(steps) if args.command == "all" else [args.command]
    failed = []
    for step in order:
        print(f"--> {step}")
        # Do not accidentally consume a stale universe/filing after an upstream failure.
        dependencies = {
            "prices": ["universe"],
            "pageviews": ["universe"],
            "filings": ["universe"],
            "texts": ["filings", "universe"],
        }
        if any(dep in failed for dep in dependencies.get(step, [])):
            print(f"[blocked] {step}: upstream step failed")
            failed.append(step)
            continue
        try:
            steps[step]()
        except Exception as exc:  # Isolate stages and redact provider exceptions.
            # Provider exceptions may include sensitive request headers. Do not print them.
            print(f"[FAIL] {step}: {type(exc).__name__}; check provider configuration and reports")
            from ingest.common import ConfigurationError
            from ingest.net import IngestHTTPError

            if isinstance(exc, ConfigurationError):
                print(str(exc))
            elif isinstance(exc, IngestHTTPError):
                print(f"Provider HTTP status: {exc.status_code}; {exc!s}")
            failed.append(step)
    if args.command == "all":
        validation = _validate_all(as_of)
        return 1 if failed or validation else 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
