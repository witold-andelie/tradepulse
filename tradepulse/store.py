"""Run storage: runs/<run_id>/output.json (one RunOutput per run)."""

from __future__ import annotations

import re
from pathlib import Path

RUN_ID = re.compile(r"^[a-z0-9-]{8,64}$")


class RunStore:
    """root defaults to <repo>/runs. Writes are atomic (temp file + os.replace)."""

    def __init__(self, root: Path | None = None) -> None:
        raise NotImplementedError

    def save(self, output: dict) -> Path:
        """Write output to root/<run_id>/output.json (UTF-8, indent=1) and return the path.
        An invalid run_id (not matching RUN_ID) raises ValueError."""
        raise NotImplementedError

    def get(self, run_id: str) -> dict | None:
        """The stored output, or None when run_id is invalid or unknown (never touches paths
        outside root)."""
        raise NotImplementedError

    def latest(self) -> dict | None:
        """The stored output with the greatest created_at (ties: greatest run_id), or None."""
        raise NotImplementedError

    def list_ids(self) -> list[str]:
        """Run ids that have an output.json, sorted."""
        raise NotImplementedError
