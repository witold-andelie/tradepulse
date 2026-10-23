"""Zetaris REST client (task D3). Reference: refs/zetaris/repo/scripts/zetaris_sql.py.

Facts from the Zetaris getting-started docs:
- REST base: ZETARIS_REST_URL (default http://localhost:8888/api/v1.0).
- Every request sends Authorization: Bearer <ZETARIS_API_KEY>, the organisation id and a fresh
  UUID in X-Request-ID.
- One SQL statement per call.
- Values may come back as strings, including decimals in exponent form ("1.5E+2").
- REST tables re-fetch upstream on every query; CACHE TABLE helps.
Record one real response (secrets removed) as tests/fixtures/zetaris_query_response.json and test
parse_response against it.
"""

from __future__ import annotations

import pandas as pd


class ZetarisError(RuntimeError):
    """A Zetaris call failed. The message must never contain the API key."""


def ensure_single_statement(sql: str) -> str:
    """Strip whitespace and one trailing ';'. Raise ValueError if another ';' remains outside
    single-quoted string literals (a second statement)."""
    result = sql.strip()
    if result.endswith(";"):
        result = result[:-1].rstrip()
    if not result:
        raise ValueError("SQL statement is empty")
    quote: str | None = None
    line_comment = False
    block_comment = False
    skip = False
    for index, char in enumerate(result):
        if skip:
            skip = False
            continue
        following = result[index + 1:index + 2]
        if line_comment:
            line_comment = char != "\n"
        elif block_comment:
            if char == "*" and following == "/":
                block_comment = False
                skip = True
        elif quote:
            if char == quote:
                if following == quote:
                    skip = True
                else:
                    quote = None
        elif char in "'\"":
            quote = char
        elif char == "-" and following == "-":
            line_comment = True
            skip = True
        elif char == "/" and following == "*":
            block_comment = True
            skip = True
        elif char == ";":
            raise ValueError("Only one SQL statement is allowed")
    if quote or block_comment:
        raise ValueError("Unterminated SQL literal or comment")
    return result


def coerce_frame(df: pd.DataFrame, dtypes: dict[str, str]) -> pd.DataFrame:
    """Convert string columns to contract dtypes ('float', 'int', 'date', 'datetime', 'string',
    'bool'). Columns not in dtypes are left as they are. Numeric strings may use exponent form.
    Empty strings and 'null' become missing. 'datetime' becomes tz-aware UTC."""
    result = df.copy()
    for column, kind in dtypes.items():
        if column not in result:
            continue
        values = result[column].map(
            lambda v: None if isinstance(v, str) and v.strip().lower() in {"", "null"} else v
        )
        if kind == "float":
            converted = pd.to_numeric(values, errors="raise").astype(float)
        elif kind == "int":
            converted = pd.to_numeric(values, errors="raise").astype("Int64")
        elif kind == "date":
            converted = pd.to_datetime(values, format="mixed", errors="raise").dt.normalize()
            if converted.dt.tz is not None:
                raise ValueError(f"Date column must be timezone-naive: {column}")
        elif kind == "datetime":
            converted = pd.to_datetime(values, format="mixed", errors="raise", utc=True)
        elif kind == "string":
            converted = values.astype("string")
        elif kind == "bool":
            def boolean(value):
                if pd.isna(value):
                    return pd.NA
                if isinstance(value, str):
                    value = value.strip().lower()
                if value in (True, 1, "true", "1"):
                    return True
                if value in (False, 0, "false", "0"):
                    return False
                raise ValueError(f"Invalid boolean in column: {column}")

            converted = values.map(boolean).astype("boolean")
        else:
            raise ValueError(f"Unknown dtype: {kind}")
        result[column] = converted
    return result


class ZetarisClient:
    def __init__(self, rest_url: str, api_key: str, org_id: str, timeout_s: float = 120.0,
                 session=None) -> None:
        raise NotImplementedError("D3")

    @classmethod
    def from_env(cls) -> "ZetarisClient":
        """Read ZETARIS_REST_URL, ZETARIS_API_KEY and ZETARIS_ORG_ID. A missing value raises a
        ZetarisError naming the variable (never its value)."""
        raise NotImplementedError("D3")

    def execute(self, sql: str) -> pd.DataFrame:
        """Run one statement (ensure_single_statement) and return parse_response(...)."""
        raise NotImplementedError("D3")

    @staticmethod
    def parse_response(payload) -> pd.DataFrame:
        """Turn the JSON body of a query response into a DataFrame (all values as returned)."""
        raise NotImplementedError("D3")
