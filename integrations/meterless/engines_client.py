"""Python client for the Node engines sidecar (task D5). The HTTP API is specified in
integrations/engines/API.md. Every method validates its payloads against contracts where a
contract exists (GraphEdge, ExtractedEvent) before sending."""

from __future__ import annotations


class EnginesError(RuntimeError):
    pass


class EnginesClient:
    def __init__(self, base_url: str, timeout_s: float = 30.0, session=None) -> None:
        raise NotImplementedError("D5")

    def health(self) -> dict:
        raise NotImplementedError("D5")

    def ingest_events(self, events: list[dict]) -> dict:
        """POST /world-model/events. Each event satisfies $defs/ExtractedEvent; invalid -> ValueError."""
        raise NotImplementedError("D5")

    def upsert_edges(self, edges: list[dict]) -> dict:
        """POST /world-model/edges. Each edge satisfies $defs/GraphEdge; invalid -> ValueError."""
        raise NotImplementedError("D5")

    def snapshot(self, as_of: str) -> dict:
        """GET /world-model/snapshot?as_of=YYYY-MM-DD -> {"edges": [...], "events": [...]}."""
        raise NotImplementedError("D5")

    def remember(self, records: list[dict]) -> dict:
        """POST /hmem/records (recommendations to remember)."""
        raise NotImplementedError("D5")

    def recall(self, symbol: str, as_of: str, k: int = 10) -> list[dict]:
        """POST /hmem/query."""
        raise NotImplementedError("D5")

    def settle(self, record_id: str, outcome: dict) -> dict:
        """POST /hmem/feedback."""
        raise NotImplementedError("D5")

    def conflicts(self, symbol: str) -> list[dict]:
        """GET /hmem/conflicts?symbol=..."""
        raise NotImplementedError("D5")
