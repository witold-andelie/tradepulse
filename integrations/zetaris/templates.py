"""Allow-listed SQL templates (task D2).

The LLM never writes SQL. Agents choose a template name and parameters; this module validates
every parameter against its declared type and renders literal SQL that both Spark SQL (Zetaris)
and DuckDB accept.

Template files live in integrations/zetaris/templates/<name>.sql. The header declares the
parameters, one comment line each:

    -- param: <name> <type>

Types:
    symbol   ^[A-Z0-9][A-Z0-9.^=-]{0,19}$   rendered as a quoted string
    symbols  non-empty list of `symbol`, max 600 rendered as ('A', 'B', ...)
    pool     one of us_equity, eu_equity, crypto, reference
    date     ISO date (datetime.date or 'YYYY-MM-DD') rendered as DATE 'YYYY-MM-DD'
    int      Python int in [0, 100000]
    tag      ^[A-Za-z][A-Za-z0-9]{0,99}$  (XBRL concept name) rendered as a quoted string
    series   ^[A-Z0-9_]{1,40}$ rendered as a quoted string

Placeholders in the body: `:name` for parameters and `{{table:<table_name>}}` for lake tables.
The adapter supplies a table resolver (Zetaris: TRADEPULSE_LAKE.<table>; DuckDB: a view name).
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Callable

from tradepulse.contracts import table_names

from .client import ensure_single_statement

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_PARAM = re.compile(r"--\s*param:\s*([a-z_][a-z0-9_]*)\s+(\w+)\s*")
_SYMBOL = re.compile(r"[A-Z0-9][A-Z0-9.^=-]{0,19}")


class TemplateError(ValueError):
    """Unknown template, missing or extra parameter, or a parameter that fails validation."""


def list_templates() -> list[str]:
    """Sorted names of the .sql files in TEMPLATE_DIR (without extension)."""
    return sorted(path.stem for path in TEMPLATE_DIR.glob("*.sql"))


def _source(name: str) -> str:
    if not isinstance(name, str) or name not in list_templates():
        raise TemplateError("Unknown template")
    return (TEMPLATE_DIR / f"{name}.sql").read_text(encoding="utf-8")


def declared_params(name: str) -> dict[str, str]:
    """{param_name: type} parsed from the template header. Unknown template -> TemplateError."""
    result: dict[str, str] = {}
    for line in _source(name).splitlines():
        if not line.strip():
            continue
        if not line.lstrip().startswith("--"):
            break
        match = _PARAM.fullmatch(line.strip())
        if match:
            param, kind = match.groups()
            if param in result:
                raise TemplateError(f"Duplicate parameter: {param}")
            result[param] = kind
        elif line.lstrip().startswith("-- param:"):
            raise TemplateError("Invalid parameter declaration")
    return result


def _literal(name: str, kind: str, value: object) -> str:
    if kind == "symbols":
        if isinstance(value, list) and 1 <= len(value) <= 600:
            return "(" + ", ".join(_literal(name, "symbol", v) for v in value) + ")"
    elif kind == "int":
        if type(value) is int and 0 <= value <= 100000:
            return str(value)
    elif kind == "date":
        if type(value) is dt.date:
            return f"DATE '{value.isoformat()}'"
        if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            try:
                return f"DATE '{dt.date.fromisoformat(value).isoformat()}'"
            except ValueError:
                pass
    elif isinstance(value, str):
        valid = (
            (kind == "symbol" and _SYMBOL.fullmatch(value))
            or (kind == "pool" and value in {"us_equity", "eu_equity", "crypto", "reference"})
            or (kind == "tag" and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,99}", value))
            or (kind == "series" and re.fullmatch(r"[A-Z0-9_]{1,40}", value))
        )
        if valid:
            return f"'{value}'"
    raise TemplateError(f"Invalid parameter: {name} ({kind})")


def render(name: str, params: dict, table: Callable[[str], str]) -> str:
    """Validate params against declared_params(name) and return the SQL text.

    - Missing or extra parameters -> TemplateError.
    - A value that fails its type check -> TemplateError naming the parameter. Never escape your
      way around a failed check: reject it.
    - `{{table:x}}` is replaced by table(x), and x must be a table in contracts/tables.
    - Comment lines (starting with --) are removed. The result is a single statement with no
      trailing semicolon.
    """
    declared = declared_params(name)
    if not isinstance(params, dict) or params.keys() != declared.keys():
        raise TemplateError("Missing or extra parameters")
    literals = {param: _literal(param, kind, params[param]) for param, kind in declared.items()}
    sql = "\n".join(line for line in _source(name).splitlines()
                    if not line.lstrip().startswith("--"))
    known_tables = set(table_names())

    def resolve(match: re.Match) -> str:
        table_name = match.group(1)
        if table_name not in known_tables:
            raise TemplateError(f"Unknown table: {table_name}")
        resolved = table(table_name)
        if not isinstance(resolved, str) or not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*", resolved
        ):
            raise TemplateError(f"Invalid table identifier: {table_name}")
        return resolved

    sql = re.sub(r"\{\{table:([a-z_][a-z0-9_]*)\}\}", resolve, sql)

    def parameter(match: re.Match) -> str:
        param = match.group(1)
        if param not in literals:
            raise TemplateError(f"Undeclared parameter: {param}")
        return literals[param]

    sql = re.sub(r":([a-z_][a-z0-9_]*)", parameter, sql)
    if "{{" in sql or "}}" in sql:
        raise TemplateError("Unresolved table placeholder")
    try:
        return ensure_single_statement(sql)
    except ValueError:
        raise TemplateError("Template must contain one statement") from None
