"""Read-only local-cache identity check: no model, HTTP or engine operations."""

import argparse
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

from tradepulse.config import load_config
from tradepulse.contracts import REPO_ROOT
from tradepulse.extract.grounding import ExtractionCache, ExtractionIdentityError
from tradepulse.extract.runner import run_extraction

from .live_acceptance import write_json
from .zetaris.adapter import DuckDBAdapter


class NoModel:
    def complete(self, *_args, **_kwargs):
        raise AssertionError("Read-only preflight must not call a model")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    destination = args.report.resolve()
    if not destination.is_relative_to(REPO_ROOT / "runs") or destination.exists():
        raise ValueError("Choose a new diagnostic file under runs/")
    root = REPO_ROOT / "data/sample"
    as_of = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["as_of"]
    start = (dt.date.fromisoformat(as_of) - dt.timedelta(days=load_config()["backtest"]["window_days"])).isoformat()
    docs = DuckDBAdapter(root).run("filing_texts_window", {"start": start, "end": as_of}).df
    if len(docs) > 10000:
        raise ValueError("Document preflight exceeds its bound")
    cache = ExtractionCache(REPO_ROOT / "data/cache/extraction_cache.jsonl")
    groups = defaultdict(list)
    for doc in docs.to_dict("records"):
        for event in cache.get(doc["sha256"]) if cache.has(doc["sha256"]) else []:
            groups[event["event_id"]].append((doc["symbol"], event))
    repeated = []
    for identity, records in groups.items():
        if len(records) < 2:
            continue
        first = records[0][1]
        fields = sorted({key for _, event in records for key in first.keys() | event.keys()
                         if first.get(key) != event.get(key)})
        repeated.append({"event_id": identity, "copies": len(records),
                         "source_symbols": sorted({symbol for symbol, _ in records}),
                         "different_fields": fields})
    report = {"status": "cache_preflight_ok", "read_only": True, "as_of": as_of,
              "new_model_calls": 0, "new_network_calls": 0, "documents": len(docs),
              "legacy_duplicate_groups": repeated}
    try:
        checked = run_extraction(docs, NoModel(), cache, max_docs=0)
        report.update(cached_documents=checked["cached"], needs_extraction=checked["skipped"],
                      unique_cached_events=len(checked["events"]),
                      collapsed_identical_events=checked["duplicate_events"])
    except ExtractionIdentityError:
        report.update(status="identity_conflict", failure_type="ExtractionIdentityError")
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_json(destination, report, [])
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "cache_preflight_ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
