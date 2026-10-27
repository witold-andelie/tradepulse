import sys
from types import SimpleNamespace

import pytest

from integrations.meterless.llm import build_routes_from_env, normalise_meterless_base_url


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
