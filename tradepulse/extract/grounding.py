"""Deterministic grounding check for LLM-extracted events, plus the extraction cache.

The extractor (an LLM) proposes ExtractedEvent objects. Nothing it says is trusted: every quote
must appear in the source document, timestamps must be point-in-time, and the object must satisfy
the contract.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

POSITIVE_SIGNALS = ("demand_exceeds_supply", "capacity_constrained", "price_increase", "guidance_raised",
                    "record_backlog")
NEGATIVE_SIGNALS = ("guidance_cut", "demand_weakness", "inventory_build", "price_decrease")


def normalize_text(text: str) -> str:
    """Comparison form: curly quotes -> straight (’ ‘ -> ', “ ” -> "), en/em dashes -> '-',
    non-breaking spaces -> space, whitespace runs -> one space, stripped, case-folded."""
    raise NotImplementedError


def quote_in_document(quote: str, document: str) -> bool:
    """normalize_text(quote) is a non-empty substring of normalize_text(document)."""
    raise NotImplementedError


def make_event_id(doc_sha256: str, symbol: str, event_type: str, quote: str) -> str:
    """First 24 hex chars of sha256 over "doc_sha256|symbol|event_type|normalize_text(quote)"."""
    raise NotImplementedError


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
    raise NotImplementedError


def demand_language_score(events: list[dict]) -> float | None:
    """Signed intensity in [-1, 1] over all demand signals of the given events:
    (n_pos - n_neg) / (n_pos + n_neg + 1). None when there is no signal."""
    raise NotImplementedError


class ExtractionCache:
    """JSON-lines file of {"doc_sha256", "events": [...]}. The newest line for a document wins."""

    def __init__(self, path: Path) -> None:
        raise NotImplementedError

    def has(self, doc_sha256: str) -> bool:
        raise NotImplementedError

    def get(self, doc_sha256: str) -> list[dict]:
        """Cached events, or KeyError."""
        raise NotImplementedError

    def put(self, doc_sha256: str, events: list[dict]) -> None:
        raise NotImplementedError
