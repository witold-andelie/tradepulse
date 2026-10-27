"""Run three sponsor-connected cases and package actual inputs, outputs and original traces.

All live cases use Zetaris templates, Nightshift (with no cloud fallback) and the real engines
sidecar. No synthetic answer or cassette reply can satisfy the success checks.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import threading
from collections import Counter
from pathlib import Path
from time import perf_counter

from ingest.privacy import CONTACT_ADDRESS
from serve import verified_sample_request
from tradepulse.contracts import REPO_ROOT, assert_payload
from tradepulse.engines import configured_engines
from tradepulse.pipeline import run_pipeline

from .environment import load_private_env
from .meterless.llm import Cassette, ChainClient, build_routes_from_env, read_token
from .zetaris.adapter import DuckDBAdapter, ZetarisAdapter
from .zetaris.client import ZetarisClient
from .zetaris.parity import check_parity


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def check_public_bytes(raw: bytes, secrets: list[str]) -> None:
    text = raw.decode("utf-8")
    if CONTACT_ADDRESS.search(text) or any(secret and secret in text for secret in secrets):
        raise ValueError("Acceptance artifact contains a private value; review it locally")


def write_json(path: Path, payload, secrets: list[str]) -> dict:
    raw = (json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    check_public_bytes(raw, secrets)
    path.write_bytes(raw)
    return {"bytes": len(raw), "sha256": digest(raw)}


class AuditedQueries:
    """Attach real template/hash receipts without logging raw data or credentials."""

    def __init__(self, adapter, path: Path) -> None:
        self.adapter, self.path = adapter, path
        self.calls = []
        self._lock = threading.Lock()

    def run(self, template: str, params: dict):
        result = self.adapter.run(template, params)
        entry = {"template": template, "params": params, "backend": result.backend,
                 "rows": len(result.df), "rows_sha256": result.rows_sha256,
                 "elapsed_ms": result.elapsed_ms}
        with self._lock:
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(entry, sort_keys=True) + "\n")
            self.calls.append(entry)
        return result


class AuditedLLM:
    def __init__(self, client, path: Path) -> None:
        self.client, self.path = client, path
        self._lock = threading.Lock()

    def complete(self, role, messages, response_schema=None):
        started = perf_counter()
        result = self.client.complete(role, messages, response_schema)
        receipt = {"role": role, "provider": result.provider, "model": result.model,
                   "replayed": result.replayed, "cassette_key": result.cassette_key,
                   "response_sha256": digest(result.text.encode("utf-8")),
                   "tokens_in": result.tokens_in, "tokens_out": result.tokens_out,
                   "elapsed_ms": int((perf_counter() - started) * 1000)}
        with self._lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(receipt, sort_keys=True) + "\n")
        return result


def validate_case(output: dict, events: list[dict]) -> dict:
    assert_payload(output, "RunOutput")
    if output["sample_mode"] or output["data_mode"] != "REAL":
        raise ValueError("Live acceptance requires a REAL run")
    for event in events:
        assert_payload(event, "TraceEvent")
    answered = [event for event in events if event["kind"] == "llm_call"]
    if not answered or any(event["payload"].get("provider") != "meterless" or
                           event["payload"].get("replayed") is not False for event in answered):
        raise ValueError("Live acceptance requires actual Nightshift answers")
    if not all(any(event["message"] == f"{role} answered" for event in answered)
               for role in ("analyst", "skeptic")):
        raise ValueError("Nightshift must answer both analyst and skeptic roles")
    if any("unavailable" in explanation["models"].values()
           for explanation in output["explanations"]):
        raise ValueError("One or more explanation model calls were unavailable")
    operations = Counter(event["payload"].get("operation") for event in events
                         if event["node"] == "meterless" and event["kind"] == "tool_call")
    if not {"snapshot", "recall", "remember"} <= operations.keys():
        raise ValueError("The actual core run must use engine snapshots, recall and persistence")
    if any(event["node"] == "meterless" and event["status"] == "error" for event in events):
        raise ValueError("Core trace contains an engine error")
    return {
        "nightshift_calls": len(answered), "engine_operations": dict(operations),
        "verdicts": dict(Counter(item["verdict"] for item in output["explanations"])),
        "tiers": dict(Counter(item["tier"] for item in output["recommendations"])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, action="append", default=[],
                        help="ignored env file to load; may be supplied more than once")
    parser.add_argument("--output", type=Path, required=True,
                        help="new directory under the ignored runs/ directory")
    args = parser.parse_args(argv)
    destination = args.output.resolve()
    if not destination.is_relative_to(REPO_ROOT / "runs"):
        raise ValueError("Choose an acceptance destination under runs/")
    if destination.exists():
        raise FileExistsError("Choose a new destination; previous run evidence is preserved")
    for path in args.env_file:
        load_private_env(path.expanduser())
    token_file = os.environ.get("METERLESS_TOKEN_FILE")
    if not token_file:
        raise ValueError("Configure METERLESS_TOKEN_FILE before live acceptance")
    secrets = [read_token(token_file), os.environ.get("ZETARIS_API_KEY", ""),
               os.environ.get("ENGINES_TOKEN", ""), os.environ.get("NVIDIA_API_KEY", "")]
    routes = {role: [route for route in values if route[0] == "meterless"]
              for role, values in build_routes_from_env().items()}
    if any(not routes.get(role) for role in ("extractor", "analyst", "skeptic")):
        raise ValueError("Nightshift must be configured for extractor, analyst and skeptic")

    os.environ["SAMPLE_MODE"] = "false"
    os.environ["ENGINES_ENABLED"] = "true"
    engines = configured_engines(False)
    health = engines.health()
    if health.get("status") != "ok":
        raise ValueError("Engines sidecar is not ready")
    request = verified_sample_request()
    adapter = ZetarisAdapter(ZetarisClient.from_env())
    parity = check_parity(adapter, DuckDBAdapter(REPO_ROOT / "data" / "sample"), request["as_of"])
    if not all(item["match"] for item in parity):
        raise ValueError("Zetaris/DuckDB parity failed; run integrations.zetaris.parity for details")

    destination.mkdir(parents=True)
    write_json(destination / "parity.json", parity, secrets)
    query = AuditedQueries(adapter, destination / "queries.jsonl")
    llm = AuditedLLM(
        ChainClient(routes, Cassette(destination / "llm_cassette.jsonl"), mode="record"),
        destination / "models.jsonl",
    )
    cases = []
    started = perf_counter()
    manifest = {"status": "running", "as_of": request["as_of"],
                "engines": health["engines"], "cases": cases,
                "generated_at": dt.datetime.now(dt.UTC).isoformat()}
    try:
        # Small pools provide the first end-to-end evidence before the filing workload.
        for pool in ("crypto", "eu_equity", "us_equity"):
            case = {**request, "pools": [pool], "top_k": 1}
            assert_payload(case, "RunRequest")
            folder = destination / pool
            folder.mkdir()
            print(json.dumps({"status": "running", "pool": pool}), flush=True)
            with (folder / "console.log").open("w", encoding="utf-8") as console:
                with contextlib.redirect_stdout(console):
                    output = run_pipeline(case, query=query, llm=llm, engines=engines,
                                          log_dir=folder)
            check_public_bytes((folder / "console.log").read_bytes(), secrets)
            original_trace = REPO_ROOT / output["trace_path"]
            raw_trace = original_trace.read_bytes()
            check_public_bytes(raw_trace, secrets)
            events = [json.loads(line) for line in raw_trace.splitlines()]
            checked = validate_case(output, events)
            # Keep the original trace file and bytes. The packaged reference is repo-relative.
            output["trace_path"] = original_trace.relative_to(REPO_ROOT).as_posix()
            files = {"input.json": write_json(folder / "input.json", case, secrets),
                     "output.json": write_json(folder / "output.json", output, secrets),
                     original_trace.name: {"bytes": len(raw_trace), "sha256": digest(raw_trace)}}
            cases.append({"pool": pool, "run_id": output["run_id"], "files": files,
                          "recommendations": len(output["recommendations"]), **checked})
            write_json(destination / "manifest.json", manifest, secrets)
            print(json.dumps({"status": "ok", "pool": pool, **checked}), flush=True)
        check_public_bytes((destination / "llm_cassette.jsonl").read_bytes(), secrets)
        check_public_bytes((destination / "queries.jsonl").read_bytes(), secrets)
        check_public_bytes((destination / "models.jsonl").read_bytes(), secrets)
        manifest.update({"status": "ok", "elapsed_s": round(perf_counter() - started, 2),
                         "zetaris_queries": len(query.calls)})
        lines = ["# Live sponsor acceptance examples", "",
                 "Computed through Zetaris, Nightshift and the Meterless engines sidecar.", "",
                 "| Pool | Recommendation records | Nightshift calls | Explanation verdicts |",
                 "| --- | ---: | ---: | --- |"]
        for item in cases:
            lines.append(f"| {item['pool']} | {item['recommendations']} | "
                         f"{item['nightshift_calls']} | {json.dumps(item['verdicts'])} |")
        lines += ["", "Each pool folder contains input.json, output.json and the original trace.",
                  "All tiers and verdicts are computed. Abstention remains a valid research result.",
                  "The current engine integration uses historical record counts, not prior accuracy.",
                  "Review model text and traces for privacy before publishing these artifacts."]
        (destination / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as error:
        manifest.update({"status": "failed", "failure_type": type(error).__name__})
        write_json(destination / "manifest.json", manifest, secrets)
        print(json.dumps({"status": "failed", "failure_type": type(error).__name__,
                          "completed_cases": len(cases)}), flush=True)
        return 1
    write_json(destination / "manifest.json", manifest, secrets)
    print(json.dumps({"status": "ok", "cases": len(cases), "output": str(destination)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
