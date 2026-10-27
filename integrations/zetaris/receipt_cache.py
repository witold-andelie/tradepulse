"""Explicit reuse of frozen local results proven equal to prior real Zetaris receipts.

Only large input windows may be cached. Instrument evidence and verifier queries remain live.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from tradepulse.contracts import REPO_ROOT

from .parity import fixed_params
from .templates import list_templates

_BULK = frozenset({"price_pool_window", "pageviews_pool_window", "facts_tag_window", "filing_texts_window"})


def read_receipt_file(path: Path) -> bytes:
    if not path.resolve().is_relative_to(REPO_ROOT / "runs") or path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Choose an existing bounded receipt under runs/")
    return path.read_bytes()


def verified_parity(path: Path, offline, as_of: str) -> list[dict]:
    payload = json.loads(read_receipt_file(path))
    cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(cases, list) or len(cases) != len(list_templates()):
        raise ValueError("Prior parity must contain every template exactly once")
    seen = set()
    for case in cases:
        template = case["template"]
        if template in seen or template not in list_templates() or case["params"] != fixed_params(template, as_of):
            raise ValueError("Prior parity identity or decision date mismatch")
        current = offline.run(template, case["params"])
        if (case.get("match") is not True or case["duckdb_rows"] != len(current.df)
                or case["zetaris_rows"] != len(current.df)
                or case["duckdb_sha256"] != current.rows_sha256
                or case["zetaris_sha256"] != current.rows_sha256):
            raise ValueError("Prior parity does not match the current frozen sample")
        seen.add(template)
    return cases


class ReceiptCache:
    backend = "zetaris-with-verified-cache"

    def __init__(self, live, offline, receipts: Path):
        self.live, self.offline = live, offline
        self.hits = 0
        self.integrity_failed = False
        self.receipts = {}
        for line in read_receipt_file(receipts).splitlines():
            entry = json.loads(line)
            if entry.get("backend") != "zetaris" or entry.get("template") not in _BULK:
                continue
            key = self._key(entry["template"], entry["params"])
            previous = self.receipts.get(key)
            if previous and (previous["rows"], previous["rows_sha256"]) != (entry["rows"], entry["rows_sha256"]):
                raise ValueError("Conflicting prior Zetaris receipts")
            self.receipts[key] = entry

    @staticmethod
    def _key(template, params):
        return json.dumps([template, params], sort_keys=True)

    def run(self, template, params):
        receipt = self.receipts.get(self._key(template, params))
        if template not in _BULK or receipt is None:
            return self.live.run(template, params)
        result = self.offline.run(template, params)
        if len(result.df) != receipt["rows"] or result.rows_sha256 != receipt["rows_sha256"]:
            self.integrity_failed = True
            raise ValueError("Frozen result does not match its prior Zetaris receipt")
        self.hits += 1
        return replace(result, backend="zetaris-verified-local-cache")
