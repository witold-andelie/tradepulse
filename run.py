"""Command-line entry point.

    py -3 run.py --as-of 2026-10-21 --pools us_equity crypto --tickers NVDA --horizon 5 --top-k 5
    py -3 run.py --serve            # HTTP API on 0.0.0.0:8000

Exit codes: 0 ok, 2 request rejected by the guard, 1 run failed.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
