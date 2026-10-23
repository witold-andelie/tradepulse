"""Run storage: runs/<run_id>/output.json (one RunOutput per run)."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import tempfile
from pathlib import Path

from tradepulse.contracts import REPO_ROOT, assert_payload

RUN_ID = re.compile(r"^[a-z0-9-]{8,64}$")


class RunStore:
    """root defaults to <repo>/runs. Writes are atomic (temp file + os.replace)."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else REPO_ROOT / "runs"

    def _output_path(self, run_id: str) -> Path | None:
        if not isinstance(run_id, str) or RUN_ID.fullmatch(run_id) is None:
            return None
        path = self.root / run_id / "output.json"
        if not path.resolve().is_relative_to(self.root.resolve()):
            return None
        return path

    def save(self, output: dict) -> Path:
        """Write output to root/<run_id>/output.json (UTF-8, indent=1) and return the path.
        An invalid run_id (not matching RUN_ID) raises ValueError."""
        path = self._output_path(output.get("run_id"))
        if path is None:
            raise ValueError("Invalid run_id or path outside storage root")
        assert_payload(output, "RunOutput")
        contents = json.dumps(output, ensure_ascii=False, indent=1, allow_nan=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                             suffix=".tmp", delete=False) as fh:
                temporary = Path(fh.name)
                fh.write(contents)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return path

    def get(self, run_id: str) -> dict | None:
        """The stored output, or None when run_id is invalid or unknown (never touches paths
        outside root)."""
        path = self._output_path(run_id)
        if path is None:
            return None
        try:
            output = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        assert_payload(output, "RunOutput")
        return output

    def latest(self) -> dict | None:
        """The stored output with the greatest created_at (ties: greatest run_id), or None."""
        outputs = [output for run_id in self.list_ids() if (output := self.get(run_id)) is not None]
        return max(outputs, key=lambda output: (
            dt.datetime.fromisoformat(output["created_at"].upper().replace("Z", "+00:00")),
            output["run_id"],
        ), default=None)

    def list_ids(self) -> list[str]:
        """Run ids that have an output.json, sorted."""
        if not self.root.is_dir():
            return []
        ids = []
        for child in self.root.iterdir():
            path = self._output_path(child.name)
            if path is not None and path.is_file():
                ids.append(child.name)
        return sorted(ids)
