"""Complete static lake-template results despite transport caps or ambiguous API totals.

The lake templates use simple projections and ORDER BY identifiers. Add server-computed count
and ordinal metadata for transport only; neither field crosses the adapter's contract boundary.
"""

from __future__ import annotations

import re

import pandas as pd

from .client import ZetarisError, ensure_single_statement

ROW = "__tp_row"
TOTAL = "__tp_total"
DEFAULT_PAGE_SIZE = 1000
DEFAULT_MAX_PAGES = 512


def _query_shape(sql: str) -> tuple[str, list[str], str]:
    statement = ensure_single_statement(sql)
    parts = re.split(r"\s+ORDER\s+BY\s+", statement, flags=re.IGNORECASE)
    if len(parts) != 2 or re.search(r"\b(?:LIMIT|OFFSET|FETCH|UNION)\b", statement, re.I):
        raise ZetarisError("Paged templates require one simple ORDER BY query")
    base, order = parts
    projection = re.match(r"SELECT\s+(.+?)\s+FROM\s+", base, re.I | re.S)
    if projection is None:
        raise ZetarisError("Paged template must select explicit columns")
    columns = [column.strip() for column in projection.group(1).split(",")]
    if (len(set(columns)) != len(columns) or
            any(not re.fullmatch(r"[a-z_][a-z0-9_]*", column, re.I) for column in columns) or
            {ROW, TOTAL} & {column.lower() for column in columns}):
        raise ZetarisError("Paged template projection must contain unique plain identifiers")
    terms, seen = [], set()
    for term in order.split(","):
        match = re.fullmatch(r"\s*([a-z_][a-z0-9_]*)(?:\s+(ASC|DESC))?\s*", term, re.I)
        if match is None or match.group(1) not in columns:
            raise ZetarisError("Paged template ordering must reference projected columns")
        column, direction = match.group(1), (match.group(2) or "ASC").upper()
        terms.append(f"{column} {direction} NULLS {'LAST' if direction == 'DESC' else 'FIRST'}")
        seen.add(column)
    # All result values break ties; fully identical rows remain interchangeable, not dropped.
    terms.extend(f"{column} ASC NULLS FIRST" for column in columns if column not in seen)
    return base, columns, ", ".join(terms)


def _integer_metadata(series: pd.Series) -> pd.Series:
    if series.map(lambda value: isinstance(value, bool)).any():
        raise ZetarisError("Invalid Zetaris paging metadata")
    try:
        values = pd.to_numeric(series, errors="raise").astype("Int64")
    except (TypeError, ValueError, OverflowError):
        raise ZetarisError("Invalid Zetaris paging metadata") from None
    if values.isna().any():
        raise ZetarisError("Missing Zetaris paging metadata")
    return values


def execute_template(client, sql: str) -> pd.DataFrame:
    base, columns, order = _query_shape(sql)
    page_size = getattr(client, "_page_size", DEFAULT_PAGE_SIZE)
    max_pages = getattr(client, "_max_pages", DEFAULT_MAX_PAGES)
    max_rows = getattr(client, "_max_rows", 500_000)
    frames, start, expected_total = [], 1, None
    for _ in range(max_pages):
        end = min(start + page_size - 1, max_rows)
        page_sql = (
            f"SELECT {', '.join(columns)}, {ROW}, {TOTAL} FROM ("
            f"SELECT tp_source.*, ROW_NUMBER() OVER (ORDER BY {order}) AS {ROW}, "
            f"COUNT(*) OVER () AS {TOTAL} FROM ({base}) tp_source"
            f") tp_page WHERE {ROW} BETWEEN {start} AND {end} ORDER BY {ROW}"
        )
        frame = client.execute(page_sql).copy()
        frame.columns = [str(column).lower() for column in frame.columns]
        if list(frame.columns) != columns + [ROW, TOTAL]:
            raise ZetarisError("Zetaris page columns do not match the rendered template")
        if frame.empty:
            if frames:
                raise ZetarisError("Zetaris paging returned an incomplete empty page")
            # A window count has no row on empty input. Verify emptiness with a scalar count.
            count = client.execute(f"SELECT COUNT(*) AS {TOTAL} FROM ({base}) tp_empty")
            if count.shape != (1, 1) or int(_integer_metadata(count.iloc[:, 0]).iloc[0]) != 0:
                raise ZetarisError("Zetaris returned no rows for a non-empty template")
            return frame[columns]
        ordinals = _integer_metadata(frame[ROW])
        totals = _integer_metadata(frame[TOTAL])
        total = int(totals.iloc[0])
        if not 1 <= total <= max_rows:
            raise ZetarisError("Zetaris template exceeds the configured maximum rows")
        if not totals.eq(total).all() or expected_total not in (None, total):
            raise ZetarisError("Zetaris result changed while paging")
        if (list(ordinals) != list(range(start, start + len(frame))) or
                int(ordinals.iloc[-1]) > min(end, total)):
            raise ZetarisError("Zetaris paging has missing or repeated row ordinals")
        observer = getattr(client, "_page_observer", None)
        if observer is not None:
            observer({"requested_start": start, "requested_end": end,
                      "received": len(frame), "window_total": total,
                      "ordinal_start": int(ordinals.iloc[0]),
                      "ordinal_end": int(ordinals.iloc[-1])})
        expected_total = total
        frames.append(frame[columns])
        start = int(ordinals.iloc[-1]) + 1
        if start == total + 1:
            result = pd.concat(frames, ignore_index=True)
            if len(result) != total:
                raise ZetarisError("Zetaris paging did not retrieve the complete template")
            return result
    raise ZetarisError("Zetaris template exceeded the bounded page-request limit")
