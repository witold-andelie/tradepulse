"""Compare every allow-listed template against the exact frozen sample on Zetaris and DuckDB."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

from tradepulse.contracts import REPO_ROOT

from integrations.environment import load_private_env
from .adapter import DuckDBAdapter, ZetarisAdapter
from .client import ZetarisClient, ZetarisError
from .templates import declared_params, list_templates


def fixed_params(template: str, as_of: str) -> dict:
    # A fixed month exercises non-empty daily, macro and filing-text data. XBRL templates
    # intentionally retain every point-in-time fact up to as_of, as their SQL specifies.
    import datetime as dt

    end = dt.date.fromisoformat(as_of)
    values = {
        "symbol": "NVDA", "symbols": ["NVDA", "AAPL"], "pool": "us_equity",
        "start": (end - dt.timedelta(days=31)).isoformat(), "end": end.isoformat(),
        "tag": "EarningsPerShareDiluted", "series": "BAMLH0A0HYM2",
    }
    declared = declared_params(template)
    missing = declared.keys() - values.keys()
    if missing:
        raise ValueError(f"Parity parameters missing for {template}: {sorted(missing)}")
    return {name: values[name] for name in declared}


def check_parity(live, offline, as_of: str, *, on_case=None) -> list[dict]:
    results = []
    for template in list_templates():
        params = fixed_params(template, as_of)
        expected = offline.run(template, params)
        actual = live.run(template, params)
        result = {
            "template": template, "params": params,
            "duckdb_rows": len(expected.df), "zetaris_rows": len(actual.df),
            "duckdb_sha256": expected.rows_sha256, "zetaris_sha256": actual.rows_sha256,
            "match": expected.rows_sha256 == actual.rows_sha256,
        }
        results.append(result)
        if on_case is not None:
            on_case(result)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-root", type=Path, default=REPO_ROOT / "data" / "sample")
    parser.add_argument("--env-file", type=Path, action="append", default=[])
    parser.add_argument("--report", type=Path,
                        help="new diagnostic JSON file under ignored runs/; contains no raw data or credentials")
    args = parser.parse_args(argv)
    for path in args.env_file:
        load_private_env(path.expanduser())
    manifest = json.loads((args.sample_root / "manifest.json").read_text(encoding="utf-8"))
    report_path = args.report.resolve() if args.report else None
    if report_path is not None:
        if not report_path.is_relative_to(REPO_ROOT / "runs"):
            raise ValueError("Choose a diagnostic report under runs/")
        if report_path.exists():
            raise FileExistsError("Choose a new report; preserve previous parity evidence")
    client = ZetarisClient.from_env()
    requests, pages, cases = [], [], []
    client._request_observer = requests.append
    client._page_observer = pages.append
    request_cursor = page_cursor = 0

    def emit(result):
        nonlocal request_cursor, page_cursor
        receipt = {**result, "transport_requests": requests[request_cursor:],
                   "pages": pages[page_cursor:]}
        cases.append(receipt)
        request_cursor, page_cursor = len(requests), len(pages)
        print(json.dumps(result, sort_keys=True))
        sys.stdout.flush()

    report = {"as_of": manifest["as_of"], "cases": cases,
              "runtime": {"python": sys.version.split()[0], "duckdb": duckdb.__version__,
                          "pandas": pd.__version__, "api_mode": client._api_mode,
                          "query_limit": client._query_limit, "page_size": client._page_size,
                          "max_pages": client._max_pages, "max_rows": client._max_rows}}
    try:
        results = check_parity(ZetarisAdapter(client), DuckDBAdapter(args.sample_root),
                               manifest["as_of"], on_case=emit)
    except Exception as error:
        report.update({"status": "failed", "failure_type": type(error).__name__,
                       "failed_template": list_templates()[len(cases)]
                       if len(cases) < len(list_templates()) else None,
                       "pending_requests": requests[request_cursor:],
                       "pending_pages": pages[page_cursor:]})
        if isinstance(error, ZetarisError):
            report["failure_detail"] = str(error)
        if report_path is not None:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "failed", "failure_type": type(error).__name__,
                          "completed_templates": len(cases)}))
        return 1
    matched = sum(result["match"] for result in results)
    report.update({"status": "ok" if matched == len(results) else "failed",
                   "matched": matched, "total": len(results)})
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok" if matched == len(results) else "failed",
                      "matched": matched, "total": len(results)}))
    return 0 if matched == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
