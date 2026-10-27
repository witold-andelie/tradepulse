"""SYNTHETIC transport/profile tests; never evidence of a live GLM result."""

import json
import sys
from types import SimpleNamespace

import pytest

from integrations.environment import load_private_env
from integrations.meterless.llm import build_routes_from_env, normalise_hosted_base_url
from integrations.live_acceptance import validate_case
from tradepulse.contracts import REPO_ROOT


def test_hosted_endpoint_keeps_provider_path_without_duplicate_completion_suffix():
    endpoint = "https://opencode.ai/inference/go/openai/v1/chat/completions"
    assert normalise_hosted_base_url(endpoint) == "https://opencode.ai/inference/go/openai/v1"
    with pytest.raises(ValueError):
        normalise_hosted_base_url("https://user:private@provider.invalid/v1")


def test_glm_profile_never_initializes_local_runtime_or_cloud_fallback(monkeypatch):
    captured, calls = [], []
    monkeypatch.setenv("LLM_PROVIDER", "glm")
    monkeypatch.setenv("GLM_API_KEY", "synthetic-private-value")
    monkeypatch.setenv("GLM_BASE_URL", "https://provider.invalid/v1/chat/completions")
    monkeypatch.setenv("GLM_MODEL", "glm-5.3-flash")
    monkeypatch.setenv("METERLESS_TOKEN_FILE", "missing-local-token-must-not-be-read")
    monkeypatch.setenv("NVIDIA_API_KEY", "must-not-be-used")

    def complete(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop",
            message=SimpleNamespace(content='{"summary":"SYNTHETIC"}'))], usage=None)

    def client(**kwargs):
        captured.append(kwargs)
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=complete)))

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=client))
    diagnostics = []
    routes = build_routes_from_env(diagnostics=diagnostics.append)
    assert set(routes) == {"extractor", "guard", "analyst", "skeptic"}
    assert all(len(route) == 1 and route[0][:2] == ("glm", "glm-5.3-flash")
               for route in routes.values())
    routes["analyst"][0][2]([], "glm-5.3-flash", {"type": "object"})
    assert len(captured) == 1
    assert captured[0]["base_url"] == "https://provider.invalid/v1"
    assert captured[0]["max_retries"] == 0
    assert captured[0]["default_headers"]["User-Agent"].startswith("tradepulse/")
    assert captured[0]["default_headers"]["x-opencode-session"]
    assert "response_format" not in calls[0]
    assert "synthetic-private-value" not in json.dumps(diagnostics)


def test_private_loader_accepts_glm_configuration_without_executing_it(monkeypatch, tmp_path):
    for key in ("GLM_API_KEY", "GLM_MODEL", "LLM_PROVIDER"):
        # Track an absent baseline so direct env-loader writes are undone after this test.
        monkeypatch.setenv(key, "")
        monkeypatch.delenv(key, raising=False)
    path = tmp_path / ".env.glm.local"
    path.write_text('LLM_PROVIDER=glm\nGLM_MODEL=glm-5.3-flash\n'
                    'GLM_API_KEY="synthetic-private-value"\n', encoding="utf-8")
    load_private_env(path)
    import os

    assert os.environ["GLM_MODEL"] == "glm-5.3-flash"
    assert os.environ["LLM_PROVIDER"] == "glm"


def test_missing_glm_settings_fail_instead_of_falling_back(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "glm")
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY_FILE", raising=False)
    monkeypatch.delenv("GLM_OPENCODE_AUTH_FILE", raising=False)
    with pytest.raises(ValueError, match="GLM_API_KEY"):
        build_routes_from_env()


def synthetic_case_and_events():
    # Mode changes are SYNTHETIC test setup, never exported as live sponsor evidence.
    output = json.loads((REPO_ROOT / "examples/crypto/output.json").read_text(encoding="utf-8"))
    output.update(sample_mode=False, data_mode="REAL")
    for item in output["explanations"]:
        item["models"] = {"analyst": "glm-5.3-flash", "skeptic": "glm-5.3-flash"}
    events = []
    for role in ("analyst", "skeptic"):
        events.append({"ts": output["created_at"], "run_id": output["run_id"], "seq": len(events),
            "node": "SYNTHETIC", "kind": "llm_call", "status": "ok", "duration_ms": None,
            "model": "glm-5.3-flash", "tokens_in": 1, "tokens_out": 1, "data_mode": "REAL",
            "message": f"{role} answered", "payload": {"provider": "glm", "replayed": False}})
    for operation in ("snapshot", "recall", "remember"):
        events.append({**events[0], "seq": len(events), "node": "meterless", "kind": "tool_call",
                       "message": "SYNTHETIC", "payload": {"operation": operation}})
    return output, events


