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
- 180 s default SDK timeout; explicit local overrides remain bounded

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
from time import perf_counter
from typing import Callable
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from .error_checks import error_signals

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


def normalise_hosted_base_url(value: str) -> str:
    """Preserve a configured provider's routing prefix; accept a pasted completion URL."""
    parsed = urlsplit(value.strip())
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("GLM_BASE_URL must be an HTTP(S) URL without credentials")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Remote GLM_BASE_URL requires HTTPS")
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        path = path[:-len("/chat/completions")]
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def read_glm_api_key() -> str:
    """Read an existing private key; optionally reference OpenCode's existing Go credential.

    Credentials remain in memory, never copied into generated configuration or receipts.
    The JSON source is opt-in and selects exactly one provider entry.
    """
    if os.environ.get("GLM_API_KEY"):
        return os.environ["GLM_API_KEY"]
    if os.environ.get("GLM_API_KEY_FILE"):
        return read_token(Path(os.environ["GLM_API_KEY_FILE"]).expanduser())
    auth_file = os.environ.get("GLM_OPENCODE_AUTH_FILE")
    if auth_file:
        try:
            path = Path(auth_file).expanduser()
            if path.stat().st_size > 65536:
                raise ValueError
            payload = json.loads(path.read_text(encoding="utf-8"))
            entry = payload.get("opencode-go")
            if not isinstance(entry, dict) or entry.get("type") != "api":
                raise ValueError
            key = entry.get("key")
            if not isinstance(key, str) or not key.strip() or len(key) > 8192:
                raise ValueError
            return key.strip()
        except (OSError, ValueError, AttributeError):
            raise ValueError("GLM_OPENCODE_AUTH_FILE has no usable opencode-go API credential") from None
    raise ValueError("Configure GLM_API_KEY, GLM_API_KEY_FILE or GLM_OPENCODE_AUTH_FILE privately")


def advertised_model_ids(payload: object) -> list[str]:
    """Read the actual endpoint catalog; M1 editions can expose concrete webllm model IDs."""
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("Nightshift model discovery requires a data list")
    values = payload["data"]
    if len(values) > 1000:
        raise ValueError("Nightshift model catalog exceeds the work limit")
    ids = []
    for item in values:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError("Nightshift model catalog contains an invalid ID")
        ids.append(item["id"])
    if not ids:
        raise ValueError("Nightshift did not advertise any models")
    return ids


def require_advertised_model(payload: object, selected: str) -> list[str]:
    ids = advertised_model_ids(payload)
    if selected not in ids:
        raise ValueError("Configured METERLESS_MODEL is not in the runtime model catalog")
    return ids


def _bounded_setting(name: str, default: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        raise ValueError(f"{name} must be an integer") from None
    if not 1 <= value <= maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}")
    return value


def _usage_count(usage, field: str) -> int | None:
    value = getattr(usage, field, None)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _schema_messages(messages: list[dict], schema: dict | None) -> list[dict]:
    """Make the existing schema visible to small models without requiring JSON-mode support."""
    prepared = [dict(message) for message in messages]
    if schema is None:
        return prepared
    instruction = ("\n\nRESPONSE SCHEMA:\n" + json.dumps(schema, ensure_ascii=False) +
                   "\nReturn only one JSON object matching this schema. Keep text concise.")
    if "claims" in schema.get("properties", {}):
        instruction += (
            " Prefer one short, well-supported claim. Copy evidence IDs exactly from the "
            "brackets in EVIDENCE, without prefixes, suffixes or row numbers. Price evidence "
            "alone cannot establish an event, relationship or cause of a ranking. If support "
            "is insufficient, return no claims and explain the limitation. Never invent facts."
        )
    if prepared and prepared[0].get("role") == "system":
        prepared[0]["content"] = str(prepared[0].get("content", "")) + instruction
    else:
        prepared.insert(0, {"role": "system", "content": instruction.strip()})
    return prepared


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


