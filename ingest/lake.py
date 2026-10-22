"""Parquet I/O with contract validation (task A7)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd


def write_table(df: pd.DataFrame, name: str, root: Path | None = None,
                as_of: dt.date | None = None) -> Path:
    """Validate df with tradepulse.contracts.assert_table(df, name, as_of) and only then write it
    to tradepulse.contracts.table_path(name, root), creating parent folders. Write to a temporary
    file first and rename, so a crash never leaves a half-written table. Return the path.
    Invalid data -> ContractError and nothing is written.
    """
    raise NotImplementedError("A7")


def read_table(name: str, root: Path | None = None) -> pd.DataFrame:
    """Read the parquet table written by write_table. Missing file -> FileNotFoundError."""
    raise NotImplementedError("A7")
