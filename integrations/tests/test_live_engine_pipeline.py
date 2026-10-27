"""Actual HTTP engines with the existing core pipeline; no live-model success is claimed here."""

import json
import os

import pytest
import requests

from integrations.meterless.engines_client import EnginesClient
from integrations.meterless.llm import Cassette, ChainClient
from integrations.zetaris.adapter import DuckDBAdapter
from serve import verified_sample_request
from tradepulse.contracts import REPO_ROOT, assert_payload
from tradepulse.pipeline import run_pipeline


@pytest.mark.network
def test_real_sidecar_handles_frozen_sample_pipeline(tmp_path, monkeypatch):
    url = os.environ.get("ENGINES_ACCEPTANCE_URL")
    if not url:
        pytest.skip("Set ENGINES_ACCEPTANCE_URL to a dedicated local test sidecar")
    monkeypatch.setenv("SAMPLE_MODE", "true")
    monkeypatch.setenv("RECORD_LLM", "false")
    root = REPO_ROOT / "data" / "sample"
    engines = EnginesClient(url)
    assert engines.health()["engines"]["hmem"].startswith("meterless-reference@")
    # A missing cassette produces honest model abstention. The subject of this test is the
    # actual persisted engine use, not Nightshift inference or Zetaris acceptance.
    llm = ChainClient({}, Cassette(tmp_path / "empty.jsonl"), mode="replay")
    base = verified_sample_request()
    for pool in base["pools"]:
        request = {**base, "pools": [pool], "top_k": 1}
        output = run_pipeline(request, query=DuckDBAdapter(root), llm=llm,
                              engines=engines, log_dir=tmp_path / "traces")
        assert_payload(output, "RunOutput")
        assert not any("engines were not used" in warning for warning in output["warnings"])
        events = [json.loads(line) for line in
                  (REPO_ROOT / output["trace_path"]).read_text(encoding="utf-8").splitlines()]
        operations = {event["payload"].get("operation") for event in events
                      if event["node"] == "meterless"}
        assert {"snapshot", "recall", "remember"} <= operations
        row = output["recommendations"][0]
        remembered = engines.recall(row["symbol"], output["as_of"], k=100)
        assert any(record["provenance"]["run_id"] == output["run_id"]
                   for record in remembered)
    headers = {}
    if os.environ.get("ENGINES_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['ENGINES_TOKEN']}"
    activity = requests.get(f"{url}/activity", headers=headers, timeout=30)
    assert activity.status_code == 200
    assert activity.json()["hmem_records"] >= sum(
        len(DuckDBAdapter(root).run("universe_pool", {"pool": pool}).df)
        for pool in base["pools"]
    )
