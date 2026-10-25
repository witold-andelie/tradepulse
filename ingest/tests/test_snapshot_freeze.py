"""SYNTHETIC snapshots cannot silently invalidate published provenance or model recordings."""

import hashlib
import json

import pytest

from ingest import lake, sample
from ingest.tests.test_pipeline_regressions import synthetic_tables
from tradepulse.contracts import table_names, table_path


@pytest.mark.parametrize("changed", [False, True])
def test_published_snapshot_requires_matching_staged_hashes(tmp_path, changed):
    source, destination = tmp_path / "source", tmp_path / "sample"
    synthetic_tables(source)
    sample.cut_sample(source, destination, ("SYNTHETIC",))
    hashes = {
        name: hashlib.sha256(table_path(name, destination).read_bytes()).hexdigest()
        for name in table_names()
    }
    manifest = {"tables": {name: {"sha256": value} for name, value in hashes.items()}}
    (destination / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    if changed:
        data = lake.read_table("macro_point", source)
        data["value"] += 1
        lake.write_table(data, "macro_point", source)
        with pytest.raises(ValueError, match="published snapshot"):
            sample.cut_sample(source, destination, ("SYNTHETIC",))
    else:
        sample.cut_sample(source, destination, ("SYNTHETIC",))
    assert hashes == {
        name: hashlib.sha256(table_path(name, destination).read_bytes()).hexdigest()
        for name in table_names()
    }
