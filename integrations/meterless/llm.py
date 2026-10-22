"""LLM provider chain with record/replay (task D4).

Roles and default routes (fallback order):
    extractor, guard -> Meterless Runtime (METERLESS_MODEL, default meterless/fast) -> NVIDIA NIM
    analyst          -> NVIDIA NIM (NIM_ANALYST_MODEL)
    skeptic          -> NVIDIA NIM (NIM_SKEPTIC_MODEL; a different model family from the analyst)

Every provider is OpenAI-compatible (/v1/chat/completions). Meterless Runtime facts:
- base http://127.0.0.1:8088/v1
- Authorization: Bearer <token read from METERLESS_TOKEN_FILE>; the placeholder 'rt-local' is
  rejected by the runtime
- headers meterless-app: <METERLESS_APP> and meterless-scope: user
- status from GET /v1/models: 200 online, 401/403 unauthorized
- 180 s timeout

SAMPLE_MODE uses mode="replay": answers come only from the cassette, and nothing touches the
network. A missing answer is an error, never a silent live call. mode="record" calls providers
and stores their answers.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROLES = ("extractor", "guard", "analyst", "skeptic")


class CassetteMiss(KeyError):
    """Replay mode found no recorded answer for this request."""


class AllProvidersFailed(RuntimeError):
    """Every provider in the role's route failed."""


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    tokens_in: int | None
    tokens_out: int | None
    cassette_key: str
    replayed: bool


def read_token(path: str | Path) -> str:
    """Read and strip the runtime token. A missing file, an empty file or the placeholder
    'rt-local' raises ValueError (the message never contains the token)."""
    raise NotImplementedError("D4")


def runtime_status(get: Callable[[str], int], base_url: str) -> str:
    """Call get(f"{base_url}/models"), which returns an HTTP status code or raises.
    Map 200 -> 'online', 401/403 -> 'unauthorized', and any other status or exception ->
    'offline'."""
    raise NotImplementedError("D4")


def cassette_key(role: str, messages: list[dict], response_schema: dict | None) -> str:
    """sha256 hex of json.dumps({"role", "messages", "schema"}, sort_keys=True, ensure_ascii=False).
    Provider and model are NOT part of the key, so a replay works whichever provider answered."""
    raise NotImplementedError("D4")


class Cassette:
    """A JSON-lines file of {"key", "text", "provider", "model", "tokens_in", "tokens_out"}."""

    def __init__(self, path: Path) -> None:
        raise NotImplementedError("D4")

    def get(self, key: str) -> dict:
        """Recorded entry or raise CassetteMiss."""
        raise NotImplementedError("D4")

    def put(self, key: str, entry: dict) -> None:
        """Append, and update the in-memory index. Re-recording a key keeps the newest entry."""
        raise NotImplementedError("D4")


class ChainClient:
    """routes: {role: [(provider_name, model, call)]}, where call(messages, model, response_schema)
    returns (text, tokens_in, tokens_out) or raises. mode: 'live', 'record' or 'replay'."""

    def __init__(self, routes: dict, cassette: Cassette | None, mode: str = "live") -> None:
        raise NotImplementedError("D4")

    def complete(self, role: str, messages: list[dict], response_schema: dict | None = None) -> LLMResponse:
        """replay: cassette only. live/record: try each provider of the role in order. The first
        success wins; record mode stores it. When all fail, raise AllProvidersFailed listing the
        provider names and error types. An unknown role raises ValueError."""
        raise NotImplementedError("D4")


def build_routes_from_env() -> dict:
    """Build the default routes above from environment variables using the `openai` package
    (base_url and api_key per provider, timeout 180 s). Not unit-tested; covered by the live
    smoke test."""
    raise NotImplementedError("D4")


def _sha(obj) -> str:  # helper you may use
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
