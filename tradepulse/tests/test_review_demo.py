"""Review the authentic published artifact; tests do not create a live acceptance result."""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from scripts.review_demo import create_review_app, load_bundle
from tradepulse.contracts import REPO_ROOT


def test_review_api_returns_original_case_and_cannot_generate():
    output, events = load_bundle()
    with TestClient(create_review_app()) as client:
        response = client.get("/runs/latest")
        assert response.json() == output
        assert "generation-disabled" in response.headers["X-TradePulse-Review-Mode"]
        assert client.get(f"/runs/{output['run_id']}/trace").json() == events
        assert client.post("/run", json=output["request"]).status_code == 405
        assert client.get("/runs/unknown-run").status_code == 404


def test_tampering_with_original_artifact_is_rejected(tmp_path):
    source = REPO_ROOT / "docs/review/crypto-evidence.json"
    manifest = json.loads(source.read_text(encoding="utf-8"))
    (tmp_path / "docs/review").mkdir(parents=True)
    shutil.copyfile(source, tmp_path / "docs/review/crypto-evidence.json")
    for entry in manifest["files"].values():
        path = tmp_path / entry["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / entry["path"], path)
    output = tmp_path / manifest["files"]["output.json"]["path"]
    output.write_bytes(output.read_bytes() + b" ")
    with pytest.raises(ValueError, match="recorded byte hash"):
        load_bundle(tmp_path)
