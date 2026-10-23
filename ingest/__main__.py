"""Command line: py -3 -m ingest <command> [--as-of YYYY-MM-DD]."""

from __future__ import annotations

import argparse
import datetime as dt
import sys

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
            "all",
        ],
    )
    parser.add_argument("--as-of", type=dt.date.fromisoformat, default=None)
    args = parser.parse_args(argv)
    as_of = args.as_of or dt.datetime.now(dt.timezone.utc).date()

    from ingest import edgar, macro, pageviews, prices, sample, universe

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
        print(sample.cut_sample(showcase_symbols=edgar.showcase_symbols()))
        return 0
    order = list(steps) if args.command == "all" else [args.command]
    for step in order:
        print(f"--> {step}")
        steps[step]()
    return _validate_all(as_of) if args.command == "all" else 0


if __name__ == "__main__":
    sys.exit(main())
