"""JSONL run trace: logs/trace-<run_id>.jsonl plus a one-line echo per event on stdout.

Every event satisfies contracts $defs/TraceEvent and is validated before it is written.
Secrets are redacted from messages and from every string inside payloads.
"""

from __future__ import annotations

import datetime as dt
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

SECRET_PATTERNS: tuple[str, ...] = (
    r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+",
    r"nvapi-[A-Za-z0-9_-]+",
    r"(?i)\b(api[_-]?key|token|password|secret)\b\s*[=:]\s*[^\s,;]+",
)
REDACTED = "[REDACTED]"


def redact(text: str) -> str:
    """Replace every match of SECRET_PATTERNS with REDACTED."""
    raise NotImplementedError


class Tracer:
    """Append-only trace for one run.

    - path = log_dir / f"trace-{run_id}.jsonl" (log_dir is created if missing).
    - seq starts at 0 and increases by 1 per event.
    - ts comes from clock() (a callable returning a timezone-aware datetime, default UTC now),
      written as ISO 8601 with a trailing 'Z' (e.g. 2026-10-22T08:00:00.123000Z).
    - echo=True prints f"[{seq:04d}] {node} {kind} {status} {message}" to stdout per event.
    """

    def __init__(self, run_id: str, data_mode: str, log_dir: Path = Path("logs"), echo: bool = True,
                 clock: Callable[[], dt.datetime] | None = None) -> None:
        raise NotImplementedError

    @property
    def path(self) -> Path:
        raise NotImplementedError

    def event(self, node: str, kind: str, *, status: str = "ok", message: str = "",
              payload: dict | None = None, duration_ms: int | None = None, model: str | None = None,
              tokens_in: int | None = None, tokens_out: int | None = None) -> dict:
        """Build, redact, validate (tradepulse.contracts.assert_payload(..., "TraceEvent")), append
        one JSON line, flush, echo, and return the event dict."""
        raise NotImplementedError

    @contextmanager
    def span(self, node: str, message: str = ""):
        """Emit node_start, run the block, then node_end with duration_ms (int, monotonic clock).
        If the block raises: emit kind="error", status="error", message=redact("<Type>: <text>"),
        then re-raise the same exception."""
        raise NotImplementedError
        yield  # pragma: no cover

    def events(self) -> list[dict]:
        """Read the trace file back as a list of dicts."""
        raise NotImplementedError
