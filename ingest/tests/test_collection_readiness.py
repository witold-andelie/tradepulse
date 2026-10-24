"""SYNTHETIC offline checks before collecting and publishing a real snapshot."""

import pandas as pd
import pytest

from ingest import __main__ as cli
from ingest import crypto, lake, sample
from ingest.tests.test_pipeline_regressions import AS_OF, synthetic_tables
from tradepulse import contracts


@pytest.mark.parametrize("missing", [None, float("nan"), pd.NA, "", "   ", "[]"])
def test_absent_yahoo_candidates_allow_refinement(missing):
    assert crypto._candidate_quotes(missing) == []


def test_yahoo_candidate_list_is_preserved_and_wrong_shape_rejected():
    options = '[{"symbol":"SYNTHETIC-USD","name":"SYNTHETIC USD"}]'
    assert crypto._candidate_quotes(options) == [
        {"symbol": "SYNTHETIC-USD", "name": "SYNTHETIC USD"}
    ]
    with pytest.raises(TypeError, match="JSON list"):
        crypto._candidate_quotes('{"symbol":"SYNTHETIC-USD"}')


@pytest.mark.parametrize("future", [False, True])
def test_sample_cli_validates_requested_decision_date_before_publication(
    tmp_path, monkeypatch, future
):
    synthetic_tables(tmp_path)
    if future:
        data = lake.read_table("macro_point", tmp_path)
        data["date"] = pd.Timestamp("2030-01-01")
        lake.write_table(data, "macro_point", tmp_path)
    destination = tmp_path / "offline"
    original = sample.cut_sample
    monkeypatch.setattr(contracts, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        sample,
        "cut_sample",
        lambda: original(tmp_path, destination, ("SYNTHETIC",)),
    )

    result = cli.main(["sample", "--as-of", AS_OF.isoformat()])

    assert result == (1 if future else 0)
    assert contracts.table_path("macro_point", destination).exists() is not future
