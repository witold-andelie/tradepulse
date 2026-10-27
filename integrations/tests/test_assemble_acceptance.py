"""SYNTHETIC file bundles test immutable evidence reuse; no live claims are produced."""

import json

import pytest

from integrations import assemble_acceptance as assemble
from integrations.live_acceptance import digest, selection_result
from integrations.tests.test_hosted_glm_acceptance import synthetic_case_and_events
from tradepulse.contracts import REPO_ROOT


def bundle(tmp_path, pool="crypto", *, fault=False):
    _, events = synthetic_case_and_events()
    output = json.loads((REPO_ROOT / f"examples/{pool}/output.json").read_text(encoding="utf-8"))
    output.update(sample_mode=False, data_mode="REAL")
    for item in output["explanations"]:
        item["models"] = {"analyst": "glm-5.3-flash", "skeptic": "glm-5.3-flash"}
    if fault:
        output["explanations"][0]["models"]["skeptic"] = "unavailable"
    for event in events:
        event.update(run_id=output["run_id"], ts=output["created_at"])
    source = tmp_path / "runs" / pool
    folder = source / pool
    folder.mkdir(parents=True)
    trace = f"trace-{output['run_id']}.jsonl"
    output["trace_path"] = (folder / trace).relative_to(tmp_path).as_posix()
    contents = {"input.json": json.dumps(output["request"]).encode(),
                "output.json": json.dumps(output).encode(),
                trace: ("\n".join(json.dumps(event) for event in events) + "\n").encode()}
    files = {}
    for name, raw in contents.items():
        (folder / name).write_bytes(raw)
        files[name] = {"bytes": len(raw), "sha256": digest(raw)}
    manifest = {"status": "failed", "as_of": output["as_of"],
                "acceptance_profile": "glm+zetaris+engines", "cases": [
                    {"pool": pool, "run_id": output["run_id"], "files": files}]}
    (source / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return source


def test_partial_success_is_reused_without_changing_original_source(monkeypatch, tmp_path):
    source = bundle(tmp_path)
    original = (source / "manifest.json").read_bytes()
    monkeypatch.setattr(assemble, "REPO_ROOT", tmp_path)
    cases, evidence, _ = assemble.collect_cases([source], "glm")
    assert len(cases) == 1 and cases[0]["pool"] == "crypto"
    assert evidence[0]["source_status"] == "failed"
    assert selection_result(cases, ["crypto"])["submission_complete"] is False
    assert (source / "manifest.json").read_bytes() == original


def test_all_three_sources_are_needed_for_complete_index(monkeypatch, tmp_path):
    sources = [bundle(tmp_path, pool) for pool in ("crypto", "eu_equity", "us_equity")]
    monkeypatch.setattr(assemble, "REPO_ROOT", tmp_path)
    cases, _, _ = assemble.collect_cases(sources[:2], "glm")
    assert selection_result(cases, [item["pool"] for item in cases])["submission_complete"] is False
    destination = tmp_path / "runs/index"
    args = [part for source in sources for part in ("--source", str(source))]
    assert assemble.main([*args, "--output", str(destination)]) == 0
    result = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    assert result["submission_complete"] is True
    assert result["new_network_calls"] == 0
    assert result["assembly_only"] is True


def test_changed_artifact_is_rejected_even_if_json_remains_valid(monkeypatch, tmp_path):
    source = bundle(tmp_path)
    path = source / "crypto/output.json"
    path.write_bytes(path.read_bytes() + b"\n")
    monkeypatch.setattr(assemble, "REPO_ROOT", tmp_path)
    with pytest.raises(ValueError, match="recorded hash"):
        assemble.collect_cases([source], "glm")


def test_unavailable_model_cannot_be_reclassified_as_accepted(monkeypatch, tmp_path):
    source = bundle(tmp_path, fault=True)
    monkeypatch.setattr(assemble, "REPO_ROOT", tmp_path)
    with pytest.raises(ValueError, match="unavailable"):
        assemble.collect_cases([source], "glm")


def test_duplicate_pool_is_not_three_distinct_inputs(monkeypatch, tmp_path):
    source = bundle(tmp_path)
    monkeypatch.setattr(assemble, "REPO_ROOT", tmp_path)
    with pytest.raises(ValueError, match="duplicate"):
        assemble.collect_cases([source, source], "glm")
