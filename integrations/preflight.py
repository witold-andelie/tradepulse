"""Check local sponsor services using explicitly selected private configuration files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from .environment import load_private_env
from .meterless.nightshift_smoke import main as nightshift_smoke
from .meterless.engines_client import EnginesClient
from .zetaris.smoke import main as zetaris_smoke


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, action="append", default=[])
    parser.add_argument("--service", choices=("zetaris", "nightshift", "engines", "all"),
                        default="all")
    args = parser.parse_args(argv)
    for path in args.env_file:
        load_private_env(path.expanduser())
    if args.service in {"zetaris", "all"}:
        zetaris_smoke()
    if args.service in {"engines", "all"}:
        import json

        client = EnginesClient(os.environ.get("ENGINES_URL") or "http://127.0.0.1:8790")
        health = client.health()
        if health.get("status") != "ok":
            raise RuntimeError("Engine health check failed")
        print(json.dumps(health))
    if args.service in {"nightshift", "all"}:
        nightshift_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
