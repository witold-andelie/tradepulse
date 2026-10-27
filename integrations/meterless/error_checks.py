"""Bounded HTTP error hints using fixed vocabulary, never arbitrary response values."""

from __future__ import annotations

import re

_PARAMETERS = frozenset({"response_format", "schema", "json_schema", "temperature", "model",
                         "messages", "max_tokens", "top_p", "stream", "seed", "stop"})
_CODES = frozenset({"invalid_request_error", "unsupported_parameter", "invalid_value",
                   "extra_forbidden", "missing", "string_type", "dict_type", "literal_error",
                   "model_not_found", "context_length_exceeded", "validation_error"})
_SIGNALS = {"unsupported": r"unsupported|not supported|does not support|unrecognized|unknown parameter",
            "extra_field": r"extra input|extra field|unexpected.{0,40}(?:field|keyword|argument)|not permitted",
            "invalid_type": r"wrong type|invalid type|expected.{0,40}(?:string|object|number)",
            "context_limit": r"context.{0,30}(?:length|limit|exceed)",
            "schema": r"\bschema\b", "json_object": r"\bjson_object\b",
            "response_format": r"\bresponse_format\b", "temperature": r"\btemperature\b"}


def error_signals(error: Exception) -> dict:
    """Inspect SDK-parsed error bodies without logging messages, headers or input echoes.

    Hints are observations, not conclusions about why a provider rejected a request.
    Unknown values are omitted. Work is capped even for nested or oversized error bodies.
    """
    body = getattr(error, "body", None)
    codes, parameters, signals = set(), set(), set()
    pending = [(body, 0)]
    for _ in range(64):
        if not pending:
            break
        node, depth = pending.pop()
        if depth > 4:
            continue
        if isinstance(node, str):
            for label, pattern in _SIGNALS.items():
                if re.search(pattern, node[:2048], re.IGNORECASE):
                    signals.add(label)
        elif isinstance(node, list):
            pending.extend((child, depth + 1) for child in node[:16])
        elif isinstance(node, dict):
            for key in ("code", "type"):
                value = node.get(key)
                if isinstance(value, str) and value in _CODES:
                    codes.add(value)
            location = node.get("param") or node.get("loc")
            parts = location[:16] if isinstance(location, list) else (
                location[:256].split(".") if isinstance(location, str) else [])
            parameters.update(part for part in parts if isinstance(part, str) and part in _PARAMETERS)
            pending.extend((node[key], depth + 1) for key in
                           ("error", "detail", "message", "msg") if key in node)
    return {"body_available": isinstance(body, (dict, list, str)),
            "codes": sorted(codes), "parameters": sorted(parameters),
            "message_signals": sorted(signals)}
