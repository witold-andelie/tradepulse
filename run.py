"""Command-line entry point.

    py -3 run.py --as-of 2026-10-21 --pools us_equity crypto --tickers NVDA --horizon 5 --top-k 5
    py -3 run.py --serve            # HTTP API on 0.0.0.0:8000

Exit codes: 0 ok, 2 request rejected by the guard, 1 run failed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys

from tradepulse.config import load_config
from tradepulse.contracts import assert_payload
from tradepulse.guard import GuardRejection, guard_request
from tradepulse.store import RunStore
from tradepulse.trace import redact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TradePulse research or serve its HTTP API.")
    parser.add_argument("--serve", action="store_true", help="Serve the HTTP API on port 8000")
    parser.add_argument("--as-of", help="Decision date in YYYY-MM-DD format")
    parser.add_argument("--pools", nargs="+", default=None, help="Research pools")
    parser.add_argument("--tickers", nargs="*", default=None, help="Additional names to explain")
    parser.add_argument("--horizon", type=int, dest="horizon_days", help="Trading-day horizon")
    parser.add_argument("--top-k", type=int, help="Number of names to explain per end of each pool")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    try:
        if args.serve:
            import uvicorn

            uvicorn.run("tradepulse.api:app", host="0.0.0.0", port=8000)
            return 0
        cfg = load_config()
        raw = {key: value for key, value in vars(args).items()
               if key != "serve" and value is not None}
        raw.setdefault("pools", list(cfg["pools"]))
        today = dt.date.today()
        earliest = today - dt.timedelta(
            days=cfg["backtest"]["window_days"] + cfg["backtest"]["warmup_days"])
        try:
            request = guard_request(raw, today=today, earliest=earliest)
        except GuardRejection as exc:
            print(redact(f"Request rejected: {exc.code}: {exc.detail}"), file=sys.stderr)
            return 2
        from tradepulse.pipeline import run_pipeline

        output = run_pipeline(request)
        assert_payload(output, "RunOutput")
        RunStore().save(output)
        print(json.dumps(output, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as exc:
        print(f"Run failed: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
