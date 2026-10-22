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

from pathlib import Path
from typing import Callable

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


class TemplateError(ValueError):
    """Unknown template, missing or extra parameter, or a parameter that fails validation."""


def list_templates() -> list[str]:
    """Sorted names of the .sql files in TEMPLATE_DIR (without extension)."""
    raise NotImplementedError("D2")


def declared_params(name: str) -> dict[str, str]:
    """{param_name: type} parsed from the template header. Unknown template -> TemplateError."""
    raise NotImplementedError("D2")


def render(name: str, params: dict, table: Callable[[str], str]) -> str:
    """Validate params against declared_params(name) and return the SQL text.

    - Missing or extra parameters -> TemplateError.
    - A value that fails its type check -> TemplateError naming the parameter. Never escape your
      way around a failed check: reject it.
    - `{{table:x}}` is replaced by table(x), and x must be a table in contracts/tables.
    - Comment lines (starting with --) are removed. The result is a single statement with no
      trailing semicolon.
    """
    raise NotImplementedError("D2")
