"""LLM provider chain with record/replay (task D4).

When METERLESS_TOKEN_FILE is set, Nightshift is the first provider for every role. NVIDIA NIM may
remain configured as a bounded fallback. This makes Nightshift a working provider in the actual
extraction and explanation path instead of a decorative health check.

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
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit, urlunsplit

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
    try:
        token = Path(path).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        raise ValueError("Runtime token file is unavailable") from None
    if not token or token == "rt-local":
        raise ValueError("Runtime token is empty or a placeholder")
    return token


def runtime_status(get: Callable[[str], int], base_url: str) -> str:
    """Call get(f"{base_url}/models"), which returns an HTTP status code or raises.
    Map 200 -> 'online', 401/403 -> 'unauthorized', and any other status or exception ->
    'offline'."""
    try:
        status = get(f"{base_url.rstrip('/')}/models")
    except Exception:
        return "offline"
    if status == 200:
        return "online"
    return "unauthorized" if status in (401, 403) else "offline"


def normalise_meterless_base_url(value: str) -> str:
    """Normalise the Nightshift URLs people commonly paste to one <host>/v1 base URL."""
    candidate = value.strip()
    if not candidate:
        candidate = "http://127.0.0.1:8088"
    if "://" not in candidate:
        candidate = f"http://{candidate}"
    parsed = urlsplit(candidate)
    if (parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("Meterless base URL must be an HTTP(S) URL without credentials")
    path = parsed.path.rstrip("/")
    for suffix in ("/chat/completions", "/models", "/healthz"):
        if path.endswith(suffix):
            path = path[:-len(suffix)].rstrip("/")
    if path.endswith("/v1"):
        path = path[:-3].rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, f"{path}/v1", "", ""))


def cassette_key(role: str, messages: list[dict], response_schema: dict | None) -> str:
    """sha256 hex of json.dumps({"role", "messages", "schema"}, sort_keys=True, ensure_ascii=False).
    Provider and model are NOT part of the key, so a replay works whichever provider answered."""
    return _sha({"role": role, "messages": messages, "schema": response_schema})


class Cassette:
    """A JSON-lines file of {"key", "text", "provider", "model", "tokens_in", "tokens_out"}."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._entries: dict[str, dict] = {}
        self._lock = threading.Lock()
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    entry = json.loads(line)
                    self._entries[entry["key"]] = entry

    def get(self, key: str) -> dict:
        """Recorded entry or raise CassetteMiss."""
        with self._lock:
            if key not in self._entries:
                raise CassetteMiss(key)
            return dict(self._entries[key])

    def put(self, key: str, entry: dict) -> None:
        """Append, and update the in-memory index. Re-recording a key keeps the newest entry."""
        with self._lock:
            self._put(key, entry)

    def _put(self, key: str, entry: dict) -> None:
        recorded = {"key": key, **{field: entry[field] for field in
                    ("text", "provider", "model", "tokens_in", "tokens_out")}}
        line = json.dumps(recorded, ensure_ascii=False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab+") as stream:
            stream.seek(0, os.SEEK_END)
            if stream.tell():
                stream.seek(-1, os.SEEK_END)
                if stream.read(1) != b"\n":
                    stream.write(b"\n")
            stream.write((line + "\n").encode("utf-8"))
        self._entries[key] = recorded


class ChainClient:
    """routes: {role: [(provider_name, model, call)]}, where call(messages, model, response_schema)
    returns (text, tokens_in, tokens_out) or raises. mode: 'live', 'record' or 'replay'."""

    def __init__(self, routes: dict, cassette: Cassette | None, mode: str = "live") -> None:
        if mode not in {"live", "record", "replay"}:
            raise ValueError("Unknown LLM mode")
        if mode in {"record", "replay"} and cassette is None:
            raise ValueError("Record and replay modes require a cassette")
        self.routes = {role: tuple(route) for role, route in routes.items()}
        self.cassette = cassette
        self.mode = mode

    def complete(self, role: str, messages: list[dict], response_schema: dict | None = None) -> LLMResponse:
        """replay: cassette only. live/record: try each provider of the role in order. The first
        success wins; record mode stores it. When all fail, raise AllProvidersFailed listing the
        provider names and error types. An unknown role raises ValueError."""
        if role not in ROLES:
            raise ValueError("Unknown LLM role")
        key = cassette_key(role, messages, response_schema)
        if self.mode == "replay":
            entry = self.cassette.get(key)
            return LLMResponse(entry["text"], entry["provider"], entry["model"],
                               entry["tokens_in"], entry["tokens_out"], key, True)
        failures: list[str] = []
        for provider, model, call in self.routes.get(role, ()):
            try:
                text, tokens_in, tokens_out = call(messages, model, response_schema)
                if not isinstance(text, str) or not text.strip():
                    raise ValueError("Empty provider response")
            except Exception as error:
                failures.append(f"{provider}: {type(error).__name__}")
                continue
            response = LLMResponse(text, provider, model, tokens_in, tokens_out, key, False)
            if self.mode == "record":
                self.cassette.put(key, {"text": text, "provider": provider, "model": model,
                                        "tokens_in": tokens_in, "tokens_out": tokens_out})
            return response
        raise AllProvidersFailed("; ".join(failures) or f"No providers configured for {role}")


def build_routes_from_env() -> dict:
    """Build bounded OpenAI-compatible routes. A configured Nightshift route is first for all
    roles, with optional NIM fallbacks. Without Nightshift, existing NIM settings still apply."""
    from openai import OpenAI

    def caller(client):
        def call(messages: list[dict], model: str, schema: dict | None):
            # No response_format: strict json_schema mode is not supported uniformly by
            # OpenAI-compatible servers (Meterless, NIM). Prompts ask for JSON and the core parses
            # replies tolerantly; malformed replies fail verification and are retried.
            response = client.chat.completions.create(model=model, messages=messages)
            text = response.choices[0].message.content
            usage = response.usage
            return (text, usage.prompt_tokens if usage else None,
                    usage.completion_tokens if usage else None)

        return call

    routes: dict[str, list] = {}
    token_file = os.environ.get("METERLESS_TOKEN_FILE")
    if token_file:
        meterless = OpenAI(
            base_url=normalise_meterless_base_url(
                os.environ.get("METERLESS_BASE_URL") or "http://127.0.0.1:8088/v1"
            ),
            api_key=read_token(token_file), timeout=180.0, max_retries=0,
            default_headers={"meterless-app": os.environ.get("METERLESS_APP") or "tradepulse",
                             "meterless-scope": "user"},
        )
        route = ("meterless", os.environ.get("METERLESS_MODEL") or "meterless/auto",
                 caller(meterless))
        for role in ROLES:
            routes[role] = [route]

    api_key = os.environ.get("NVIDIA_API_KEY")
    if api_key:
        nim = OpenAI(
            base_url=os.environ.get("NVIDIA_BASE_URL") or "https://integrate.api.nvidia.com/v1",
            api_key=api_key, timeout=180.0, max_retries=0,
        )
        call = caller(nim)
        analyst = os.environ.get("NIM_ANALYST_MODEL")
        skeptic = os.environ.get("NIM_SKEPTIC_MODEL")
        extractor = os.environ.get("NIM_EXTRACTOR_MODEL") or analyst
        if extractor:
            for role in ("extractor", "guard"):
                routes.setdefault(role, []).append(("nim", extractor, call))
        if analyst:
            routes.setdefault("analyst", []).append(("nim", analyst, call))
        if skeptic:
            routes.setdefault("skeptic", []).append(("nim", skeptic, call))
    return routes


def _sha(obj) -> str:  # helper you may use
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
