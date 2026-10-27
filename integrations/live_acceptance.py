"""Run three sponsor-connected cases and package actual inputs, outputs and original traces.

All live cases use Zetaris templates, an explicitly selected live AI provider and the real
engines sidecar. No synthetic answer or cassette reply can satisfy the success checks.
The original Nightshift-only profile remains available; GLM is a distinct hosted profile.
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
from tradepulse.store import RunStore

from .environment import load_private_env
from .meterless.llm import Cassette, ChainClient, build_routes_from_env, read_glm_api_key, read_token
from .meterless.reply_checks import inspect_reply
from .zetaris.adapter import DuckDBAdapter, ZetarisAdapter
from .zetaris.client import ZetarisClient
from .zetaris.parity import check_parity
from .zetaris.receipt_cache import ReceiptCache, read_receipt_file, verified_parity

ALL_POOLS = ("crypto", "eu_equity", "us_equity")


class ModelSchemaError(ValueError):
    """A real provider replied, but its text does not satisfy the requested response schema."""


def selection_result(cases: list[dict], pools: list[str]) -> dict:
    complete = len(cases) == len(ALL_POOLS) and {item["pool"] for item in cases} == set(ALL_POOLS)
    return {"status": "ok" if complete else "selected_cases_ok",
            "submission_complete": complete, "selected_pools": pools,
            "remaining_pools": [pool for pool in ALL_POOLS
                                if pool not in {item["pool"] for item in cases}]}


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
        checked = inspect_reply(result.text, response_schema)
        schema_valid = checked["schema_valid"]
        receipt = {"role": role, "provider": result.provider, "model": result.model,
                   "replayed": result.replayed, "cassette_key": result.cassette_key,
                   "response_sha256": digest(result.text.encode("utf-8")),
                   "tokens_in": result.tokens_in, "tokens_out": result.tokens_out,
                   "elapsed_ms": int((perf_counter() - started) * 1000),
                   "schema_valid": schema_valid, "schema_errors": checked["errors"]}
        with self._lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(receipt, sort_keys=True) + "\n")
        # The core extractor owns its bounded per-document feedback/grounding retry. Raising
        # here would abort the entire extraction stage before that existing loop can act.
        if not schema_valid and role != "extractor":
            raise ModelSchemaError("Provider response did not satisfy the requested JSON schema")
        return result


class AuditedEngines:
    """Keep the exact pending write payload before HTTP, without altering core orchestration."""

    def __init__(self, client, destination, secrets):
        self.client, self.destination, self.secrets = client, destination, secrets

    def __getattr__(self, name):
        return getattr(self.client, name)

    def remember(self, records):
        pool = records[0]["content"]["pool"] if records else "empty"
        if pool not in (*ALL_POOLS, "empty"):
            raise ValueError("Unexpected pending-memory pool")
        write_json(self.destination / f"pending-memory-records-{pool}.json", {"records": records}, self.secrets)
        return self.client.remember(records)


def validate_case(output: dict, events: list[dict], *, expected_provider: str = "meterless") -> dict:
    if expected_provider not in {"meterless", "glm"}:
        raise ValueError("Unknown live acceptance provider")
    assert_payload(output, "RunOutput")
    if output["sample_mode"] or output["data_mode"] != "REAL":
        raise ValueError("Live acceptance requires a REAL run")
    for event in events:
        assert_payload(event, "TraceEvent")
    answered = [event for event in events if event["kind"] == "llm_call"]
    if not answered or any(event["payload"].get("provider") != expected_provider or
                           event["payload"].get("replayed") is not False for event in answered):
        raise ValueError("Live acceptance requires actual answers from the selected provider")
    if not all(any(event["message"] == f"{role} answered" for event in answered)
               for role in ("analyst", "skeptic")):
        raise ValueError("The selected provider must answer both analyst and skeptic roles")
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
        "llm_provider": expected_provider, "llm_calls": len(answered),
        "nightshift_calls": len(answered) if expected_provider == "meterless" else 0,
        "engine_operations": dict(operations),
        "verdicts": dict(Counter(item["verdict"] for item in output["explanations"])),
        "tiers": dict(Counter(item["tier"] for item in output["recommendations"])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, action="append", default=[],
                        help="ignored env file to load; may be supplied more than once")
    parser.add_argument("--output", type=Path, required=True,
                        help="new directory under the ignored runs/ directory")
    parser.add_argument("--pools", nargs="+", choices=ALL_POOLS, default=list(ALL_POOLS),
                        help="run selected pools first; only all three can complete submission acceptance")
    parser.add_argument("--llm-provider", choices=("nightshift", "glm"), default="nightshift",
                        help="explicit profile; hosted GLM never calls local Nightshift")
    parser.add_argument("--reuse-parity", type=Path,
                        help="explicit prior live parity evidence, rechecked against the current frozen sample")
    parser.add_argument("--bulk-receipts", type=Path,
                        help="prior real Zetaris query receipts for explicitly labelled bulk-window caching")
    args = parser.parse_args(argv)
    if len(set(args.pools)) != len(args.pools):
        parser.error("Each pool may be selected only once")
    destination = args.output.resolve()
    if not destination.is_relative_to(REPO_ROOT / "runs"):
        raise ValueError("Choose an acceptance destination under runs/")
    if destination.exists():
        raise FileExistsError("Choose a new destination; previous run evidence is preserved")
    for path in args.env_file:
        load_private_env(path.expanduser())
    expected_provider = "glm" if args.llm_provider == "glm" else "meterless"
    os.environ["LLM_PROVIDER"] = "glm" if expected_provider == "glm" else "auto"
    secrets = [os.environ.get(name, "") for name in
               ("ZETARIS_API_KEY", "ZETARIS_PASSWORD", "ENGINES_TOKEN", "NVIDIA_API_KEY", "GLM_API_KEY")]
    if expected_provider == "meterless":
        token_file = os.environ.get("METERLESS_TOKEN_FILE")
        if not token_file:
            raise ValueError("Configure METERLESS_TOKEN_FILE for Nightshift acceptance")
        secrets.append(read_token(token_file))
    else:
        secrets.append(read_glm_api_key())
    request_lock = threading.Lock()

    def record_request(receipt):
        with request_lock, (destination / "model_requests.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(receipt, sort_keys=True) + "\n")

    routes = {role: [route for route in values if route[0] == expected_provider]
              for role, values in build_routes_from_env(diagnostics=record_request).items()}
    if any(not routes.get(role) for role in ("extractor", "analyst", "skeptic")):
        raise ValueError("The selected provider must be configured for extractor, analyst and skeptic")

    os.environ["SAMPLE_MODE"] = "false"
    os.environ["ENGINES_ENABLED"] = "true"
    engines = configured_engines(False)
    health = engines.health()
    if health.get("status") != "ok":
        raise ValueError("Engines sidecar is not ready")
    request = verified_sample_request()
    adapter = ZetarisAdapter(ZetarisClient.from_env())
    offline = DuckDBAdapter(REPO_ROOT / "data" / "sample")
    parity = (verified_parity(args.reuse_parity, offline, request["as_of"]) if args.reuse_parity else
              check_parity(adapter, offline, request["as_of"]))
    if not all(item["match"] for item in parity):
        raise ValueError("Zetaris/DuckDB parity failed; run integrations.zetaris.parity for details")

    destination.mkdir(parents=True)
    write_json(destination / "parity.json", parity, secrets)
    source_evidence = {}
    for name, path in (("parity", args.reuse_parity), ("bulk_receipts", args.bulk_receipts)):
        if path:
            source_evidence[name] = {"path": path.resolve().relative_to(REPO_ROOT).as_posix(),
                                     "sha256": digest(read_receipt_file(path))}
    if args.bulk_receipts:
        adapter = ReceiptCache(adapter, offline, args.bulk_receipts)
    query = AuditedQueries(adapter, destination / "queries.jsonl")
    engine_lock = threading.Lock()

    def record_engine(receipt):
        with engine_lock, (destination / "engine_requests.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(receipt, sort_keys=True) + "\n")

    engines.observer = record_engine
    engines = AuditedEngines(engines, destination, secrets)
    llm = AuditedLLM(
        ChainClient(routes, Cassette(destination / "llm_cassette.jsonl"), mode="record"),
        destination / "models.jsonl",
    )
    cases = []
    started = perf_counter()
    manifest = {"status": "running", "as_of": request["as_of"],
                "acceptance_profile": f"{args.llm_provider}+zetaris+engines",
                "llm_provider": expected_provider,
                "nightshift_required_for_this_profile": expected_provider == "meterless",
                "parity_execution": "reused-verified-report" if args.reuse_parity else "fresh-live",
                "source_evidence": source_evidence,
                "engines": health["engines"], "cases": cases,
                "selected_pools": args.pools, "submission_complete": False,
                "generated_at": dt.datetime.now(dt.UTC).isoformat()}
    write_json(destination / "manifest.json", manifest, secrets)
    try:
        # Small pools provide the first end-to-end evidence before the filing workload.
        for pool in args.pools:
            manifest["active_pool"] = pool
            manifest["stage"] = "pipeline"
            case = {**request, "pools": [pool], "top_k": 1}
            assert_payload(case, "RunRequest")
            folder = destination / pool
            folder.mkdir()
            write_json(folder / "input.json", case, secrets)
            print(json.dumps({"status": "running", "pool": pool}), flush=True)
            with (folder / "console.log").open("w", encoding="utf-8") as console:
                with contextlib.redirect_stdout(console):
                    output = run_pipeline(case, query=query, llm=llm, engines=engines,
                                          log_dir=folder)
            if isinstance(adapter, ReceiptCache):
                if adapter.integrity_failed:
                    raise ValueError("A prior bulk receipt failed integrity checks")
                output["warnings"].append(
                    "Bulk input windows may use an explicitly labelled local cache matched to prior Zetaris "
                    "row hashes; instrument evidence and verifier queries still use live Zetaris."
                )
            check_public_bytes((folder / "console.log").read_bytes(), secrets)
            original_trace = REPO_ROOT / output["trace_path"]
            raw_trace = original_trace.read_bytes()
            check_public_bytes(raw_trace, secrets)
            events = [json.loads(line) for line in raw_trace.splitlines()]
            # Keep the original trace file and bytes. The packaged reference is repo-relative.
            output["trace_path"] = original_trace.relative_to(REPO_ROOT).as_posix()
            files = {"input.json": write_json(folder / "input.json", case, secrets),
                     "output.json": write_json(folder / "output.json", output, secrets),
                     original_trace.name: {"bytes": len(raw_trace), "sha256": digest(raw_trace)}}
            manifest["stage"] = "validate-case"
            checked = validate_case(output, events, expected_provider=expected_provider)
            stored_output = RunStore().save(output)
            cases.append({"pool": pool, "run_id": output["run_id"], "files": files,
                          "stored_output": stored_output.relative_to(REPO_ROOT).as_posix(),
                          "recommendations": len(output["recommendations"]), **checked})
            write_json(destination / "manifest.json", manifest, secrets)
            print(json.dumps({"status": "ok", "pool": pool, **checked}), flush=True)
        check_public_bytes((destination / "llm_cassette.jsonl").read_bytes(), secrets)
        check_public_bytes((destination / "queries.jsonl").read_bytes(), secrets)
        check_public_bytes((destination / "models.jsonl").read_bytes(), secrets)
        manifest.update({**selection_result(cases, args.pools), "stage": "complete",
                         "elapsed_s": round(perf_counter() - started, 2),
                         "zetaris_queries": sum(item["backend"] == "zetaris" for item in query.calls),
                         "verified_cache_queries": sum(item["backend"] == "zetaris-verified-local-cache"
                                                       for item in query.calls)})
        lines = ["# Live sponsor acceptance examples", "",
                 f"Computed through Zetaris, {args.llm_provider} and the Meterless engines sidecar.", "",
                 "| Pool | Recommendation records | Live model calls | Explanation verdicts |",
                 "| --- | ---: | ---: | --- |"]
        for item in cases:
            lines.append(f"| {item['pool']} | {item['recommendations']} | "
                         f"{item['llm_calls']} | {json.dumps(item['verdicts'])} |")
        lines += ["", "Each pool folder contains input.json, output.json and the original trace.",
                  f"New live Zetaris queries: {manifest['zetaris_queries']}; "
                  f"prior-receipt-verified local queries: {manifest['verified_cache_queries']}.",
                  f"Parity execution: {manifest['parity_execution']}; source evidence is in manifest.json.",
                  f"Submission acceptance complete: {manifest['submission_complete']}.",
                  f"Acceptance profile: {manifest['acceptance_profile']}; sponsor service evidence is disclosed separately.",
                  "All tiers and verdicts are computed. Abstention remains a valid research result.",
                  "The current engine integration uses historical record counts, not prior accuracy.",
                  "Review model text and traces for privacy before publishing these artifacts."]
        (destination / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as error:
        manifest.update({"status": "failed", "failure_type": type(error).__name__})
        write_json(destination / "manifest.json", manifest, secrets)
        print(json.dumps({"status": "failed", "failure_type": type(error).__name__,
                          "stage": manifest.get("stage"), "pool": manifest.get("active_pool"),
                          "completed_cases": len(cases)}), flush=True)
        return 1
    write_json(destination / "manifest.json", manifest, secrets)
    print(json.dumps({**selection_result(cases, args.pools),
                      "cases": len(cases), "output": str(destination)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
