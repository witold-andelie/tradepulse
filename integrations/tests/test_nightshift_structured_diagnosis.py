"""SYNTHETIC minimal reproductions of three lead-reported Nightshift failure shapes.

These strings are deliberately invalid/unverified, not recorded financial results.
"""

import json
import sys
from copy import deepcopy
from types import SimpleNamespace

import pytest

from integrations.meterless.llm import build_routes_from_env
from integrations.meterless.reply_checks import inspect_reply
from tradepulse.agents.prompts import ANALYST_SCHEMA
from tradepulse.contracts import REPO_ROOT


@pytest.mark.parametrize(("text", "valid", "keyword"), [
    ('{"claims": []', False, "json"),
    ('{"summary":"SYNTHETIC","claims":[{"text":"SYNTHETIC","evidence_ids":[]}],'
     '"what_to_watch":[]}', False, "required"),
    ('{"summary":"SYNTHETIC","claims":[],"what_to_watch":[]}, {"claims":[',
     False, "json"),
])
def test_partial_or_schema_invalid_reply_is_rejected_whole(text, valid, keyword):
    result = inspect_reply(text, ANALYST_SCHEMA)
    assert result["schema_valid"] is valid
    assert result["errors"][0]["keyword"] == keyword
    assert "SYNTHETIC" not in json.dumps(result)


def test_schema_success_does_not_hide_invented_evidence_ids():
    text = json.dumps({"summary": "SYNTHETIC", "claims": [
        {"text": "SYNTHETIC", "kind": "relation",
         "evidence_ids": ["ev-synthetic-price-symbol-window", "price-symbol-window"],
         "cause_evidence_id": "causes", "cause_accession": "accession"}],
        "what_to_watch": []})
    result = inspect_reply(text, ANALYST_SCHEMA, {"ev-synthetic-price-symbol-window"})
    assert result["schema_valid"] is True
    assert result["unknown_evidence_ids"] == 1
    assert result["causal_claims"] == 1
    assert "verified" not in result  # This checker cannot certify financial claims.


def fake_runtime(monkeypatch, tmp_path, complete):
    token = tmp_path / "token"
    token.write_text("synthetic-private-value", encoding="utf-8")
    monkeypatch.setenv("METERLESS_TOKEN_FILE", str(token))
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_kwargs:
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=complete)))))


def test_webllm_schema_is_opt_in_and_preserves_input(monkeypatch, tmp_path):
    calls, diagnostics = [], []

    def complete(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="length",
            message=SimpleNamespace(content='{"claims": ['))], usage=None)

    fake_runtime(monkeypatch, tmp_path, complete)
    monkeypatch.setenv("METERLESS_RESPONSE_FORMAT", "webllm_schema")
    messages = [{"role": "user", "content": "SYNTHETIC"}]
    original = deepcopy(messages)
    call = build_routes_from_env(diagnostics=diagnostics.append)["analyst"][0][2]
    text, _, _ = call(messages, "webllm/test", ANALYST_SCHEMA)
    assert text == '{"claims": ['  # Never repair the answer or replace IDs.
    assert calls[0]["response_format"] == {
        "type": "json_object", "schema": json.dumps(ANALYST_SCHEMA, ensure_ascii=False)}
    assert calls[0]["temperature"] == 0
    assert messages == original
    assert diagnostics[0]["finish_reason"] == "length"
    assert "synthetic-private-value" not in json.dumps(diagnostics)


def test_unsupported_format_fails_once_without_silent_retry(monkeypatch, tmp_path):
    calls, diagnostics = [], []

    class Unsupported(RuntimeError):
        status_code = 400

    def complete(**kwargs):
        calls.append(kwargs)
        raise Unsupported("synthetic-private-value")

    fake_runtime(monkeypatch, tmp_path, complete)
    monkeypatch.setenv("METERLESS_RESPONSE_FORMAT", "webllm_schema")
    call = build_routes_from_env(diagnostics=diagnostics.append)["analyst"][0][2]
    with pytest.raises(Unsupported):
        call([], "webllm/test", ANALYST_SCHEMA)
    assert len(calls) == 1
    assert diagnostics[0]["error_type"] == "Unsupported"
    assert diagnostics[0]["http_status"] == 400
    assert "synthetic-private-value" not in json.dumps(diagnostics)


def test_default_does_not_assume_nightshift_forwards_grammar(monkeypatch, tmp_path):
    calls = []

    def complete(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{}'))],
                               usage=None)

    fake_runtime(monkeypatch, tmp_path, complete)
    monkeypatch.delenv("METERLESS_RESPONSE_FORMAT", raising=False)
    build_routes_from_env()["analyst"][0][2]([], "webllm/test", ANALYST_SCHEMA)
    assert "response_format" not in calls[0]


def test_probe_rejects_offline_case_before_query_or_model(tmp_path):
    from integrations.meterless.structured_probe import select_item

    with pytest.raises(ValueError, match="REAL output"):
        select_item(REPO_ROOT / "examples/crypto/output.json", "AAVE-USD")


