"""Exercise a fresh real-sample run with network calls blocked; write measured CI evidence."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import socket
import tempfile
import time
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from serve import ensure_sample_run
from tradepulse.contracts import assert_payload
from tradepulse.pipeline import run_pipeline
from tradepulse.store import RunStore


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    attempts = []

    def blocked(*_args, **_kwargs):
        attempts.append(True)
        raise RuntimeError("CI offline smoke forbids network calls")

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="tradepulse-ci-", dir=args.output.parent) as directory:
        root = Path(directory)
        store = RunStore(root / "runs")

        def runner(request):
            return run_pipeline(request, log_dir=root / "logs")

        with patch.dict(os.environ, {"SAMPLE_MODE": "true", "RECORD_LLM": "false",
                                     "ENGINES_ENABLED": "false"}), \
                patch.object(socket.socket, "connect", blocked), \
                patch.object(socket, "getaddrinfo", blocked), contextlib.redirect_stdout(io.StringIO()):
            output = ensure_sample_run(store, runner=runner)
            cached = ensure_sample_run(store, runner=runner)
        assert_payload(output, "RunOutput")
        if attempts or cached["run_id"] != output["run_id"] or not output["recommendations"]:
            raise AssertionError("Fresh offline startup or cached reuse failed")
        events = [json.loads(line) for line in Path(output["trace_path"]).read_text(encoding="utf-8").splitlines()]
        for event in events:
            assert_payload(event, "TraceEvent")
        evidence = {"run_id": output["run_id"], "as_of": output["as_of"],
                    "data_mode": output["data_mode"], "recommendations": len(output["recommendations"]),
                    "factor_cards": len(output["factor_cards"]),
                    "explanations": dict(Counter(item["verdict"] for item in output["explanations"])),
                    "tiers": dict(Counter(item["tier"] for item in output["recommendations"])),
                    "trace_events": len(events), "network_attempts": len(attempts),
                    "cached_run_reused": True, "seconds": time.monotonic() - started,
                    "scope": "Actual offline sample computation; no hosted sponsors or model recording certified."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
