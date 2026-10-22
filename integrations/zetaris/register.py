"""Register the lake in Zetaris (task D1): py -3 -m integrations.zetaris.register sql/*.sql"""

from __future__ import annotations

import re

PLACEHOLDER = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")


def split_statements(text: str) -> list[str]:
    """Split a .sql file into statements on ';' outside single/double quotes. Drop '--' comment
    lines and empty statements. Each statement is returned stripped and without its ';'."""
    raise NotImplementedError("D1")


def substitute(statement: str, values: dict[str, str]) -> str:
    """Replace ${NAME} placeholders from values. Any placeholder without a value raises KeyError
    naming it, so nothing half-configured is ever sent."""
    raise NotImplementedError("D1")


def run_files(client, paths, values: dict[str, str]) -> list[tuple[str, str]]:
    """Execute every statement of every file in order. Returns (statement_head, status) pairs, where
    status is 'ok', 'exists' (error text matches 'already exists') or raises on any other error."""
    raise NotImplementedError("D1")
