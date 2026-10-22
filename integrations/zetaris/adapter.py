"""Query adapters (task D2): one interface, two back ends that run the same templates.

- DuckDBAdapter: SAMPLE_MODE and local development, over the parquet lake.
- ZetarisAdapter: live mode, through ZetarisClient (REST).

Evidence produced by these adapters is re-run by the verifier, so results must be reproducible.
rows_sha256 must give the same hash for the same logical rows whatever the back end.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class QueryResult:
    template: str
    params: dict
    sql: str
    backend: str            # "duckdb" or "zetaris"
    df: pd.DataFrame = field(repr=False)
    rows_sha256: str
    elapsed_ms: int


def rows_sha256(df: pd.DataFrame) -> str:
    """Back-end independent hash of a result set.

    Canonical form:
    - Column names are lower-cased and kept in their given order.
    - Every value is normalised to text:
      - None/NaN/NaT -> null
      - numbers, including numeric strings such as "1.50" or "1.5E+2" -> format(float(v), ".10g")
      - dates -> YYYY-MM-DD
      - tz-aware timestamps -> UTC ISO 'YYYY-MM-DDTHH:MM:SSZ'
      - other values -> str
    - Each row is serialised as a JSON array. The rows are sorted, joined with '\\n', and the
      result is hashed with sha256 (hex).
    Row order and dtype differences must not change the hash.
    """
    raise NotImplementedError("D2")


class DuckDBAdapter:
    """Runs templates on parquet files under lake_root/data/lake (or data/sample/data/lake).
    Each lake table whose parquet file exists is exposed as a view with the table's own name;
    querying a missing table raises an error that names it."""

    backend = "duckdb"

    def __init__(self, lake_root: Path) -> None:
        raise NotImplementedError("D2")

    def run(self, template: str, params: dict) -> QueryResult:
        raise NotImplementedError("D2")


class ZetarisAdapter:
    """Runs templates through ZetarisClient against database TRADEPULSE_LAKE (configurable).
    Coerces result columns to the dtypes declared in contracts/tables when the column name is
    known, so DuckDB and Zetaris results compare equal."""

    backend = "zetaris"

    def __init__(self, client, database: str = "TRADEPULSE_LAKE") -> None:
        raise NotImplementedError("D3")

    def run(self, template: str, params: dict) -> QueryResult:
        raise NotImplementedError("D3")


def make_adapter(sample_mode: bool, lake_root: Path | None = None):
    """SAMPLE_MODE -> DuckDBAdapter on data/sample. Otherwise ZetarisAdapter configured from the
    environment. Never silently fall back from Zetaris to DuckDB in live mode: raise instead."""
    raise NotImplementedError("D3")
