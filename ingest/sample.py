"""Validated, staged offline snapshots with a strict size limit."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd

from ingest.common import showcase
from ingest.lake import read_table, write_table
from tradepulse.contracts import table_names, table_path

SAMPLE_ROOT = Path(__file__).resolve().parents[1] / "data" / "sample"
MAX_SAMPLE_MB = 25


def cut_sample(
    lake_root: Path | None = None,
    sample_root: Path = SAMPLE_ROOT,
    showcase_symbols: tuple[str, ...] = (),
    max_ex99_docs: int = 300,
) -> dict[str, int]:
    if max_ex99_docs < 0:
        raise ValueError("max_ex99_docs must be nonnegative")
    sample_root = Path(sample_root)
    if table_path("filing", lake_root).resolve() == table_path("filing", sample_root).resolve():
        raise ValueError("Sample destination must differ from the source lake")
    names = showcase_symbols or showcase()
    counts = {}
    sample_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sample-", dir=sample_root.parent) as temporary:
        staging = Path(temporary)
        for name in table_names():
            data = read_table(name, lake_root)
            if data.empty:
                raise ValueError(f"Cannot publish an empty sample table: {name}")
            if name == "filing_text":
                ordered = data.sort_values(
                    ["available_at", "accession_number", "document_name", "symbol"],
                    ascending=[False, True, True, True],
                )
                annual = ordered[(ordered.document_type == "10-K") & ordered.symbol.isin(names)]
                exhibits = ordered[ordered.document_type == "EX-99.1"]
                # A single document can have rows for several share classes. Limit documents,
                # then retain every symbol attached to the selected document keys.
                keys = ["accession_number", "document_name"]
                selected = exhibits[keys].drop_duplicates().head(max_ex99_docs)
                exhibits = exhibits.merge(selected, on=keys, how="inner", validate="many_to_one")
                data = pd.concat([annual, exhibits], ignore_index=True)
                if data.empty:
                    raise ValueError("Text selection would produce an empty sample table")
            write_table(data, name, staging)
            counts[name] = len(data)
        size = sum(p.stat().st_size for p in staging.rglob("*") if p.is_file())
        # Include existing non-table artifacts in the total destination size.
        expected = {table_path(n, sample_root).resolve() for n in table_names()}
        size += sum(
            p.stat().st_size
            for p in sample_root.rglob("*")
            if p.is_file() and p.resolve() not in expected
        )
        if size >= MAX_SAMPLE_MB * 1024 * 1024:
            raise RuntimeError(f"Sample exceeds size limit: {size} bytes")
        for name in table_names():
            destination = table_path(name, sample_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(table_path(name, staging), destination)
    return counts
