"""SYNTHETIC transport failures; no real engine writes occur here."""

import json

import pytest
import requests

from integrations.meterless.engines_client import EnginesClient, EnginesError


def test_large_write_is_explicitly_batched_with_separate_timeout(monkeypatch):
    monkeypatch.setenv("ENGINES_WRITE_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("ENGINES_REMEMBER_BATCH_SIZE", "50")
    calls, diagnostics = [], []

    class Session:
        def post(self, _url, *, json, timeout):
            calls.append((len(json["records"]), timeout))
            return type("Response", (), {"status_code": 200,
                "json": lambda _: {"added": len(json["records"])}})()

    client = EnginesClient("http://localhost:8790", timeout_s=10, session=Session())
    client.observer = diagnostics.append
    assert client.remember([{"id": str(index)} for index in range(123)]) == {"added": 123}
    assert calls == [(50, 60), (50, 60), (23, 60)]
    assert client.timeout_s == 10
    assert len(diagnostics) == 3


def test_unknown_write_outcome_is_not_automatically_retried(monkeypatch):
    monkeypatch.setenv("ENGINES_WRITE_TIMEOUT_SECONDS", "60")
    calls, diagnostics = [], []

    class Session:
        def post(self, *_args, **_kwargs):
            calls.append(1)
            raise requests.ReadTimeout("synthetic-private-value")

    client = EnginesClient("http://localhost:8790", session=Session())
    client.observer = diagnostics.append
    with pytest.raises(EnginesError) as caught:
        client.remember([{"id": "synthetic"}])
    assert len(calls) == 1
    assert caught.value.error_type == "ReadTimeout"
    assert diagnostics[0]["error_type"] == "ReadTimeout"
    assert "synthetic-private-value" not in json.dumps(diagnostics)


def test_invalid_batch_acknowledgement_does_not_look_successful(monkeypatch):
    monkeypatch.setenv("ENGINES_REMEMBER_BATCH_SIZE", "1")

    class Session:
        def post(self, *_args, **_kwargs):
            return type("Response", (), {"status_code": 200, "json": lambda _: {"added": 2}})()

    with pytest.raises(EnginesError):
        EnginesClient("http://localhost:8790", session=Session()).remember([{"id": "synthetic"}])
