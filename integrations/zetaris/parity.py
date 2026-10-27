"""Compare every allow-listed template against the exact frozen sample on Zetaris and DuckDB."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tradepulse.contracts import REPO_ROOT

from .adapter import DuckDBAdapter, ZetarisAdapter
from .client import ZetarisClient
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


def check_parity(live, offline, as_of: str) -> list[dict]:
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
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-root", type=Path, default=REPO_ROOT / "data" / "sample")
    args = parser.parse_args(argv)
    manifest = json.loads((args.sample_root / "manifest.json").read_text(encoding="utf-8"))
    results = check_parity(
        ZetarisAdapter(ZetarisClient.from_env()), DuckDBAdapter(args.sample_root), manifest["as_of"],
    )
    for result in results:
        print(json.dumps(result, sort_keys=True))
    matched = sum(result["match"] for result in results)
    print(json.dumps({"status": "ok" if matched == len(results) else "failed",
                      "matched": matched, "total": len(results)}))
    return 0 if matched == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
