import sys
from types import SimpleNamespace

import pytest

from integrations.meterless.llm import (build_routes_from_env, normalise_meterless_base_url,
                                        require_advertised_model)


@pytest.mark.parametrize(("raw", "expected"), [
    ("127.0.0.1:8088", "http://127.0.0.1:8088/v1"),
    ("http://127.0.0.1:8088/v1/models", "http://127.0.0.1:8088/v1"),
    ("http://127.0.0.1:8088/v1/chat/completions", "http://127.0.0.1:8088/v1"),
    ("http://127.0.0.1:8088/healthz", "http://127.0.0.1:8088/v1"),
])
def test_normalise_meterless_base_url(raw, expected):
    assert normalise_meterless_base_url(raw) == expected


def test_normalise_meterless_base_url_rejects_credentials():
    with pytest.raises(ValueError):
        normalise_meterless_base_url("http://user:secret@127.0.0.1:8088")


def test_nightshift_remains_first_for_all_roles_with_nim_configured(monkeypatch, tmp_path):
    token_file = tmp_path / "proxy-token"
    token_file.write_text("test-runtime-token", encoding="utf-8")
    monkeypatch.setenv("METERLESS_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("NVIDIA_API_KEY", "test-nim-key")
    monkeypatch.setenv("NIM_ANALYST_MODEL", "test-analyst")
    monkeypatch.setenv("NIM_SKEPTIC_MODEL", "test-skeptic")
    clients = []

    def client(**kwargs):
        clients.append(kwargs)
        return SimpleNamespace()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=client))
    routes = build_routes_from_env()
    assert set(routes) == {"extractor", "guard", "analyst", "skeptic"}
    assert all(route[0][0] == "meterless" for route in routes.values())
    assert all(route[-1][0] == "nim" for route in routes.values())
    assert clients[0]["default_headers"]["meterless-app"] == "tradepulse"
    assert clients[0]["default_headers"]["meterless-scope"] == "user"
    assert clients[0]["timeout"] == 180
    assert clients[0]["max_retries"] == 0


@pytest.mark.parametrize("selected", ["meterless/auto", "webllm/Llama-3.2-1B-Instruct-q4f16_1-MLC"])
def test_model_validation_uses_the_actual_advertised_id(selected):
    assert require_advertised_model({"data": [{"id": selected}]}, selected) == [selected]


def test_unadvertised_or_empty_model_cannot_pass_discovery():
    with pytest.raises(ValueError, match="not in the runtime"):
        require_advertised_model({"data": [{"id": "webllm/test"}]}, "meterless/auto")
    with pytest.raises(ValueError):
        require_advertised_model({"data": []}, "meterless/auto")


def test_local_requests_are_serial_bounded_and_include_schema(monkeypatch, tmp_path):
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor
    from copy import deepcopy

    token_file = tmp_path / "proxy-token"
    token_file.write_text("synthetic-test-token", encoding="utf-8")
    monkeypatch.setenv("METERLESS_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("METERLESS_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("METERLESS_MAX_TOKENS", "512")
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    state = {"active": 0, "peak": 0}
    lock = threading.Lock()
    calls = []

    def complete(**kwargs):
        with lock:
            calls.append(kwargs)
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
        time.sleep(0.01)
        with lock:
            state["active"] -= 1
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{}'))],
                               usage=None)

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **kwargs:
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=complete)))))
    routes = build_routes_from_env()
    messages = [{"role": "system", "content": "SYNTHETIC test"}]
    original = deepcopy(messages)
    schema = {"type": "object", "required": ["summary"]}
    with ThreadPoolExecutor(max_workers=4) as workers:
        list(workers.map(lambda role: routes[role][0][2](messages, "webllm/test", schema),
                         ["extractor", "analyst", "skeptic", "guard"]))
    assert state["peak"] == 1
    assert len(calls) == 4
    assert all(call["max_tokens"] == 512 for call in calls)
    assert all('"required": ["summary"]' in call["messages"][0]["content"] for call in calls)
    assert messages == original
