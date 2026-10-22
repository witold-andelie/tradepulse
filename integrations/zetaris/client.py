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
    raise NotImplementedError("D3")


def coerce_frame(df: pd.DataFrame, dtypes: dict[str, str]) -> pd.DataFrame:
    """Convert string columns to contract dtypes ('float', 'int', 'date', 'datetime', 'string',
    'bool'). Columns not in dtypes are left as they are. Numeric strings may use exponent form.
    Empty strings and 'null' become missing. 'datetime' becomes tz-aware UTC."""
    raise NotImplementedError("D3")


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
