"""Read config/tradepulse.toml. Parameters are never hard-coded elsewhere."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "tradepulse.toml"

POOLS = ("us_equity", "eu_equity", "crypto")


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("rb") as fh:
        return tomllib.load(fh)


def pool_config(pool: str) -> dict[str, Any]:
    if pool not in POOLS:
        raise KeyError(f"unknown pool {pool!r}; expected one of {POOLS}")
    return load_config()["pools"][pool]
