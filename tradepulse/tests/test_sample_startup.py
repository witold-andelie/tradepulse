"""Offline startup policy tests with SYNTHETIC payloads and an injected runner."""

import datetime as dt
import hashlib
import json
from unittest.mock import Mock

import pytest

from serve import ensure_sample_run
from tradepulse.contracts import REPO_ROOT, table_names, table_path
from tradepulse.store import RunStore


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("SAMPLE_MODE", "true")
    monkeypatch.setenv("RECORD_LLM", "false")
    output = json.loads((REPO_ROOT / "contracts/fixtures/run_output.fixture.json").read_text(encoding="utf-8"))
    root = tmp_path / "sample"
    tables = {}
    for name in table_names():
        path = table_path(name, root)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = f"SYNTHETIC hash-only table: {name}".encode()
        path.write_bytes(payload)
        tables[name] = {"path": path.relative_to(root).as_posix(), "bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest()}
    (root / "manifest.json").write_text(
        json.dumps({"as_of": output["as_of"], "tables": tables}), encoding="utf-8")
    store, runner = RunStore(tmp_path / "runs"), Mock(return_value=output)
    return root, store, runner, output


def start(setup):
    root, store, runner, _ = setup
    return ensure_sample_run(store, runner=runner, sample_root=root, today=dt.date(2026, 10, 25))


def test_fresh_sample_is_verified_computed_and_saved_once(setup):
    root, store, runner, output = setup
    assert start(setup) == output
    assert runner.call_args.args[0]["as_of"] == output["as_of"]
    assert store.latest() == output
    assert start(setup) == output
    runner.assert_called_once()


def test_existing_run_does_not_require_recomputing_the_sample(setup):
    root, store, runner, output = setup
    store.save(output)
    (root / "manifest.json").unlink()
    assert start(setup) == output
    runner.assert_not_called()


def test_live_mode_never_falls_back_to_sample(setup, monkeypatch):
    monkeypatch.setenv("SAMPLE_MODE", "false")
    assert start(setup) is None
    setup[2].assert_not_called()


def test_automatic_startup_never_records_live_model_answers(setup, monkeypatch):
    monkeypatch.setenv("RECORD_LLM", "true")
    with pytest.raises(ValueError, match="Record models explicitly"):
        start(setup)
    setup[2].assert_not_called()


def test_tampered_table_blocks_startup_before_computing(setup):
    root, _, runner, _ = setup
    table_path("price_bar", root).write_bytes(b"SYNTHETIC altered table")
    with pytest.raises(ValueError, match="size|hash"):
        start(setup)
    runner.assert_not_called()


def test_future_snapshot_is_rejected_before_computing(setup):
    root, _, runner, _ = setup
    path = root / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["as_of"] = "2099-01-01"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="as_of"):
        start(setup)
    runner.assert_not_called()
