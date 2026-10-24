"""Atomic Parquet I/O with contract validation."""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import tempfile
from pathlib import Path

import pandas as pd

from tradepulse.contracts import ContractError, assert_table, table_path


def write_table(
    df: pd.DataFrame, name: str, root: Path | None = None, as_of: dt.date | None = None
) -> Path:
    assert_table(df, name, as_of)
    if name == "filing_text":
        valid = (df.text.str.len() == df.char_count) & (df.char_count <= 200000)
        valid &= (
            df.text.map(lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()) == df.sha256
        )
        if not valid.all():
            raise ContractError("filing_text: invalid text length or SHA-256")
    if name == "pageview" and (df.views < 0).any():
        raise ContractError("pageview: negative view count")
    path = table_path(name, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{name}-", suffix=".parquet", dir=path.parent)
    os.close(fd)
    try:
        df.to_parquet(temporary, index=False, compression="zstd")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return path


def read_table(name: str, root: Path | None = None) -> pd.DataFrame:
    return pd.read_parquet(table_path(name, root))
