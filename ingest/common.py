"""Shared typed frames, configuration and reporting for ingestion."""

from __future__ import annotations

import datetime as dt
import os
import re
from pathlib import Path

import pandas as pd

from tradepulse.config import load_config
from tradepulse.contracts import REPO_ROOT, load_table_spec


class ConfigurationError(ValueError):
    """A safe-to-display configuration error containing no secret values."""


def frame(rows, name):
    spec = load_table_spec(name)
    result = pd.DataFrame(rows, columns=[c["name"] for c in spec["columns"]])
    for c in spec["columns"]:
        key, kind = c["name"], c["dtype"]
        if kind == "date":
            result[key] = pd.to_datetime(result[key])
        elif kind == "datetime":
            result[key] = pd.to_datetime(result[key], utc=True)
        elif kind == "int":
            result[key] = pd.to_numeric(result[key], errors="raise").astype("Int64")
        elif kind == "float":
            result[key] = pd.to_numeric(result[key], errors="raise").astype(float)
        elif kind == "string":
            result[key] = result[key].astype("string")
    return result


def window_start(as_of):
    cfg = load_config()["backtest"]
    return as_of - dt.timedelta(days=cfg["window_days"] + cfg["warmup_days"])


def _local_setting(name):
    """Read local settings without caching contact details in process environment."""
    path = REPO_ROOT / ".env"
    local = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.removeprefix("export ").split("=", 1)
            local[key.strip()] = value.strip().strip("\"'")
    return os.environ.get(name, local.get(name, ""))


def environment(name):
    """Require a non-placeholder contact identity without exposing its value."""
    value = _local_setting(name)
    contact = re.search(r"[^\s()<>@]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,63})", value)
    domain = contact.group(1).lower() if contact else ""
    placeholder = domain in {"example.com", "example.org", "example.net"} or domain.endswith(
        (".invalid", ".test", ".example", ".localhost")
    )
    if (
        not value.strip()
        or not contact
        or placeholder
        or not value.isascii()
        or "\n" in value
        or "\r" in value
    ):
        raise ConfigurationError(f"Set a real contact User-Agent in {name}; no value was logged")
    return value


def report(df, filename, root=None):
    path = Path(root or REPO_ROOT) / "data/lake/_reports" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def showcase():
    edges = pd.read_csv(REPO_ROOT / "config/graph/seed_edges.csv")
    return tuple(sorted(set(edges.src_symbol) | set(edges.dst_symbol)))


def before_cutoff(df, name, as_of):
    """Filter all information timestamps, preserving bookkeeping timestamps."""
    keep = pd.Series(True, index=df.index)
    for c in load_table_spec(name)["columns"]:
        key = c["name"]
        if key in ("snapshot_date", "ingested_at", "fetched_at"):
            continue
        if c["dtype"] == "date":
            keep &= df[key].isna() | (df[key] <= pd.Timestamp(as_of))
        elif c["dtype"] == "datetime":
            end = pd.Timestamp(as_of, tz="UTC") + pd.Timedelta(days=1)
            keep &= df[key].isna() | (df[key] < end)
    return df.loc[keep].reset_index(drop=True)
