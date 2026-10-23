"""JSONL run trace: logs/trace-<run_id>.jsonl plus a one-line echo per event on stdout.

Every event satisfies contracts $defs/TraceEvent and is validated before it is written.
Secrets are redacted from messages and from every string inside payloads.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Iterator

from tradepulse.contracts import assert_payload
from tradepulse.store import RUN_ID

SECRET_PATTERNS: tuple[str, ...] = (
    r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+",
    r"nvapi-[A-Za-z0-9_-]+",
    r"(?i)\b(api[_-]?key|token|password|secret)\b\s*[=:]\s*[^\s,;]+",
)
REDACTED = "[REDACTED]"


def redact(text: str) -> str:
    """Replace every match of SECRET_PATTERNS with REDACTED."""
    for pattern in SECRET_PATTERNS:
        text = re.sub(pattern, REDACTED, text)
    return text


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {_redact_value(key): _redact_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_value(item) for item in value]
    return value


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
        if not isinstance(run_id, str) or RUN_ID.fullmatch(run_id) is None:
            raise ValueError("Invalid run_id")
        self.run_id = run_id
        self.data_mode = data_mode
        self.echo = echo
        self.clock = clock if clock is not None else lambda: dt.datetime.now(dt.timezone.utc)
        self._seq = 0
        self._lock = Lock()
        log_dir = Path(log_dir)
        self._path = log_dir / f"trace-{run_id}.jsonl"
        if not self._path.resolve().is_relative_to(log_dir.resolve()):
            raise ValueError("Trace path is outside log_dir")
        log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def event(self, node: str, kind: str, *, status: str = "ok", message: str = "",
              payload: dict | None = None, duration_ms: int | None = None, model: str | None = None,
              tokens_in: int | None = None, tokens_out: int | None = None) -> dict:
        """Build, redact, validate (tradepulse.contracts.assert_payload(..., "TraceEvent")), append
        one JSON line, flush, echo, and return the event dict."""
        with self._lock:
            timestamp = self.clock()
            if timestamp.utcoffset() is None:
                raise ValueError("Trace clock must return a timezone-aware datetime")
            event = _redact_value({
                "ts": timestamp.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                "run_id": self.run_id,
                "seq": self._seq,
                "node": node,
                "kind": kind,
                "status": status,
                "duration_ms": duration_ms,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "data_mode": self.data_mode,
                "message": message,
                "payload": {} if payload is None else payload,
            })
            assert_payload(event, "TraceEvent")
            line = json.dumps(event, ensure_ascii=False, allow_nan=False)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()
            self._seq += 1
            if self.echo:
                print(f"[{event['seq']:04d}] {event['node']} {event['kind']} "
                      f"{event['status']} {event['message']}")
            return event

    @contextmanager
    def span(self, node: str, message: str = "") -> Iterator[None]:
        """Emit node_start, run the block, then node_end with duration_ms (int, monotonic clock).
        If the block raises: emit kind="error", status="error", message=redact("<Type>: <text>"),
        then re-raise the same exception."""
        self.event(node, "node_start", message=message)
        started = time.monotonic()
        try:
            yield
        except Exception as exc:
            self.event(node, "error", status="error", message=f"{type(exc).__name__}: {exc}",
                       duration_ms=int((time.monotonic() - started) * 1000))
            raise
        else:
            self.event(node, "node_end", message=message,
                       duration_ms=int((time.monotonic() - started) * 1000))

    def events(self) -> list[dict]:
        """Read the trace file back as a list of dicts."""
        if not self.path.is_file():
            return []
        with self._lock:
            return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines()
                    if line.strip()]
