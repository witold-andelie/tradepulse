"""Offline container/policy tests using SYNTHETIC table rows and an injected audit."""

import datetime as dt
import hashlib
import json
from zipfile import ZipFile

import pandas as pd
import pytest

from ingest import handoff
from ingest.common import frame
from tradepulse.contracts import load_table_spec, table_names, table_path

DAY = dt.date(2026, 10, 23)


@pytest.fixture
def synthetic_lake(tmp_path, monkeypatch):
    tables, reference = [], {}
    for name in table_names():
        row = {}
        for column in load_table_spec(name)["columns"]:
            row[column["name"]] = column["enum"][0] if column.get("enum") else {
                "date": DAY,
                "datetime": dt.datetime.combine(DAY, dt.time(), tzinfo=dt.UTC),
                "string": "SYNTHETIC",
                "float": 1.0,
                "int": 1,
            }[column["dtype"]]
        path = table_path(name, tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame([row], name).to_parquet(path, index=False)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        tables.append({"table": name, "rows": 1, "sha256": digest})
        reference[name] = {"sha256": digest}
    reports = tmp_path / "data/lake/_reports"
    reports.mkdir()
    for name in handoff.PROVENANCE:
        (reports / name).write_text("SYNTHETIC", encoding="utf-8")
    (reports / "handoff_manifest.json").write_text(json.dumps({"tables": tables}), encoding="utf-8")
    sample = tmp_path / "data/sample"
    sample.mkdir()
    (sample / "manifest.json").write_text(json.dumps({"as_of": DAY.isoformat(), "tables": reference}), encoding="utf-8")
    checks = pd.DataFrame([{"check": "texts.earnings_complete", "passed": False}])
    monkeypatch.setattr(handoff, "audit", lambda *args: checks)
    return tmp_path, checks


def test_requires_explicit_source_exception_opt_in(synthetic_lake):
    root, _ = synthetic_lake
    output = root / "private.zip"
    with pytest.raises(ValueError, match="opted in"):
        handoff.package_lake(DAY, output, root)
    assert not output.exists()


def test_verified_package_retains_strict_failure_and_never_claims_upload(synthetic_lake):
    root, _ = synthetic_lake
    result = handoff.package_lake(DAY, root / "private.zip", root, allow_source_exceptions=True)
    assert result["verified"] is True
    assert result["strict_acceptance_passed"] is False
    assert result["source_exception_release"] is True
    assert result["uploaded"] is False
    assert result["tables"] == len(table_names())
    assert result == handoff.verify_package(root / "private.zip")


def test_rejects_unresolved_failures_even_with_source_exception_opt_in(synthetic_lake):
    root, checks = synthetic_lake
    checks.loc[len(checks)] = {"check": "prices.references", "passed": False}
    with pytest.raises(ValueError, match="Lake audit failed"):
        handoff.package_lake(DAY, root / "private.zip", root, allow_source_exceptions=True)


def test_refuses_to_overwrite_existing_private_file(synthetic_lake):
    root, _ = synthetic_lake
    output = root / "private.zip"
    output.write_bytes(b"SYNTHETIC existing handoff")
    with pytest.raises(FileExistsError):
        handoff.package_lake(DAY, output, root, allow_source_exceptions=True)
    assert output.read_bytes() == b"SYNTHETIC existing handoff"


def test_refuses_to_put_full_private_lake_in_public_sample(synthetic_lake):
    root, _ = synthetic_lake
    output = root / "data/sample/private.zip"
    with pytest.raises(ValueError, match="outside the public sample"):
        handoff.package_lake(DAY, output, root, allow_source_exceptions=True)
    assert not output.exists()


@pytest.mark.parametrize("change", ["payload", "unexpected", "strict_flag"])
def test_verifier_rejects_tampering(synthetic_lake, change):
    root, _ = synthetic_lake
    output = root / "private.zip"
    handoff.package_lake(DAY, output, root, allow_source_exceptions=True)
    with ZipFile(output) as source:
        members = {name: source.read(name) for name in source.namelist()}
    if change == "payload":
        members["data/lake/price_bar.parquet"] += b"tampered"
    elif change == "unexpected":
        members["../unexpected"] = b"SYNTHETIC"
    else:
        manifest = json.loads(members["manifest.json"])
        manifest["strict_acceptance_passed"] = True
        members["manifest.json"] = json.dumps(manifest).encode()
    tampered = root / "tampered.zip"
    with ZipFile(tampered, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    with pytest.raises(ValueError):
        handoff.verify_package(tampered)
