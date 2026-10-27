"""Query adapters (task D2): one interface, two back ends that run the same templates.

- DuckDBAdapter: SAMPLE_MODE and local development, over the parquet lake.
- ZetarisAdapter: live mode, through ZetarisClient (REST).

Evidence produced by these adapters is re-run by the verifier, so results must be reproducible.
rows_sha256 must give the same hash for the same logical rows whatever the back end.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass, field
from numbers import Number
from pathlib import Path
from time import perf_counter

import duckdb
import pandas as pd

from tradepulse.contracts import load_table_spec, table_names, table_path

from .client import ZetarisClient, coerce_frame
from .paging import execute_template
from .templates import render


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
    def normalise(value: object) -> str | None:
        if pd.isna(value):
            return None
        if isinstance(value, dt.datetime):
            if value.tzinfo is not None:
                return value.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return value.date().isoformat()
        if isinstance(value, dt.date):
            return value.isoformat()
        if isinstance(value, Number) and not isinstance(value, bool):
            return format(float(value), ".10g")
        if isinstance(value, str) and re.fullmatch(
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value
        ):
            return format(float(value), ".10g")
        return str(value)

    columns = json.dumps([str(column).lower() for column in df.columns], ensure_ascii=False)
    rows = sorted(json.dumps([normalise(value) for value in row], ensure_ascii=False)
                  for row in df.itertuples(index=False, name=None))
    return hashlib.sha256((columns + "\n" + "\n".join(rows)).encode("utf-8")).hexdigest()


class DuckDBAdapter:
    """Runs templates on parquet files under lake_root/data/lake (or data/sample/data/lake).
    Each lake table whose parquet file exists is exposed as a view with the table's own name;
    querying a missing table raises an error that names it."""

    backend = "duckdb"

    def __init__(self, lake_root: Path) -> None:
        self.lake_root = Path(lake_root).resolve()
        self._connection = duckdb.connect(":memory:", config={
            "autoinstall_known_extensions": "false", "autoload_known_extensions": "false",
        })
        self._tables: set[str] = set()
        try:
            for name in table_names():
                path = table_path(name, root=self.lake_root)
                if path.is_file():
                    # A database-level view (not a connection-local relation view), so it is
                    # visible from the per-query cursors used in run().
                    escaped = path.as_posix().replace("'", "''")
                    self._connection.execute(
                        f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{escaped}')")
                    self._tables.add(name)
        except Exception:
            self._connection.close()
            raise

    def run(self, template: str, params: dict) -> QueryResult:
        started = perf_counter()
        used_tables: list[str] = []

        def table(name: str) -> str:
            if name not in self._tables:
                raise FileNotFoundError(f"Missing lake table: {name}")
            used_tables.append(name)
            return name

        saved_params = deepcopy(params)
        sql = render(template, saved_params, table)
        # One cursor per query: a DuckDB connection must not be shared across threads, and the
        # explanation graph runs evidence queries in parallel.
        with self._connection.cursor() as cursor:
            df = cursor.execute(sql).fetchdf()
        df = _coerce_result(df, used_tables)
        return QueryResult(template, saved_params, sql, self.backend, df, rows_sha256(df),
                           int((perf_counter() - started) * 1000))


class ZetarisAdapter:
    """Runs templates through ZetarisClient against database TRADEPULSE_LAKE (configurable).
    Coerces result columns to the dtypes declared in contracts/tables when the column name is
    known, so DuckDB and Zetaris results compare equal."""

    backend = "zetaris"

    def __init__(self, client, database: str = "TRADEPULSE_LAKE") -> None:
        if not isinstance(database, str) or not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*", database
        ):
            raise ValueError("Invalid Zetaris database identifier")
        self.client = client
        self.database = database

    def run(self, template: str, params: dict) -> QueryResult:
        started = perf_counter()
        used_tables: list[str] = []

        def table(name: str) -> str:
            used_tables.append(name)
            return f"{self.database}.{name}"

        saved_params = deepcopy(params)
        sql = render(template, saved_params, table)
        frame = execute_template(self.client, sql)
        columns = [str(column).lower() for column in frame.columns]
        if len(set(columns)) != len(columns):
            raise ValueError("Duplicate Zetaris result column names")
        frame = frame.copy()
        frame.columns = columns
        frame = _coerce_result(frame, used_tables)
        return QueryResult(
            template,
            saved_params,
            sql,
            self.backend,
            frame,
            rows_sha256(frame),
            int((perf_counter() - started) * 1000),
        )


def _coerce_result(frame: pd.DataFrame, used_tables: list[str]) -> pd.DataFrame:
    """Both backends must obey the same contract types before canonical result hashing."""
    dtypes: dict[str, str] = {}
    for table_name in used_tables:
        for column in load_table_spec(table_name)["columns"]:
            previous = dtypes.get(column["name"])
            if previous is not None and previous != column["dtype"]:
                raise ValueError(f"Conflicting contract dtype: {column['name']}")
            dtypes[column["name"]] = column["dtype"]
    return coerce_frame(frame, dtypes)


def make_adapter(sample_mode: bool, lake_root: Path | None = None):
    """SAMPLE_MODE -> DuckDBAdapter on data/sample. Otherwise ZetarisAdapter configured from the
    environment. Never silently fall back from Zetaris to DuckDB in live mode: raise instead."""
    if sample_mode:
        return DuckDBAdapter(lake_root or Path(__file__).resolve().parents[2] / "data" / "sample")
    return ZetarisAdapter(ZetarisClient.from_env())
