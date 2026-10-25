"""Start the API with an offline sample result available on a fresh checkout."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

from tradepulse.config import load_config
from tradepulse.contracts import REPO_ROOT, table_names, table_path
from tradepulse.guard import guard_request
from tradepulse.store import RunStore


def verified_sample_request(sample_root=None, *, today=None):
    """Validate frozen table identities and derive the request from the snapshot decision date."""
    root = Path(sample_root) if sample_root is not None else REPO_ROOT / "data/sample"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    as_of = dt.date.fromisoformat(manifest["as_of"])
    request = guard_request(
        {"as_of": as_of.isoformat(), "pools": list(load_config()["pools"])},
        today=today or dt.datetime.now(dt.UTC).date(),
        earliest=as_of,
    )
    if set(manifest["tables"]) != set(table_names()):
        raise ValueError("Sample manifest must contain the seven agreed tables")
    total = 0
    for name in table_names():
        item = manifest["tables"][name]
        path = table_path(name, root)
        if item["path"] != path.relative_to(root).as_posix():
            raise ValueError("Sample manifest contains an unexpected table path")
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Sample table resolves outside the snapshot")
        size = path.stat().st_size
        total += size
        if size != item["bytes"] or size == 0 or total >= 25_000_000:
            raise ValueError("Sample table size does not match the frozen snapshot")
        with path.open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != item["sha256"]:
                raise ValueError("Sample table hash does not match the frozen snapshot")
    return request


def ensure_sample_run(store=None, *, runner=None, sample_root=None, today=None):
    """Reuse a saved run or compute the frozen sample once; never record models automatically."""
    from tradepulse.pipeline import record_llm, run_pipeline, sample_mode

    if not sample_mode():
        return None
    store = store if store is not None else RunStore()
    existing = store.latest()
    if existing is not None:
        return existing
    if record_llm():
        raise ValueError("Record models explicitly before starting the API")
    request = verified_sample_request(sample_root, today=today)
    output = (runner or run_pipeline)(request)
    store.save(output)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    try:
        output = ensure_sample_run()
        if output is not None:
            print(json.dumps({"run_id": output["run_id"], "data_mode": output["data_mode"],
                              "recommendations": len(output["recommendations"])}), flush=True)
    except Exception as exc:
        print(f"Startup failed: {type(exc).__name__}; verify the sample and run settings.",
              file=sys.stderr)
        return 1
    import uvicorn

    uvicorn.run("tradepulse.api:app", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
