"""Interfaces the core depends on. Member D's integrations implement them; tests use fakes.

Keeping the core on these protocols means the pipeline runs on fakes before the sponsor
integrations exist, and the sponsor code can change without touching the core.
"""

from __future__ import annotations

from typing import Any, Protocol


class QueryResultLike(Protocol):
    template: str
    params: dict
    sql: str
    backend: str
    df: Any            # pandas.DataFrame
    rows_sha256: str
    elapsed_ms: int


class QueryPort(Protocol):
    """integrations.zetaris.adapter.DuckDBAdapter / ZetarisAdapter."""

    backend: str

    def run(self, template: str, params: dict) -> QueryResultLike: ...


class LLMResponseLike(Protocol):
    text: str
    provider: str
    model: str
    tokens_in: int | None
    tokens_out: int | None
    cassette_key: str
    replayed: bool


class LLMPort(Protocol):
    """integrations.meterless.llm.ChainClient. Roles: extractor, guard, analyst, skeptic."""

    def complete(self, role: str, messages: list[dict], response_schema: dict | None = None) -> LLMResponseLike: ...


class EnginesPort(Protocol):
    """integrations.meterless.engines_client.EnginesClient (World Model + H-MEM sidecar)."""

    def ingest_events(self, events: list[dict]) -> dict: ...
    def upsert_edges(self, edges: list[dict]) -> dict: ...
    def snapshot(self, as_of: str) -> dict: ...
    def remember(self, records: list[dict]) -> dict: ...
    def recall(self, symbol: str, as_of: str, k: int = 10) -> list[dict]: ...
    def settle(self, record_id: str, outcome: dict) -> dict: ...
    def conflicts(self, symbol: str) -> list[dict]: ...
