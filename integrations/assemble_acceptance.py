"""Index previously accepted live cases without re-running models, queries or engines.

Source files remain untouched. The index references their original paths and SHA-256 hashes;
keep those directories alongside the index when publishing an evidence bundle.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from tradepulse.contracts import REPO_ROOT, assert_payload

from .live_acceptance import ALL_POOLS, digest, selection_result, validate_case, write_json

MAX_FILE_BYTES = 64 * 1024 * 1024


def read_artifact(path: Path, root: Path) -> bytes:
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Acceptance source escapes its directory")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Acceptance source exceeds the artifact limit")
    return path.read_bytes()


def collect_cases(sources: list[Path], provider: str) -> tuple[list[dict], list[dict], str]:
    if provider not in {"glm", "meterless"}:
        raise ValueError("Unknown acceptance provider")
    if not 1 <= len(sources) <= 3:
        raise ValueError("Choose one to three source acceptance directories")
    records, evidence, dates, seen = [], [], set(), set()
    expected_profile = f"{'glm' if provider == 'glm' else 'nightshift'}+zetaris+engines"
    for source in sources:
        source = source.resolve()
        if not source.is_relative_to(REPO_ROOT / "runs"):
            raise ValueError("Acceptance sources must be under runs/")
        raw_manifest = read_artifact(source / "manifest.json", source)
        manifest = json.loads(raw_manifest)
        if manifest.get("acceptance_profile") != expected_profile:
            raise ValueError("Source acceptance profile does not match the selected provider")
        dates.add(manifest["as_of"])
        if len(dates) != 1:
            raise ValueError("Source cases must share the same decision date")
        accepted = manifest.get("cases", [])
        if not isinstance(accepted, list) or len(accepted) > 3:
            raise ValueError("Invalid accepted-case list")
        evidence.append({"manifest": (source / "manifest.json").relative_to(REPO_ROOT).as_posix(),
                         "sha256": digest(raw_manifest), "source_status": manifest.get("status")})
        for record in accepted:
            pool = record["pool"]
            if pool not in ALL_POOLS or pool in seen:
                raise ValueError("Unknown or duplicate accepted pool")
            folder = source / pool
            files = record["files"]
            if not isinstance(files, dict) or not 3 <= len(files) <= 4:
                raise ValueError("Invalid accepted-case file manifest")
            checked_files = {}
            for name, expected in files.items():
                if Path(name).name != name or "/" in name or "\\" in name:
                    raise ValueError("Case file must have a plain filename")
                raw = read_artifact(folder / name, source)
                if len(raw) != expected["bytes"] or digest(raw) != expected["sha256"]:
                    raise ValueError("Accepted artifact no longer matches its recorded hash")
                checked_files[name] = raw
            request = json.loads(checked_files["input.json"])
            output = json.loads(checked_files["output.json"])
            assert_payload(request, "RunRequest")
            if (request["pools"] != [pool] or request["as_of"] != manifest["as_of"]
                    or output["as_of"] != request["as_of"] or output["request"] != request
                    or [item["pool"] for item in output["pools"]] != [pool]
                    or output["run_id"] != record["run_id"]):
                raise ValueError("Accepted case identity does not match its input and manifest")
            trace_name = Path(output["trace_path"]).name
            if trace_name not in checked_files or not trace_name.endswith(".jsonl"):
                raise ValueError("Recorded original trace is missing")
            lines = checked_files[trace_name].splitlines()
            if len(lines) > 100000:
                raise ValueError("Trace exceeds the event limit")
            events = [json.loads(line) for line in lines]
            if any(event.get("run_id") != output["run_id"] for event in events):
                raise ValueError("Trace contains a different run")
            checked = validate_case(output, events, expected_provider=provider)
            records.append({"pool": pool, "run_id": output["run_id"],
                            "source_directory": folder.relative_to(REPO_ROOT).as_posix(),
                            "files": files, "recommendations": len(output["recommendations"]),
                            **checked})
            seen.add(pool)
    if not records:
        raise ValueError("No previously accepted live case was found")
    return sorted(records, key=lambda item: ALL_POOLS.index(item["pool"])), evidence, dates.pop()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, action="append", required=True)
    parser.add_argument("--llm-provider", choices=("glm", "nightshift"), default="glm")
    parser.add_argument("--output", type=Path, required=True, help="new evidence index under runs/")
    args = parser.parse_args(argv)
    destination = args.output.resolve()
    if not destination.is_relative_to(REPO_ROOT / "runs") or destination.exists():
        raise ValueError("Choose a new evidence index directory under runs/")
    provider = "glm" if args.llm_provider == "glm" else "meterless"
    cases, sources, as_of = collect_cases(args.source, provider)
    selected = [case["pool"] for case in cases]
    result = {**selection_result(cases, selected), "as_of": as_of, "cases": cases,
              "acceptance_profile": f"{args.llm_provider}+zetaris+engines", "sources": sources,
              "assembly_only": True, "new_network_calls": 0,
              "generated_at": dt.datetime.now(dt.UTC).isoformat()}
    destination.mkdir(parents=True)
    write_json(destination / "manifest.json", result, [])
    lines = ["# Accepted live cases", "", "An index of original evidence; no model was re-run.", "",
             "| Pool | Run | Records | Live model calls | Original source |", "| --- | --- | ---: | ---: | --- |"]
    for case in cases:
        lines.append(f"| {case['pool']} | {case['run_id']} | {case['recommendations']} | "
                     f"{case['llm_calls']} | {case['source_directory']} |")
    lines += ["", f"Three-pool engineering acceptance complete: {result['submission_complete']}.",
              "Source hashes and verdicts are preserved; failed source attempts remain failed.",
              "Keep the original source directories, root model/query receipts and parity reports.",
              "This index is not a standalone copy of those artifacts or a full event eligibility attestation."]
    (destination / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "cases": len(cases),
                      "submission_complete": result["submission_complete"], "new_network_calls": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
