"""Verify and serve the original accepted Crypto result without generating or trading."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

from tradepulse.contracts import REPO_ROOT, assert_payload


def load_bundle(root: Path = REPO_ROOT):
    manifest = json.loads((root / "docs/review/crypto-evidence.json").read_text(encoding="utf-8"))
    content = {}
    for name, expected in manifest["files"].items():
        path = (root / expected["path"]).resolve()
        if not path.is_relative_to(root.resolve()) or path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Review artifact escapes its directory or exceeds the work limit")
        raw = path.read_bytes()
        if len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
            raise ValueError("Review artifact does not match its recorded byte hash")
        content[name] = raw
    request = json.loads(content["input.json"])
    output = json.loads(content["output.json"])
    events = [json.loads(line) for line in content["trace.jsonl"].splitlines() if line.strip()]
    assert_payload(request, "RunRequest")
    assert_payload(output, "RunOutput")
    if (output["run_id"] != manifest["run_id"] or output["request"] != request
            or request["pools"] != ["crypto"] or output["data_mode"] != "REAL" or output["sample_mode"]
            or output["trace_path"] != manifest["files"]["trace.jsonl"]["path"]):
        raise ValueError("Review input, output and original trace identities do not agree")
    if len(events) > 10000:
        raise ValueError("Review trace exceeds its work limit")
    for event in events:
        assert_payload(event, "TraceEvent")
        if event["run_id"] != output["run_id"]:
            raise ValueError("Review trace contains a different run")
    calls = [event for event in events if event["kind"] == "llm_call"]
    if (not calls or any(event["payload"].get("provider") != "glm"
                         or event["payload"].get("replayed") is not False for event in calls)):
        raise ValueError("Published inference provenance does not match the GLM case")
    operations = {event["payload"].get("operation") for event in events
                  if event["node"] == "meterless" and event["kind"] == "tool_call"}
    if not {"snapshot", "recall", "remember"} <= operations:
        raise ValueError("Published trace does not contain all required engine operations")
    return output, events


def create_review_app():
    from fastapi.responses import JSONResponse
    from tradepulse.api import create_app

    output, _events = load_bundle()

    class SavedRun:
        def latest(self):
            return deepcopy(output)

        def get(self, run_id):
            return deepcopy(output) if run_id == output["run_id"] else None

    def disabled_runner(_request):
        raise RuntimeError("Review server cannot generate new runs")

    app = create_app(store=SavedRun(), runner=disabled_runner)

    @app.middleware("http")
    async def read_only(request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            return JSONResponse({"error": "review_read_only"}, status_code=405)
        response = await call_next(request)
        response.headers["X-TradePulse-Review-Mode"] = "saved-real-run; generation-disabled"
        return response

    return app


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    output, events = load_bundle()
    print(json.dumps({"review_mode": "saved-real-run", "new_model_calls": 0,
                      "run_id": output["run_id"], "recommendations": len(output["recommendations"]),
                      "verdicts": dict(Counter(item["verdict"] for item in output["explanations"])),
                      "original_trace_events": len(events)}), flush=True)
    if not args.verify_only:
        import uvicorn
        uvicorn.run(create_review_app(), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
