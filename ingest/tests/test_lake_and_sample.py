"""Checks on real produced data. Lake tests run with `-m lake`; the sample test always runs."""

from pathlib import Path

import pytest

from tradepulse.contracts import REPO_ROOT, table_names, table_path, validate_table

SAMPLE_ROOT = REPO_ROOT / "data" / "sample"


@pytest.mark.lake
@pytest.mark.parametrize("name", table_names())
def test_lake_table_is_valid(name):
    import pandas as pd

    path = table_path(name)
    if not path.exists():
        pytest.skip(f"{path} not built yet (run: py -3 -m ingest all)")
    df = pd.read_parquet(path)
    assert not df.empty
    assert validate_table(df, name) == []


def _sample_files() -> list[Path]:
    return [table_path(n, root=SAMPLE_ROOT) for n in table_names()]


def test_sample_snapshot_is_complete_and_valid():
    import pandas as pd

    files = _sample_files()
    if not any(p.exists() for p in files):
        pytest.skip("ACCEPTANCE: data/sample is not built yet; this test must pass (not skip) before A9 is done")
    total = 0
    for path, name in zip(files, table_names()):
        assert path.exists(), f"missing sample table {name}"
        df = pd.read_parquet(path)
        assert validate_table(df, name) == [], name
        total += path.stat().st_size
    assert total < 25 * 1024 * 1024, f"sample is {total / 1e6:.1f} MB (limit 25 MB)"
