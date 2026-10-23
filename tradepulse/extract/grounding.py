"""Deterministic grounding check for LLM-extracted events, plus the extraction cache.

The extractor (an LLM) proposes ExtractedEvent objects. Nothing it says is trusted: every quote
must appear in the source document, timestamps must be point-in-time, and the object must satisfy
the contract.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from copy import deepcopy
from pathlib import Path

from tradepulse.contracts import validate_payload

POSITIVE_SIGNALS = ("demand_exceeds_supply", "capacity_constrained", "price_increase", "guidance_raised",
                    "record_backlog")
NEGATIVE_SIGNALS = ("guidance_cut", "demand_weakness", "inventory_build", "price_decrease")


def normalize_text(text: str) -> str:
    """Comparison form: curly quotes -> straight (’ ‘ -> ', “ ” -> "), en/em dashes -> '-',
    non-breaking spaces -> space, whitespace runs -> one space, stripped, case-folded."""
    table = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                          "\u2013": "-", "\u2014": "-", "\u00a0": " "})
    return " ".join(text.translate(table).split()).casefold()


def quote_in_document(quote: str, document: str) -> bool:
    """normalize_text(quote) is a non-empty substring of normalize_text(document)."""
    normalized = normalize_text(quote)
    return bool(normalized) and normalized in normalize_text(document)


def make_event_id(doc_sha256: str, symbol: str, event_type: str, quote: str) -> str:
    """First 24 hex chars of sha256 over "doc_sha256|symbol|event_type|normalize_text(quote)"."""
    text = f"{doc_sha256}|{symbol}|{event_type}|{normalize_text(quote)}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def grounding_problems(event: dict, document: str, doc_sha256: str, doc_available_at: dt.datetime) -> list[str]:
    """Every reason the event must be rejected; an empty list means it is grounded.

    Problems (one string each, starting with the listed prefix):
    - "schema: ..."       the event fails $defs/ExtractedEvent (first error message)
    - "doc_sha256: ..."   event["doc_sha256"] != doc_sha256
    - "quote: ..."        event["quote"] is not in the document
    - "demand_quote: ..." a demand_signals quote is not in the document (one problem per signal)
    - "polarity: ..."     a demand signal whose polarity disagrees with POSITIVE/NEGATIVE_SIGNALS
    - "available_at: ..." event["available_at"] is earlier than doc_available_at
    - "event_id: ..."     event["event_id"] != make_event_id(...)
    Schema failure returns only the schema problem (the other checks need valid fields).
    """
    errors = validate_payload(event, "ExtractedEvent")
    if errors:
        return [f"schema: {errors[0]}"]
    problems = []
    if event["doc_sha256"] != doc_sha256:
        problems.append("doc_sha256: does not match source document")
    if not quote_in_document(event["quote"], document):
        problems.append("quote: not found in source document")
    for index, signal in enumerate(event["demand_signals"]):
        if not quote_in_document(signal["quote"], document):
            problems.append(f"demand_quote: signal {index} not found in source document")
        expected = 1 if signal["type"] in POSITIVE_SIGNALS else -1
        if signal["polarity"] != expected:
            problems.append(f"polarity: signal {index} disagrees with {signal['type']}")
    available_at = dt.datetime.fromisoformat(event["available_at"].upper().replace("Z", "+00:00"))
    if doc_available_at.utcoffset() is None:
        problems.append("available_at: source document timing must be timezone-aware")
    elif available_at < doc_available_at:
        problems.append("available_at: earlier than source document availability")
    expected_id = make_event_id(doc_sha256, event["symbol"], event["event_type"], event["quote"])
    if event["event_id"] != expected_id:
        problems.append("event_id: does not match source document and event")
    return problems


def demand_language_score(events: list[dict]) -> float | None:
    """Signed intensity in [-1, 1] over all demand signals of the given events:
    (n_pos - n_neg) / (n_pos + n_neg + 1). None when there is no signal."""
    n_pos, n_neg = 0, 0
    for event in events:
        for signal in event["demand_signals"]:
            n_pos += int(signal["polarity"] == 1)
            n_neg += int(signal["polarity"] == -1)
    return (n_pos - n_neg) / (n_pos + n_neg + 1) if n_pos + n_neg else None


class ExtractionCache:
    """JSON-lines file of {"doc_sha256", "events": [...]}. The newest line for a document wins."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._events: dict[str, list[dict]] = {}
        if self.path.exists():
            with self.path.open(encoding="utf-8") as source:
                for line in source:
                    if line.strip():
                        record = json.loads(line)
                        self._events[record["doc_sha256"]] = record["events"]

    def has(self, doc_sha256: str) -> bool:
        return doc_sha256 in self._events

    def get(self, doc_sha256: str) -> list[dict]:
        """Cached events, or KeyError."""
        return deepcopy(self._events[doc_sha256])

    def put(self, doc_sha256: str, events: list[dict]) -> None:
        line = json.dumps({"doc_sha256": doc_sha256, "events": events}, sort_keys=True, allow_nan=False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as target:
            target.write(line + "\n")
        self._events[doc_sha256] = json.loads(line)["events"]
