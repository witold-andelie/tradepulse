"""Compute three real-snapshot input/output/trace examples without live model calls."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import io
import json
import socket
from collections import Counter
from pathlib import Path

from ingest.privacy import CONTACT_ADDRESS
from serve import verified_sample_request
from tradepulse.contracts import REPO_ROOT, assert_payload
from tradepulse.pipeline import record_llm, run_pipeline, sample_mode


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("examples"))
    parser.add_argument("--offline-check", action="store_true")
    args = parser.parse_args(argv)
    if not sample_mode() or record_llm():
        raise ValueError("Examples require SAMPLE_MODE=true and RECORD_LLM=false")
    if args.output.exists():
        raise FileExistsError("Choose a fresh examples destination; previous evidence is preserved")
    if not args.output.resolve().is_relative_to(REPO_ROOT.resolve()):
        raise ValueError("Choose an examples destination inside the repository")
    base = verified_sample_request()
    if len(base["pools"]) > 3:
        raise ValueError("Example generation is limited to the three agreed pools")
    attempts = []

    def blocked(*_args, **_kwargs):
        attempts.append(True)
        raise RuntimeError("Networking is disabled for example generation")

    connect, getaddrinfo = socket.socket.connect, socket.getaddrinfo
    entries = []
    try:
        if args.offline_check:
            socket.socket.connect = blocked
            socket.getaddrinfo = blocked
        for pool in base["pools"]:
            request = {**base, "pools": [pool], "top_k": 1}
            assert_payload(request, "RunRequest")
            with contextlib.redirect_stdout(io.StringIO()):
                output = run_pipeline(request)
            assert_payload(output, "RunOutput")
            original_trace = output["trace_path"]
            trace = (REPO_ROOT / original_trace).read_bytes()
            if len(trace) > 10_000_000:
                raise ValueError("Example trace exceeds the bounded delivery size")
            for line in trace.splitlines():
                assert_payload(json.loads(line), "TraceEvent")
            folder = args.output / pool
            folder.mkdir(parents=True)
            relative_trace = (folder / "trace.jsonl").resolve().relative_to(REPO_ROOT)
            output = {**output, "trace_path": relative_trace.as_posix()}
            assert_payload(output, "RunOutput")
            payloads = {
                "input.json": (json.dumps(request, indent=2) + "\n").encode(),
                "output.json": (json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode(),
                "trace.jsonl": trace,
            }
            for name, payload in payloads.items():
                if CONTACT_ADDRESS.search(payload.decode("utf-8")):
                    raise ValueError("Example payload contains a contact address")
                (folder / name).write_bytes(payload)
            entries.append({"pool": pool, "run_id": output["run_id"],
                            "recommendations": len(output["recommendations"]),
                            "factor_cards": len(output["factor_cards"]),
                            "explanations": dict(Counter(e["verdict"] for e in output["explanations"])),
                            "tiers": dict(Counter(r["tier"] for r in output["recommendations"])),
                            "original_trace_path": original_trace,
                            "files": {name: {"bytes": len(value), "sha256": digest(value)}
                                      for name, value in payloads.items()}})
    finally:
        socket.socket.connect, socket.getaddrinfo = connect, getaddrinfo
    if attempts:
        raise RuntimeError("Example generation attempted networking; evidence is not accepted")
    manifest = {"as_of": base["as_of"], "generated_at": dt.datetime.now(dt.UTC).isoformat(),
                "source": "Frozen real public-data snapshot; not synthetic fixture results.",
                "models_recorded": False, "network_blocked": args.offline_check,
                "network_attempts": len(attempts), "cases": entries,
                "trace_policy": "Original trace bytes retained; only output trace_path relocated to the packaged trace."}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"as_of": base["as_of"], "cases": len(entries), "network_attempts": len(attempts)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
