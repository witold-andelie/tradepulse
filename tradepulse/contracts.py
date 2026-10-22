"""Load and enforce the shared data contracts in contracts/.

Two kinds of contract exist:

* table contracts (contracts/tables/*.json) for parquet tables in the data lake;
  checked with validate_table / assert_table on a pandas DataFrame;
* the API contract (contracts/api/tradepulse.schema.json, JSON Schema 2020-12);
  checked with validate_payload.
"""

from __future__ import annotations

import datetime as dt
import json
import operator
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = REPO_ROOT / "contracts"
TABLES_DIR = CONTRACTS_DIR / "tables"
API_SCHEMA_PATH = CONTRACTS_DIR / "api" / "tradepulse.schema.json"

DTYPES = ("string", "float", "int", "bool", "date", "datetime")
_CHECK_RE = re.compile(r"^\s*(\w+)\s*(>=|<=|>|<|==)\s*(\w+|-?\d+(?:\.\d+)?)\s*$")
_OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt, "==": operator.eq}


class ContractError(ValueError):
    """Raised when data does not satisfy its contract."""


# --------------------------------------------------------------------------- tables


def table_names() -> list[str]:
    return sorted(p.stem for p in TABLES_DIR.glob("*.json"))


@lru_cache(maxsize=None)
def load_table_spec(name: str) -> dict[str, Any]:
    path = TABLES_DIR / f"{name}.json"
    if not path.exists():
        raise KeyError(f"no table contract named {name!r}; known: {table_names()}")
    return json.loads(path.read_text(encoding="utf-8"))


def table_path(name: str, root: Path | None = None) -> Path:
    """Where the table lives. root=None -> repo root (data/lake/...)."""
    rel = load_table_spec(name)["path"]
    return (root or REPO_ROOT) / rel


def _dtype_ok(series: pd.Series, dtype: str) -> bool:
    values = series.dropna()
    if dtype == "string":
        return pd.api.types.is_string_dtype(series) or values.map(lambda v: isinstance(v, str)).all()
    if dtype == "float":
        return pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series)
    if dtype == "int":
        return pd.api.types.is_integer_dtype(series)
    if dtype == "bool":
        return pd.api.types.is_bool_dtype(series)
    if dtype == "date":
        if pd.api.types.is_datetime64_any_dtype(series):
            if getattr(series.dt, "tz", None) is not None:
                return False
            return bool((values == values.dt.normalize()).all())
        return values.map(lambda v: isinstance(v, dt.date) and not isinstance(v, dt.datetime)).all()
    if dtype == "datetime":
        tz = getattr(series.dt, "tz", None) if pd.api.types.is_datetime64_any_dtype(series) else None
        return tz is not None and str(tz) == "UTC"
    raise ValueError(f"unknown dtype {dtype!r}")


def _check_mask(df: pd.DataFrame, expr: str) -> pd.Series:
    m = _CHECK_RE.match(expr)
    if not m:
        raise ValueError(f"unsupported check expression {expr!r}")
    left, op, right = m.groups()
    if right in df.columns:
        rhs = df[right]
    else:
        try:
            rhs = float(right)
        except ValueError:
            raise KeyError(right) from None
    return _OPS[op](df[left], rhs)


def validate_table(df: pd.DataFrame, name: str, as_of: dt.date | None = None) -> list[str]:
    """Return a list of human-readable violations (empty list = valid)."""
    spec = load_table_spec(name)
    errors: list[str] = []
    expected = [c["name"] for c in spec["columns"]]

    missing = [c for c in expected if c not in df.columns]
    extra = [c for c in df.columns if c not in expected]
    if missing:
        errors.append(f"{name}: missing columns {missing}")
    if extra:
        errors.append(f"{name}: unexpected columns {extra}")

    for col in spec["columns"]:
        cname = col["name"]
        if cname not in df.columns:
            continue
        series = df[cname]
        if not _dtype_ok(series, col["dtype"]):
            errors.append(f"{name}.{cname}: expected dtype {col['dtype']}, got {series.dtype}")
        if not col["nullable"] and series.isna().any():
            errors.append(f"{name}.{cname}: {int(series.isna().sum())} null values in non-nullable column")
        if "enum" in col:
            bad = sorted(set(series.dropna().astype(str)) - set(col["enum"]))
            if bad:
                errors.append(f"{name}.{cname}: values outside enum {bad[:5]}")

    pk = spec["primary_key"]
    if all(c in df.columns for c in pk):
        dup = df.duplicated(subset=pk, keep=False)
        if dup.any():
            errors.append(f"{name}: {int(dup.sum())} rows share a primary key {pk}")

    for expr in spec.get("checks", []):
        try:
            mask = _check_mask(df, expr)
        except KeyError:
            continue  # the missing column is already reported
        except TypeError:
            errors.append(f"{name}: check '{expr}' could not be evaluated (wrong dtypes)")
            continue
        bad = int((~mask.fillna(True)).sum())
        if bad:
            errors.append(f"{name}: {bad} rows violate check '{expr}'")

    if as_of is not None:
        cutoff = pd.Timestamp(as_of)
        for col in spec["columns"]:
            cname = col["name"]
            if cname not in df.columns or col["dtype"] not in ("date", "datetime"):
                continue
            if cname in ("ingested_at", "fetched_at", "snapshot_date"):
                continue  # bookkeeping times, not data times
            values = pd.to_datetime(df[cname])
            if col["dtype"] == "datetime":
                values = values.dt.tz_convert("UTC").dt.tz_localize(None)
                limit = cutoff + pd.Timedelta(days=1)
            else:
                limit = cutoff
            late = int((values > limit).sum())
            if late:
                errors.append(f"{name}.{cname}: {late} values after as_of {as_of}")

    return errors


def assert_table(df: pd.DataFrame, name: str, as_of: dt.date | None = None) -> None:
    errors = validate_table(df, name, as_of=as_of)
    if errors:
        raise ContractError("; ".join(errors))


# --------------------------------------------------------------------------- API payloads


@lru_cache(maxsize=1)
def load_api_schema() -> dict[str, Any]:
    return json.loads(API_SCHEMA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _validator(definition: str) -> Draft202012Validator:
    schema = load_api_schema()
    if definition not in schema["$defs"]:
        raise KeyError(f"no $defs entry named {definition!r}")
    sub = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"}
    return Draft202012Validator(sub, format_checker=FormatChecker())


def validate_payload(payload: Any, definition: str = "RunOutput") -> list[str]:
    """Validate a JSON-like object against one $defs entry. Empty list = valid."""
    errors = sorted(_validator(definition).iter_errors(payload), key=lambda e: list(e.path))
    return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors]


def assert_payload(payload: Any, definition: str = "RunOutput") -> None:
    errors = validate_payload(payload, definition)
    if errors:
        raise ContractError("; ".join(errors[:20]))
