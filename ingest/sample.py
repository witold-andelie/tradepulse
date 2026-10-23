"""Cut the committed SAMPLE_MODE snapshot data/sample/ from data/lake/ (task A9)."""

from __future__ import annotations

from pathlib import Path
import tempfile

import pandas as pd

from ingest.lake import read_table, write_table
from tradepulse.contracts import assert_table, table_names, table_path

SAMPLE_ROOT = Path(__file__).resolve().parents[1] / "data" / "sample"
MAX_SAMPLE_MB = 25


def cut_sample(
    lake_root: Path | None = None,
    sample_root: Path = SAMPLE_ROOT,
    showcase_symbols: tuple[str, ...] = (),
    max_ex99_docs: int = 300,
) -> dict[str, int]:
    """Copy the lake into sample_root/data/lake/ with filing_text reduced to the showcase names'
    10-K documents plus at most max_ex99_docs EX-99.1 documents (most recent first).
    Every table is written with lake.write_table so it is validated. Raise RuntimeError if the
    result exceeds MAX_SAMPLE_MB. Return {table_name: row_count}.
    """
    if max_ex99_docs < 0:
        raise ValueError("max_ex99_docs must be nonnegative")
    sample_root = Path(sample_root)
    if (
        table_path("filing_text", lake_root).resolve()
        == table_path("filing_text", sample_root).resolve()
    ):
        raise ValueError("Sample destination must differ from the source lake")
    counts = {}
    # Stage and measure the complete snapshot before publishing any destination table.
    sample_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sample-", dir=sample_root.parent) as temporary:
        stage = Path(temporary)
        for name in table_names():
            frame = read_table(name, lake_root)
            if name == "filing_text":
                annual = frame[
                    frame["document_type"].eq("10-K") & frame["symbol"].isin(showcase_symbols)
                ]
                releases = frame[frame["document_type"].eq("EX-99.1")].sort_values(
                    ["available_at", "accession_number", "document_name", "symbol"],
                    ascending=[False, True, True, True],
                    kind="stable",
                )
                # Count documents, not duplicate rows for different share classes.
                keys = ["accession_number", "document_name"]
                selected = releases[keys].drop_duplicates().head(max_ex99_docs)
                releases = releases.merge(selected, on=keys, how="inner", validate="many_to_one")
                frame = pd.concat([annual, releases], ignore_index=True)
            assert_table(frame, name)
            write_table(frame, name, stage)
            counts[name] = len(frame)
        staged_files = [table_path(name, stage) for name in table_names()]
        size = sum(path.stat().st_size for path in staged_files)
        if size >= MAX_SAMPLE_MB * 1024 * 1024:
            raise RuntimeError(f"Sample is {size} bytes; must be below {MAX_SAMPLE_MB} MiB")
        destinations = {table_path(name, sample_root).resolve() for name in table_names()}
        retained_size = sum(
            path.stat().st_size
            for path in sample_root.rglob("*")
            if path.is_file() and path.resolve() not in destinations
        )
        if size + retained_size >= MAX_SAMPLE_MB * 1024 * 1024:
            raise RuntimeError("Existing sample contents would exceed the size budget")
        for name in table_names():
            # Validate through the public writer again at the final destination.
            write_table(read_table(name, stage), name, sample_root)
    return counts