def test_probe_reconstructs_context_from_computed_output(tmp_path):
    from integrations.meterless.structured_probe import select_item

    # SYNTHETIC mode change tests selection only, never provides live acceptance evidence.
    output = json.loads((REPO_ROOT / "examples/crypto/output.json").read_text(encoding="utf-8"))
    output.update(data_mode="REAL", sample_mode=False)
    path = tmp_path / "case.json"
    path.write_text(json.dumps(output), encoding="utf-8")
    row = output["recommendations"][0]
    item = select_item(path, row["symbol"])
    assert item["as_of"] == output["as_of"]
    assert item["n"] == len(output["recommendations"])
    assert item["score"] == row["score"]


def test_probe_makes_one_request_even_when_reply_is_invalid(monkeypatch, tmp_path):
    from integrations.meterless import structured_probe as probe

    calls = []

    def complete(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop",
            message=SimpleNamespace(content='{"claims": []'))], usage=None)

    fake_runtime(monkeypatch, tmp_path, complete)
    monkeypatch.setattr(probe, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(probe, "select_item", lambda *_: {
        "symbol": "SYNTHETIC", "as_of": "2026-01-01"})
    monkeypatch.setattr(probe, "ZetarisClient", SimpleNamespace(from_env=lambda: object()))
    monkeypatch.setattr(probe, "ZetarisAdapter", lambda _: object())
    monkeypatch.setattr(probe, "gather_evidence", lambda *_: (
        {"ev-synthetic": {"query_template": "price_symbol_window"}}, {}, "SYNTHETIC"))
    monkeypatch.setattr(probe, "analyst_messages", lambda *_: [
        {"role": "user", "content": "SYNTHETIC"}])
    destination = tmp_path / "runs/probe"
    assert probe.main(["--case-output", "unused.json", "--symbol", "SYNTHETIC",
                       "--response-format", "webllm_schema", "--output", str(destination)]) == 1
    assert len(calls) == 1
    assert json.loads((destination / "report.json").read_text())["feature_acceptance"] is False
    assert json.loads((destination / "reply.json").read_text())["text"] == '{"claims": []'


def test_json_object_control_changes_only_nested_schema(monkeypatch, tmp_path):
    calls = []

    def complete(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{}'))],
                               usage=None)

    fake_runtime(monkeypatch, tmp_path, complete)
    for mode in ("webllm_schema", "json_object"):
        monkeypatch.setenv("METERLESS_RESPONSE_FORMAT", mode)
        build_routes_from_env()["analyst"][0][2]([], "webllm/test", ANALYST_SCHEMA)
    previous, control = deepcopy(calls)
    del previous["response_format"]["schema"]
    assert previous == control


@pytest.mark.parametrize(("body", "codes", "parameters", "signal"), [
    ({"error": {"message": "SYNTHETIC: response_format is not supported; private-test-value",
                "param": "response_format", "type": "invalid_request_error",
                "code": "private-test-value"}}, ["invalid_request_error"],
     ["response_format"], "unsupported"),
    ({"detail": [{"loc": ["body", "response_format", "schema"],
                  "msg": "SYNTHETIC: Extra inputs are not permitted",
                  "type": "extra_forbidden", "input": "private-test-value"}]},
     ["extra_forbidden"], ["response_format", "schema"], "extra_field"),
])
def test_http_error_summary_uses_fixed_vocabulary_only(body, codes, parameters, signal):
    from integrations.meterless.error_checks import error_signals

    error = RuntimeError("private-test-value")
    error.body = body
    result = error_signals(error)
    assert result["codes"] == codes
    assert result["parameters"] == parameters
    assert signal in result["message_signals"]
    assert "private-test-value" not in json.dumps(result)
    assert "SYNTHETIC" not in json.dumps(result)


def test_http_error_summary_handles_missing_or_unknown_body():
    from integrations.meterless.error_checks import error_signals

    assert error_signals(RuntimeError("private-test-value"))["body_available"] is False
    error = RuntimeError()
    error.body = {"private-test-value": "private-test-value", "message": "private-test-value"}
    result = error_signals(error)
    assert result["body_available"] is True
    assert result["codes"] == result["parameters"] == result["message_signals"] == []


def test_real_sdk_error_body_reaches_diagnostics_without_echoed_inputs(monkeypatch, tmp_path):
    import httpx
    import openai

    from integrations.meterless.llm import AllProvidersFailed, ChainClient

    token = tmp_path / "token"
    token.write_text("synthetic-private-value", encoding="utf-8")
    monkeypatch.setenv("METERLESS_TOKEN_FILE", str(token))
    monkeypatch.setenv("METERLESS_RESPONSE_FORMAT", "json_object")
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    captured, diagnostics = [], []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(400, json={"error": {"type": "invalid_request_error",
            "param": "response_format", "message": "SYNTHETIC: unsupported response_format",
            "input": "synthetic-private-value"}})

    original_client = openai.OpenAI
    with httpx.Client(transport=httpx.MockTransport(handler)) as transport_client:
        monkeypatch.setattr(openai, "OpenAI", lambda **kwargs:
                            original_client(http_client=transport_client, **kwargs))
        routes = build_routes_from_env(diagnostics=diagnostics.append)
        with pytest.raises(AllProvidersFailed):
            ChainClient(routes, None).complete("analyst", [], ANALYST_SCHEMA)
    assert len(captured) == 1
    assert captured[0]["response_format"] == {"type": "json_object"}
    assert diagnostics[0]["error_signals"]["parameters"] == ["response_format"]
    assert "unsupported" in diagnostics[0]["error_signals"]["message_signals"]
    assert "synthetic-private-value" not in json.dumps(diagnostics)
