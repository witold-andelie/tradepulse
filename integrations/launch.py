"""Load explicitly selected private settings and run the unchanged TradePulse CLI/API."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from .environment import load_private_env


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--env-file", type=Path, action="append", default=[])
    args, remaining = parser.parse_known_args(argv)
    for path in args.env_file:
        load_private_env(path.expanduser())
    if os.environ.get("LLM_PROVIDER") != "glm":
        raise ValueError("This launcher requires the explicit hosted GLM profile")
    os.environ["SAMPLE_MODE"] = "false"
    os.environ["ENGINES_ENABLED"] = "true"
    from run import main as run_main

    return run_main(remaining)


if __name__ == "__main__":
    raise SystemExit(main())
