"""Register the lake in Zetaris (task D1): py -3 -m integrations.zetaris.register sql/*.sql"""

from __future__ import annotations

import argparse
import glob
import os
import re
from pathlib import Path

from .client import ZetarisClient, ensure_single_statement

PLACEHOLDER = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")


def split_statements(text: str) -> list[str]:
    """Split a .sql file into statements on ';' outside single/double quotes. Drop '--' comment
    lines and empty statements. Each statement is returned stripped and without its ';'."""
    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    line_comment = False
    block_comment = False
    skip = False
    for index, char in enumerate(text):
        if skip:
            skip = False
            continue
        following = text[index + 1:index + 2]
        if line_comment:
            if char == "\n":
                line_comment = False
                current.append("\n")
        elif block_comment:
            if char == "*" and following == "/":
                block_comment = False
                skip = True
        elif quote:
            current.append(char)
            if char == quote:
                if following == quote:
                    current.append(following)
                    skip = True
                else:
                    quote = None
        elif char in "'\"":
            quote = char
            current.append(char)
        elif char == "-" and following == "-":
            line_comment = True
            skip = True
            current.append(" ")
        elif char == "/" and following == "*":
            block_comment = True
            skip = True
            current.append(" ")
        elif char == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
    if quote or block_comment:
        raise ValueError("Unterminated SQL literal or comment")
    final = "".join(current).strip()
    if final:
        statements.append(final)
    return statements


def substitute(statement: str, values: dict[str, str]) -> str:
    """Replace ${NAME} placeholders from values. Any placeholder without a value raises KeyError
    naming it, so nothing half-configured is ever sent."""
    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in values or values[name] is None:
            raise KeyError(name)
        return values[name]

    return PLACEHOLDER.sub(replace, statement)


def run_files(client, paths, values: dict[str, str]) -> list[tuple[str, str]]:
    """Execute every statement of every file in order. Returns (statement_head, status) pairs, where
    status is 'ok', 'exists' (error text matches 'already exists') or raises on any other error."""
    statements = [ensure_single_statement(substitute(statement, values))
                  for path in paths
                  for statement in split_statements(Path(path).read_text(encoding="utf-8"))]
    results: list[tuple[str, str]] = []
    for statement in statements:
        try:
            client.execute(statement)
            status = "ok"
        except Exception as error:
            if "already exists" not in str(error).lower():
                raise
            status = "exists"
        # Omit literal values, which may contain private configuration.
        head = re.match(r"[A-Za-z_][A-Za-z0-9_]*", statement)
        results.append((head.group() if head else "SQL", status))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Register SQL files in Zetaris")
    parser.add_argument("files", nargs="+", help="SQL paths or glob patterns, in execution order")
    args = parser.parse_args()
    paths: list[Path] = []
    for pattern in args.files:
        matches = sorted(glob.glob(pattern))
        if not matches:
            parser.error("SQL file pattern matched no files")
        paths.extend(Path(path) for path in matches)
    try:
        results = run_files(ZetarisClient.from_env(), paths, dict(os.environ))
    except KeyError as error:
        parser.exit(1, f"Missing substitution variable: {error.args[0]}\n")
    except Exception as error:
        parser.exit(1, f"Registration failed ({type(error).__name__})\n")
    for head, status in results:
        print(f"{head}: {status}")


if __name__ == "__main__":
    main()
