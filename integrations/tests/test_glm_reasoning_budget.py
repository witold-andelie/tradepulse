"""SYNTHETIC SDK responses reproduce reasoning-budget starvation without network calls."""

import json
import sys
from types import SimpleNamespace

import pytest

from integrations.meterless.llm import AllProvidersFailed, ChainClient, build_routes_from_env


def runtime(monkeypatch, create):
    monkeypatch.setenv("LLM_PROVIDER", "glm")
    monkeypatch.setenv("GLM_API_KEY", "synthetic-private-value")
    monkeypatch.setenv("GLM_BASE_URL", "https://provider.invalid/v1")
    monkeypatch.setenv("GLM_MODEL", "glm-5.3-flash")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_:
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))))


def test_forced_thinking_model_uses_low_effort_without_unsupported_disable(monkeypatch):
    captured = []

    def complete(**kwargs):
        captured.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop",
            message=SimpleNamespace(content="{}"))], usage=None)

    runtime(monkeypatch, complete)
    monkeypatch.delenv("GLM_REASONING_EFFORT", raising=False)
    route = build_routes_from_env()["analyst"][0]
    route[2]([], route[1], {"type": "object"})
    assert captured[0]["reasoning_effort"] == "low"
    assert "thinking" not in captured[0]


def test_glm_json_mode_is_explicit_and_does_not_force_temperature_zero(monkeypatch):
    captured = []

    def complete(**kwargs):
        captured.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop",
            message=SimpleNamespace(content="{}"))], usage=None)

    runtime(monkeypatch, complete)
    monkeypatch.setenv("GLM_RESPONSE_FORMAT", "json_object")
    route = build_routes_from_env()["analyst"][0]
    route[2]([], route[1], {"type": "object"})
    assert captured[0]["response_format"] == {"type": "json_object"}
    assert "temperature" not in captured[0]
    assert captured[0]["reasoning_effort"] == "low"


def test_empty_length_response_records_usage_without_exposing_reasoning(monkeypatch):
    diagnostics = []

    def complete(**_kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="length", message=
            SimpleNamespace(content="", reasoning_content="SYNTHETIC PRIVATE REASONING"))], usage=
            SimpleNamespace(prompt_tokens=500, completion_tokens=4096,
                            completion_tokens_details=SimpleNamespace(reasoning_tokens=4096)))

    runtime(monkeypatch, complete)
    routes = build_routes_from_env(diagnostics=diagnostics.append)
    with pytest.raises(AllProvidersFailed):
        ChainClient(routes, None).complete("analyst", [], {"type": "object"})
    receipt = diagnostics[0]
    assert receipt["content_chars"] == 0
    assert receipt["has_reasoning_content"] is True
    assert receipt["reasoning_tokens"] == receipt["completion_tokens"] == 4096
    assert receipt["finish_reason"] == "length"
    assert "SYNTHETIC PRIVATE REASONING" not in json.dumps(receipt)


def test_unsupported_reasoning_disable_is_rejected_before_request(monkeypatch):
    runtime(monkeypatch, lambda **_: pytest.fail("Must not generate"))
    monkeypatch.setenv("GLM_REASONING_EFFORT", "none")
    with pytest.raises(ValueError, match="GLM_REASONING_EFFORT"):
        build_routes_from_env()