def test_glm_acceptance_is_distinct_from_original_nightshift_acceptance():
    output, events = synthetic_case_and_events()
    checked = validate_case(output, events, expected_provider="glm")
    assert checked["llm_provider"] == "glm"
    assert checked["llm_calls"] == 2
    assert checked["nightshift_calls"] == 0
    with pytest.raises(ValueError, match="selected provider"):
        validate_case(output, events)  # Original profile cannot silently accept hosted GLM.


@pytest.mark.parametrize("fault", ["replayed", "engine_error", "missing_remember", "wrong_provider"])
def test_hosted_profile_keeps_actual_provider_and_engine_requirements(fault):
    output, events = synthetic_case_and_events()
    if fault == "replayed":
        events[0]["payload"]["replayed"] = True
    elif fault == "engine_error":
        events[-1]["status"] = "error"
    elif fault == "missing_remember":
        events.pop()
    else:
        events[0]["payload"]["provider"] = "meterless"
    with pytest.raises(ValueError):
        validate_case(output, events, expected_provider="glm")


def test_real_sdk_uses_supplied_route_and_exact_model_without_new_library(monkeypatch):
    import httpx
    import openai

    monkeypatch.setenv("LLM_PROVIDER", "glm")
    monkeypatch.setenv("GLM_API_KEY", "synthetic-private-value")
    monkeypatch.setenv("GLM_BASE_URL", "https://provider.invalid/inference/go/openai/v1/chat/completions")
    monkeypatch.setenv("GLM_MODEL", "glm-5.3-flash")
    captured = []

    def handler(request):
        captured.append((request.url.path, json.loads(request.content)))
        return httpx.Response(200, json={"id": "synthetic", "created": 0,
            "object": "chat.completion", "model": "glm-5.3-flash", "choices": [{"index": 0,
            "finish_reason": "stop", "message": {"role": "assistant", "content": "{}"}}]})

    original_client = openai.OpenAI
    with httpx.Client(transport=httpx.MockTransport(handler)) as transport_client:
        monkeypatch.setattr(openai, "OpenAI", lambda **kwargs:
                            original_client(http_client=transport_client, **kwargs))
        route = build_routes_from_env()["analyst"][0]
        route[2]([], route[1], {"type": "object"})
    assert captured == [("/inference/go/openai/v1/chat/completions", {
        "messages": [{"role": "system", "content": 'RESPONSE SCHEMA:\n{"type": "object"}'
         '\nReturn only one JSON object matching this schema. Keep text concise.'}],
        "model": "glm-5.3-flash", "max_tokens": 4096, "reasoning_effort": "low"})]


def test_launcher_passes_private_configuration_to_existing_cli_without_model_call(monkeypatch, tmp_path):
    from integrations.launch import main

    for key in ("LLM_PROVIDER", "GLM_MODEL"):
        monkeypatch.setenv(key, "")
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SAMPLE_MODE", "true")
    monkeypatch.setenv("ENGINES_ENABLED", "false")
    path = tmp_path / ".env.glm.local"
    path.write_text("LLM_PROVIDER=glm\nGLM_MODEL=glm-5.3-flash\n", encoding="utf-8")
    forwarded = []
    monkeypatch.setitem(sys.modules, "run", SimpleNamespace(main=lambda args: forwarded.append(args) or 0))
    assert main(["--env-file", str(path), "--serve"]) == 0
    assert forwarded == [["--serve"]]
    import os

    assert os.environ["SAMPLE_MODE"] == "false"
    assert os.environ["ENGINES_ENABLED"] == "true"


def test_existing_opencode_go_key_can_be_referenced_without_copying_it(monkeypatch, tmp_path):
    from integrations.meterless.llm import read_glm_api_key

    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY_FILE", raising=False)
    source = tmp_path / "auth.json"
    raw = json.dumps({"opencode-go": {"type": "api", "key": "synthetic-private-value"},
                      "other": {"type": "api", "key": "must-not-be-selected"}})
    source.write_text(raw, encoding="utf-8")
    monkeypatch.setenv("GLM_OPENCODE_AUTH_FILE", str(source))
    assert read_glm_api_key() == "synthetic-private-value"
    assert source.read_text(encoding="utf-8") == raw
    source.write_text('{"other": {"type":"api","key":"must-not-be-selected"}}', encoding="utf-8")
    with pytest.raises(ValueError, match="opencode-go"):
        read_glm_api_key()
