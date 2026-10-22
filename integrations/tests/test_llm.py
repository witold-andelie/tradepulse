import pytest

from integrations.meterless.llm import (AllProvidersFailed, Cassette, CassetteMiss, ChainClient, cassette_key,
                                        read_token, runtime_status)

MSG = [{"role": "user", "content": "Extract events from: Demand exceeds supply."}]


def test_read_token(tmp_path):
    good = tmp_path / "proxy-token"
    good.write_text("  abc123\n", encoding="utf-8")
    assert read_token(good) == "abc123"
    for content in ("", "rt-local"):
        bad = tmp_path / "bad"
        bad.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError):
            read_token(bad)
    with pytest.raises(ValueError):
        read_token(tmp_path / "missing")


def test_runtime_status():
    base = "http://127.0.0.1:8088/v1"
    assert runtime_status(lambda url: 200, base) == "online"
    assert runtime_status(lambda url: 401, base) == "unauthorized"
    assert runtime_status(lambda url: 403, base) == "unauthorized"
    assert runtime_status(lambda url: 500, base) == "offline"

    def boom(url):
        raise ConnectionError("refused")
    assert runtime_status(boom, base) == "offline"
    seen = []
    runtime_status(lambda url: seen.append(url) or 200, base)
    assert seen == [f"{base}/models"]


def test_cassette_key():
    k = cassette_key("extractor", MSG, None)
    assert k == cassette_key("extractor", [dict(m) for m in MSG], None)
    assert k != cassette_key("analyst", MSG, None)
    assert k != cassette_key("extractor", MSG, {"type": "object"})
    assert len(k) == 64


def test_cassette_roundtrip(tmp_path):
    path = tmp_path / "cassette.jsonl"
    c = Cassette(path)
    with pytest.raises(CassetteMiss):
        c.get("nope")
    c.put("k1", {"text": "a", "provider": "p", "model": "m", "tokens_in": 1, "tokens_out": 2})
    c.put("k1", {"text": "b", "provider": "p", "model": "m", "tokens_in": 1, "tokens_out": 2})
    assert Cassette(path).get("k1")["text"] == "b"  # reloaded from disk, newest wins


def _provider(name, fail=False, log=None):
    def call(messages, model, schema):
        (log if log is not None else []).append(name)
        if fail:
            raise TimeoutError(f"{name} timed out")
        return (f"answer from {name}", 10, 5)
    return (name, f"{name}-model", call)


def test_chain_falls_back_and_records(tmp_path):
    log = []
    routes = {"extractor": [_provider("meterless", fail=True, log=log), _provider("nim", log=log)]}
    cas = Cassette(tmp_path / "c.jsonl")
    rec = ChainClient(routes, cas, mode="record").complete("extractor", MSG)
    assert rec.provider == "nim" and rec.text == "answer from nim" and not rec.replayed
    assert log == ["meterless", "nim"]

    log.clear()
    rep = ChainClient(routes, Cassette(tmp_path / "c.jsonl"), mode="replay").complete("extractor", MSG)
    assert rep.text == rec.text and rep.replayed and rep.cassette_key == rec.cassette_key
    assert log == []  # replay never calls a provider


def test_replay_miss_and_failures(tmp_path):
    routes = {"analyst": [_provider("nim", fail=True)]}
    with pytest.raises(CassetteMiss):
        ChainClient(routes, Cassette(tmp_path / "c.jsonl"), mode="replay").complete("analyst", MSG)
    with pytest.raises(AllProvidersFailed):
        ChainClient(routes, None, mode="live").complete("analyst", MSG)
    with pytest.raises(ValueError):
        ChainClient(routes, None, mode="live").complete("trader", MSG)
