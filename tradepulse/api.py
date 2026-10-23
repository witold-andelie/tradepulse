"""HTTP API (FastAPI). Endpoints are listed in contracts/README.md.

create_app(store, runner, today, earliest) builds the app; module-level `app` uses defaults:
RunStore(), tradepulse.pipeline.run_pipeline (imported lazily), date.today(), and earliest =
today - (backtest.window_days + backtest.warmup_days) from config.

- POST /run: body -> guard_request. GuardRejection -> 422 {"error": code, "detail": detail}.
  Only one run at a time: a second concurrent request -> 409 {"error": "busy"}.
  runner(request) must return a RunOutput; contract violations -> 500
  {"error": "contract", "detail": [first 20 messages]}; any other exception -> 500
  {"error": "run_failed", "detail": "<ExceptionType>"} (no message text: it may contain data).
  Success: store.save(output) and return the output.
- GET /runs/latest -> latest output or 404 {"error": "not_found"}.
- GET /runs/{run_id} -> output or 404 (invalid ids are 404 too).
- GET /runs/{run_id}/trace -> list of TraceEvent dicts read from the output's trace_path
  (relative to the repo root), or 404 when the run or file is missing.
- GET /health -> {"status": "ok", "sample_mode": <SAMPLE_MODE env, default true>}.
- CORS allows the origin in env WEB_ORIGIN (default http://localhost:5173).
"""

from __future__ import annotations

from tradepulse.contracts import REPO_ROOT  # trace_path is resolved against this (tests patch it)


def create_app(store=None, runner=None, today=None, earliest=None):
    raise NotImplementedError


app = None  # replaced by create_app() once implemented
