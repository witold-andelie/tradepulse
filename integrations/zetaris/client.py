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

import math
import hashlib
import os
import re
import uuid
from urllib.parse import urlsplit

import pandas as pd
import requests


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
    _DEFAULT_QUERY_LIMIT = 50_000
    _DEFAULT_MAX_ROWS = 500_000
    _DEFAULT_MAX_REQUESTS = 4

    def __init__(self, rest_url: str, api_key: str, org_id: str, timeout_s: float = 120.0,
                 session=None) -> None:
        parsed = urlsplit(rest_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Zetaris REST URL must be an HTTP(S) URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Zetaris REST URL must not contain credentials, a query or a fragment")
        if not isinstance(api_key, str) or not api_key:
            raise ValueError("Zetaris API key must not be empty")
        if not isinstance(org_id, str) or not re.fullmatch(r"[0-9]+", org_id):
            raise ValueError("Zetaris organisation id must be numeric")
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("Timeout must be finite and positive")
        self.rest_url = rest_url.rstrip("/")
        self._api_key = api_key
        self.org_id = org_id
        self.timeout_s = timeout_s
        self._session = session if session is not None else requests.Session()
        self._query_limit = self._DEFAULT_QUERY_LIMIT
        self._max_rows = self._DEFAULT_MAX_ROWS
        self._max_requests = self._DEFAULT_MAX_REQUESTS
        self._page_size = 1000
        self._max_pages = 512
        self._api_mode = "direct"
        self._engine_id: str | None = None
        self._request_observer = None
        self._page_observer = None

    @classmethod
    def from_env(cls) -> "ZetarisClient":
        """Read ZETARIS_REST_URL, ZETARIS_API_KEY and ZETARIS_ORG_ID. A missing value raises a
        ZetarisError naming the variable (never its value)."""
        api_mode = os.environ.get("ZETARIS_API_MODE", "direct")
        if api_mode not in {"direct", "proxy"}:
            raise ZetarisError("ZETARIS_API_MODE must be direct or proxy")
        url_name = "ZETARIS_BASE_URL" if api_mode == "proxy" else "ZETARIS_REST_URL"
        required = (url_name, "ZETARIS_API_KEY", "ZETARIS_ORG_ID")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            raise ZetarisError("Missing Zetaris configuration: " + ", ".join(missing))
        try:
            timeout_s = _positive_float_env("ZETARIS_TIMEOUT_S", 120.0)
            client = cls(*(os.environ[name] for name in required), timeout_s=timeout_s)
            if api_mode == "proxy" and urlsplit(client.rest_url).path not in {"", "/"}:
                raise ValueError("ZETARIS_BASE_URL must be an origin without a path")
            client._api_mode = api_mode
            client._engine_id = os.environ.get("ZETARIS_ENGINE_ID") or None
            client._query_limit = _positive_int_env(
                "ZETARIS_QUERY_LIMIT", cls._DEFAULT_QUERY_LIMIT
            )
            client._max_rows = _positive_int_env("ZETARIS_MAX_ROWS", cls._DEFAULT_MAX_ROWS)
            client._max_requests = _positive_int_env(
                "ZETARIS_MAX_REQUESTS", cls._DEFAULT_MAX_REQUESTS
            )
            client._page_size = _positive_int_env("ZETARIS_PAGE_SIZE", 1000)
            client._max_pages = _positive_int_env("ZETARIS_MAX_PAGES", 512)
        except ValueError as error:
            raise ZetarisError(str(error)) from None
        if client._query_limit > client._max_rows:
            raise ZetarisError("ZETARIS_QUERY_LIMIT must not exceed ZETARIS_MAX_ROWS")
        if client._page_size > client._max_rows or client._max_pages > 2000:
            raise ZetarisError("Zetaris paging settings exceed the configured work bounds")
        return client

    def execute(self, sql: str) -> pd.DataFrame:
        """Run one statement (ensure_single_statement) and return parse_response(...)."""
        statement = ensure_single_statement(sql)
        limit = self._query_limit
        query_like = bool(re.match(r"\s*(?:SELECT|WITH)\b", statement, re.IGNORECASE))

        for _ in range(self._max_requests):
            payload = self._request(statement, limit)
            frame = self.parse_response(payload)
            if not query_like:
                return frame
            if len(frame.columns) == 0:
                raise ZetarisError("Zetaris query response is missing its result schema")

            total = _response_total(payload)
            if total is not None and total <= len(frame):
                return frame
            if total is None and len(frame) < limit:
                return frame
            if total is not None and total > self._max_rows:
                raise ZetarisError(
                    f"Zetaris result has {total} rows, above the configured maximum "
                    f"of {self._max_rows}"
                )

            target = max(limit * 2, total or 0)
            next_limit = min(self._max_rows, target)
            if next_limit <= limit:
                raise ZetarisError(
                    "Zetaris result may be truncated at the configured maximum row limit"
                )
            limit = next_limit

        raise ZetarisError("Zetaris result did not complete within the bounded request limit")

    def _request(self, sql: str, limit: int):
        request_id = str(uuid.uuid4())
        body = {
            "queryId": str(uuid.uuid4()),
            "sql": sql,
            "source": "SqlEditor",
            "limit": limit,
        }
        endpoint = "/sql-editor/sqls/run"
        if self._api_mode == "proxy":
            endpoint = "/api/proxy/sql-editor/sqls/run-query"
            body = {"sql": sql, "limit": limit}
            if self._engine_id is not None:
                body["engineId"] = self._engine_id
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "X-Org-ID": self.org_id,
            "X-Request-ID": request_id,
            "Content-Type": "application/json",
        }
        try:
            response = self._session.post(
                f"{self.rest_url}{endpoint}",
                json=body,
                headers=headers,
                timeout=self.timeout_s,
                allow_redirects=False,
            )
        except Exception as error:
            raise ZetarisError(f"Zetaris request failed ({type(error).__name__})") from None
        if not 200 <= response.status_code < 300:
            detail = _safe_detail(getattr(response, "text", ""), self._api_key)
            suffix = f": {detail}" if detail else ""
            raise ZetarisError(f"Zetaris returned HTTP {response.status_code}{suffix}")
        try:
            payload = response.json()
        except ValueError:
            if not getattr(response, "content", b""):
                return None
            raise ZetarisError("Zetaris returned invalid JSON") from None
        if self._request_observer is not None:
            self._request_observer({
                "sql_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
                "requested_limit": limit,
                "returned_rows": len(self.parse_response(payload)),
                "api_total": _response_total(payload),
            })
        return payload

    @staticmethod
    def parse_response(payload) -> pd.DataFrame:
        """Turn the JSON body of a query response into a DataFrame (all values as returned)."""
        if payload is None:
            return pd.DataFrame()
        if not isinstance(payload, dict):
            raise ZetarisError("Zetaris response must be an object")
        if payload.get("error"):
            raise ZetarisError("Zetaris response reported an error")

        data = payload.get("data", payload.get("rows"))
        if isinstance(data, dict):
            return ZetarisClient.parse_response(data)
        if data is None:
            return pd.DataFrame()
        if not isinstance(data, list):
            raise ZetarisError("Zetaris response data must be a list")
        if not data:
            headers = _response_headers(payload)
            return pd.DataFrame(columns=headers or None)
        if all(isinstance(row, dict) for row in data):
            return pd.DataFrame(data)
        if any(not isinstance(row, (list, tuple)) for row in data):
            raise ZetarisError("Zetaris response rows must be arrays or objects")

        headers = _response_headers(payload)
        if headers is None:
            raise ZetarisError("Zetaris response is missing column headers")
        if any(len(row) != len(headers) for row in data):
            raise ZetarisError("Zetaris response row width does not match its headers")
        return pd.DataFrame(data, columns=headers)


