"""Load explicitly selected, ignored local configuration without executing shell code."""

from __future__ import annotations

import os
import re
from pathlib import Path

_ALLOWED = re.compile(r"(?:ZETARIS_|METERLESS_|NVIDIA_|NIM_|ENGINES_)[A-Z0-9_]+")


def load_private_env(path: Path) -> None:
    """Read integration settings only; existing process values have precedence."""
    if path.stat().st_size > 65536:
        raise ValueError("Integration environment file exceeds the size limit")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not _ALLOWED.fullmatch(key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        # No substitutions, includes or expansion: the value is data, never a shell program.
        if value:
            os.environ.setdefault(key, value)
