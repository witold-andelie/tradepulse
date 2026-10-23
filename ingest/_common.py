"""Shared configuration and contract-shaped frames for ingestion."""

from __future__ import annotations

import datetime as dt
import os
import tomllib
from pathlib import Path
from typing import Any

import pandas as pd

from tradepulse.contracts import REPO_ROOT, load_table_spec


def project_root(root: Path | None) -> Path:
    return Path(root) if root is not None else REPO_ROOT


def configuration(root: Path | None) -> dict[str, Any]:
    path = project_root(root) / "config" / "tradepulse.toml"
    with path.open("rb") as stream:
        return tomllib.load(stream)


def window_start(as_of: dt.date, root: Path | None, *, warmup: bool = True) -> dt.date:
    config = configuration(root)["backtest"]
    days = config["window_days"] + (config["warmup_days"] if warmup else 0)
    return as_of - dt.timedelta(days=days)


def user_agent(variable: str, root: Path | None = None) -> str:
    """Use the process environment, with a small, non-interpolating .env fallback.

    Only the two provider User-Agent settings are loaded; values are never logged.
    Shell expansion and command execution are deliberately unsupported.
    """
    path = project_root(root) / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            key, separator, value = line.removeprefix("export ").partition("=")
            if separator and key.strip() in {"SEC_USER_AGENT", "WIKIMEDIA_USER_AGENT"}:
                value = value.strip()
                if value[:1] in {"'", '"'} and value[-1:] == value[:1]:
                    value = value[1:-1]
                else:
                    value = value.split(" #", 1)[0].rstrip()
                os.environ.setdefault(key.strip(), value)
    return os.environ.get(variable, "")


def table_frame(name: str, rows: Any = ()) -> pd.DataFrame:
    """Build columns in contract order, including typed empty and nullable columns."""
    spec = load_table_spec(name)
    frame = pd.DataFrame(rows, columns=[column["name"] for column in spec["columns"]])
    for column in spec["columns"]:
        key, dtype = column["name"], column["dtype"]
        if dtype == "date":
            frame[key] = pd.to_datetime(frame[key])
        elif dtype == "datetime":
            frame[key] = pd.to_datetime(frame[key], utc=True)
        elif dtype == "int":
            frame[key] = frame[key].astype("Int64" if column["nullable"] else "int64")
        elif dtype == "float":
            frame[key] = pd.to_numeric(frame[key]).astype("float64")
        elif dtype == "string":
            frame[key] = frame[key].astype("string")
    return frame


def concat_tables(name: str, frames: list[pd.DataFrame]) -> pd.DataFrame:
    nonempty = [frame for frame in frames if not frame.empty]
    return table_frame(name, pd.concat(nonempty, ignore_index=True) if nonempty else ())


def report_path(root: Path | None, filename: str) -> Path:
    path = project_root(root) / "data" / "lake" / "_reports" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