def _response_headers(payload: dict) -> list[str] | None:
    raw = next(
        (payload.get(key) for key in ("headers", "columns", "header", "fields")
         if payload.get(key) is not None),
        None,
    )
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ZetarisError("Zetaris response headers must be a list")
    headers: list[str] = []
    for item in raw:
        if isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            name = item.get("name") or item.get("field") or item.get("column")
        else:
            name = None
        if not isinstance(name, str) or not name:
            raise ZetarisError("Zetaris response contains an invalid column header")
        headers.append(name)
    if len(set(headers)) != len(headers):
        raise ZetarisError("Zetaris response contains duplicate column headers")
    return headers


def _response_total(payload) -> int | None:
    if not isinstance(payload, dict):
        return None
    if "total" not in payload:
        return _response_total(payload.get("data"))
    value = payload["total"]
    if isinstance(value, bool):
        raise ZetarisError("Zetaris response total must be a non-negative integer")
    if not isinstance(value, (str, int)) or not re.fullmatch(r"[0-9]+", str(value)):
        raise ZetarisError("Zetaris response total must be a non-negative integer") from None
    total = int(value)
    if total < 0:
        raise ZetarisError("Zetaris response total must be a non-negative integer")
    return total


def _positive_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be a positive integer") from None
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _positive_float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"{name} must be finite and positive") from None
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def _safe_detail(text: str, secret: str) -> str:
    # The server body can include credentials, personal addresses or SQL text. HTTP status
    # is enough to diagnose the transport; never echo untrusted response text into logs.
    return "server detail [REDACTED]" if text else ""