def build_routes_from_env(*, diagnostics: Callable[[dict], None] | None = None) -> dict:
    """Build bounded OpenAI-compatible routes. A configured Nightshift route is first for all
    roles, with optional NIM fallbacks. Without Nightshift, existing NIM settings still apply."""
    from openai import OpenAI

    def caller(client, *, concurrency=None, max_tokens=None, output_format="prompt",
               request_timeout=180, queue_timeout=180, reasoning_effort=None,
               json_temperature=0):
        def call(messages: list[dict], model: str, schema: dict | None):
            queued = perf_counter()
            if concurrency is not None and not concurrency.acquire(timeout=queue_timeout):
                if diagnostics is not None:
                    diagnostics({"stage": "queue", "error_type": "TimeoutError",
                                 "response_format": output_format,
                                 "request_timeout_seconds": request_timeout,
                                 "queue_timeout_seconds": queue_timeout})
                raise TimeoutError(f"Nightshift request queue wait exceeded {queue_timeout} seconds")
            started = perf_counter()
            receipt = {"response_format": output_format,
                       "configured_max_tokens": max_tokens,
                       "requested_reasoning_effort": reasoning_effort,
                       "request_timeout_seconds": request_timeout,
                       "queue_timeout_seconds": queue_timeout,
                       "queue_ms": int((started - queued) * 1000)}
            try:
                options = {"max_tokens": max_tokens} if max_tokens is not None else {}
                if reasoning_effort is not None:
                    options["reasoning_effort"] = reasoning_effort
                if schema is not None and output_format != "prompt":
                    response_format = {"type": "json_object"}
                    if output_format == "webllm_schema":
                        response_format["schema"] = json.dumps(schema, ensure_ascii=False)
                    options["response_format"] = response_format
                    if json_temperature is not None:
                        options["temperature"] = json_temperature
                response = client.chat.completions.create(
                    model=model, messages=_schema_messages(messages, schema), **options,
                )
                text = response.choices[0].message.content
                usage = response.usage
                message = response.choices[0].message
                details = getattr(usage, "completion_tokens_details", None)
                reason = getattr(response.choices[0], "finish_reason", None)
                receipt.update({"finish_reason": reason if reason in
                                {"stop", "length", "tool_calls", "abort", "content_filter"}
                                else "unknown", "stage": "response",
                                "content_chars": len(text) if isinstance(text, str) else 0,
                                "has_reasoning_content": bool(getattr(message, "reasoning_content", None)
                                                              or getattr(message, "reasoning", None)),
                                "prompt_tokens": _usage_count(usage, "prompt_tokens"),
                                "completion_tokens": _usage_count(usage, "completion_tokens"),
                                "reasoning_tokens": _usage_count(details, "reasoning_tokens"),
                                "response_sha256": hashlib.sha256((text or "").encode()).hexdigest()})
                return (text, usage.prompt_tokens if usage else None,
                        usage.completion_tokens if usage else None)
            except Exception as error:
                receipt.update(stage="request", error_type=type(error).__name__)
                status = getattr(error, "status_code", None)
                if isinstance(status, int) and 100 <= status <= 599:
                    receipt["http_status"] = status
                    receipt["error_signals"] = error_signals(error)
                raise
            finally:
                if concurrency is not None:
                    concurrency.release()
                if diagnostics is not None:
                    receipt["request_ms"] = int((perf_counter() - started) * 1000)
                    diagnostics(receipt)

        return call

    routes: dict[str, list] = {}
    provider = os.environ.get("LLM_PROVIDER", "auto")
    if provider not in {"auto", "glm"}:
        raise ValueError("LLM_PROVIDER must be auto or glm")
    if provider == "glm":
        api_key = read_glm_api_key()
        base = os.environ.get("GLM_BASE_URL")
        model = os.environ.get("GLM_MODEL")
        if not base or not model:
            raise ValueError("Configure GLM_BASE_URL and GLM_MODEL explicitly")
        effort = os.environ.get("GLM_REASONING_EFFORT",
                                "low" if model.lower().startswith("glm-5.3") else "provider_default")
        if effort not in {"provider_default", "low", "high", "max"}:
            raise ValueError("GLM_REASONING_EFFORT must be provider_default, low, high or max")
        output_format = os.environ.get("GLM_RESPONSE_FORMAT", "prompt")
        if output_format not in {"prompt", "json_object"}:
            raise ValueError("GLM_RESPONSE_FORMAT must be prompt or json_object")
        timeout = _bounded_setting("GLM_TIMEOUT_SECONDS", 180, 600)
        queue_timeout = _bounded_setting("GLM_QUEUE_TIMEOUT_SECONDS", 600, 1800)
        client = OpenAI(
            base_url=normalise_hosted_base_url(base), api_key=api_key,
            timeout=float(timeout), max_retries=0,
            default_headers={"User-Agent": "tradepulse/1.0",
                             "x-opencode-session": str(uuid4())},
        )
        concurrency = threading.BoundedSemaphore(_bounded_setting("GLM_MAX_CONCURRENCY", 1, 4))
        route = ("glm", model, caller(client, concurrency=concurrency,
                 max_tokens=_bounded_setting("GLM_MAX_TOKENS", 4096, 8192),
                 request_timeout=timeout, queue_timeout=queue_timeout,
                 reasoning_effort=None if effort == "provider_default" else effort,
                 output_format=output_format, json_temperature=None))
        # An explicit hosted profile bypasses local inference, including token-file reads.
        return {role: [route] for role in ROLES}
    token_file = os.environ.get("METERLESS_TOKEN_FILE")
    if token_file:
        output_format = os.environ.get("METERLESS_RESPONSE_FORMAT", "prompt")
        if output_format not in {"prompt", "json_object", "webllm_schema"}:
            raise ValueError("METERLESS_RESPONSE_FORMAT must be prompt, json_object or webllm_schema")
        request_timeout = _bounded_setting("METERLESS_TIMEOUT_SECONDS", 180, 600)
        queue_timeout = _bounded_setting("METERLESS_QUEUE_TIMEOUT_SECONDS", 180, 1800)
        meterless = OpenAI(
            base_url=normalise_meterless_base_url(
                os.environ.get("METERLESS_BASE_URL") or "http://127.0.0.1:8088/v1"
            ),
            api_key=read_token(token_file), timeout=float(request_timeout), max_retries=0,
            default_headers={"meterless-app": os.environ.get("METERLESS_APP") or "tradepulse",
                             "meterless-scope": "user"},
        )
        concurrency = threading.BoundedSemaphore(
            _bounded_setting("METERLESS_MAX_CONCURRENCY", 1, 4)
        )
        route = ("meterless", os.environ.get("METERLESS_MODEL") or "meterless/auto",
                 caller(meterless, concurrency=concurrency,
                        max_tokens=_bounded_setting("METERLESS_MAX_TOKENS", 768, 4096),
                        output_format=output_format, request_timeout=request_timeout,
                        queue_timeout=queue_timeout))
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
