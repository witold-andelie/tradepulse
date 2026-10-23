"""Parquet I/O with contract validation (task A7)."""

from __future__ import annotations

import datetime as dt
import os
import tempfile
from pathlib import Path

import pandas as pd

from tradepulse.contracts import assert_table, table_path


def write_table(
    df: pd.DataFrame, name: str, root: Path | None = None, as_of: dt.date | None = None
) -> Path:
    """Validate df with tradepulse.contracts.assert_table(df, name, as_of) and only then write it
    to tradepulse.contracts.table_path(name, root), creating parent folders. Write to a temporary
    file first and rename, so a crash never leaves a half-written table. Return the path.
    Invalid data -> ContractError and nothing is written.
    """
    assert_table(df, name, as_of=as_of)
    path = table_path(name, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".parquet", delete=False) as file:
            temporary = Path(file.name)
        df.to_parquet(temporary, index=False)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def read_table(name: str, root: Path | None = None) -> pd.DataFrame:
    """Read the parquet table written by write_table. Missing file -> FileNotFoundError."""
    return pd.read_parquet(table_path(name, root))
