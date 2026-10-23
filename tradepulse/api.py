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

import datetime as dt
import json
import os
from pathlib import Path
from threading import Lock
from typing import Any, Callable

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tradepulse.config import load_config
from tradepulse.contracts import REPO_ROOT  # trace_path is resolved against this (tests patch it)
from tradepulse.contracts import assert_payload, validate_payload
from tradepulse.guard import GuardRejection, guard_request
from tradepulse.store import RunStore


def _default_runner(request: dict) -> dict:
    from tradepulse.pipeline import run_pipeline

    return run_pipeline(request)


def create_app(store: RunStore | None = None, runner: Callable[[dict], dict] | None = None,
               today: dt.date | None = None, earliest: dt.date | None = None) -> FastAPI:
    store = store if store is not None else RunStore()
    runner = runner if runner is not None else _default_runner
    fixed_today, fixed_earliest = today, earliest
    span = load_config()["backtest"]
    lookback = dt.timedelta(days=span["window_days"] + span["warmup_days"])

    def bounds() -> tuple[dt.date, dt.date]:
        # Evaluated per request so a long-running server never uses a stale date.
        current = fixed_today if fixed_today is not None else dt.date.today()
        return current, fixed_earliest if fixed_earliest is not None else current - lookback
    run_lock = Lock()
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("WEB_ORIGIN", "http://localhost:5173")],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def invalid_body(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse({"error": "schema", "detail": "Invalid JSON request body"},
                            status_code=422)

    @app.post("/run")
    def post_run(raw: Any = Body(...)) -> JSONResponse:
        try:
            current, first = bounds()
            request = guard_request(raw, today=current, earliest=first)
        except GuardRejection as exc:
            return JSONResponse({"error": exc.code, "detail": exc.detail}, status_code=422)
        if not run_lock.acquire(blocking=False):
            return JSONResponse({"error": "busy"}, status_code=409)
        try:
            output = runner(request)
            errors = validate_payload(output, "RunOutput")
            if errors:
                return JSONResponse({"error": "contract", "detail": errors[:20]}, status_code=500)
            store.save(output)
            return JSONResponse(output)
        except Exception as exc:
            return JSONResponse({"error": "run_failed", "detail": type(exc).__name__},
                                status_code=500)
        finally:
            run_lock.release()

    @app.get("/runs/latest")
    def latest_run() -> JSONResponse:
        output = store.latest()
        if output is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return JSONResponse(output)

    @app.get("/runs/{run_id}")
    def get_run(run_id: str) -> JSONResponse:
        output = store.get(run_id)
        if output is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return JSONResponse(output)

    @app.get("/runs/{run_id}/trace")
    def get_trace(run_id: str) -> JSONResponse:
        output = store.get(run_id)
        if output is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        root = REPO_ROOT.resolve()
        relative = Path(output["trace_path"])
        path = (root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root) or not path.is_file():
            return JSONResponse({"error": "not_found"}, status_code=404)
        try:
            events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                      if line.strip()]
            for event in events:
                assert_payload(event, "TraceEvent")
            return JSONResponse(events)
        except (OSError, ValueError) as exc:
            return JSONResponse({"error": "run_failed", "detail": type(exc).__name__},
                                status_code=500)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "sample_mode": os.getenv("SAMPLE_MODE", "true").strip().lower()
                in {"true", "1", "yes", "on"}}

    return app


app = create_app()
