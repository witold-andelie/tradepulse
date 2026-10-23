import copy
import datetime as dt
import json
import threading

import pytest
from fastapi.testclient import TestClient

from tradepulse.api import create_app
from tradepulse.contracts import CONTRACTS_DIR
from tradepulse.store import RunStore

FIXTURE = json.loads((CONTRACTS_DIR / "fixtures" / "run_output.fixture.json").read_text(encoding="utf-8"))
TODAY = dt.date(2026, 10, 22)
EARLIEST = dt.date(2024, 9, 1)


def _output(run_id="synthetic-run-0002", created="2026-10-22T09:00:00Z"):
    out = copy.deepcopy(FIXTURE)
    out["run_id"], out["created_at"] = run_id, created
    out["trace_path"] = f"logs/trace-{run_id}.jsonl"
    return out


def test_store_roundtrip_and_latest(tmp_path):
    store = RunStore(tmp_path)
    assert store.latest() is None and store.list_ids() == []
    store.save(_output("synthetic-run-0001", "2026-10-22T08:00:00Z"))
    path = store.save(_output("synthetic-run-0002", "2026-10-22T09:00:00Z"))
    assert path == tmp_path / "synthetic-run-0002" / "output.json"
    assert store.get("synthetic-run-0001")["run_id"] == "synthetic-run-0001"
    assert store.latest()["run_id"] == "synthetic-run-0002"
    assert store.list_ids() == ["synthetic-run-0001", "synthetic-run-0002"]


@pytest.mark.parametrize("bad", ["../etc", "UPPER-CASE-ID", "short", "a/b/c/d/e/f"])
def test_store_rejects_bad_ids(tmp_path, bad):
    store = RunStore(tmp_path)
    assert store.get(bad) is None
    with pytest.raises(ValueError):
        store.save(dict(_output(), run_id=bad))


def _client(tmp_path, runner):
    return TestClient(create_app(store=RunStore(tmp_path / "runs"), runner=runner, today=TODAY, earliest=EARLIEST))


def test_post_run_success_and_reads(tmp_path):
    seen = []
    client = _client(tmp_path, lambda req: seen.append(req) or _output())
    r = client.post("/run", json={"pools": ["us_equity"], "tickers": ["NVDA"]})
    assert r.status_code == 200 and r.json()["run_id"] == "synthetic-run-0002"
    assert seen[0]["tickers"] == ["NVDA"] and seen[0]["horizon_days"] == 5
    assert client.get("/runs/latest").json()["run_id"] == "synthetic-run-0002"
    assert client.get("/runs/synthetic-run-0002").status_code == 200
    assert client.get("/runs/unknown-run-9999").status_code == 404


def test_post_run_guard_rejection(tmp_path):
    client = _client(tmp_path, lambda req: _output())
    r = client.post("/run", json={"pools": ["moon"]})
    assert r.status_code == 422 and r.json()["error"] == "schema"


def test_post_run_contract_violation(tmp_path):
    client = _client(tmp_path, lambda req: {"run_id": "x"})
    r = client.post("/run", json={"pools": ["crypto"]})
    assert r.status_code == 500 and r.json()["error"] == "contract"
    assert isinstance(r.json()["detail"], list)


def test_post_run_failure_hides_message(tmp_path):
    def boom(req):
        raise RuntimeError("secret detail api_key=123")
    r = _client(tmp_path, boom).post("/run", json={"pools": ["crypto"]})
    assert r.status_code == 500 and r.json() == {"error": "run_failed", "detail": "RuntimeError"}


def test_busy_when_a_run_is_in_progress(tmp_path):
    started, release = threading.Event(), threading.Event()

    def slow(req):
        started.set()
        release.wait(5)
        return _output()
    client = _client(tmp_path, slow)
    results = {}
    th = threading.Thread(target=lambda: results.setdefault("first", client.post("/run", json={"pools": ["crypto"]})))
    th.start()
    assert started.wait(5)
    second = client.post("/run", json={"pools": ["crypto"]})
    release.set()
    th.join(5)
    assert second.status_code == 409 and second.json()["error"] == "busy"
    assert results["first"].status_code == 200


def test_trace_endpoint(tmp_path, monkeypatch):
    # trace_path in the output is resolved against tradepulse.api.REPO_ROOT
    monkeypatch.setattr("tradepulse.api.REPO_ROOT", tmp_path)
    client = _client(tmp_path, lambda req: _output())
    client.post("/run", json={"pools": ["crypto"]})
    assert client.get("/runs/synthetic-run-0002/trace").status_code == 404  # trace file missing
    assert client.get("/runs/unknown-run-9999/trace").status_code == 404    # run missing
    lines = (CONTRACTS_DIR / "fixtures" / "trace.fixture.jsonl").read_text(encoding="utf-8")
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "trace-synthetic-run-0002.jsonl").write_text(lines, encoding="utf-8")
    r = client.get("/runs/synthetic-run-0002/trace")
    assert r.status_code == 200 and len(r.json()) == len(lines.splitlines())


def test_health(tmp_path, monkeypatch):
    monkeypatch.setenv("SAMPLE_MODE", "false")
    assert _client(tmp_path, lambda req: _output()).get("/health").json() == {"status": "ok", "sample_mode": False}
