"""Cut the committed SAMPLE_MODE snapshot data/sample/ from data/lake/ (task A9)."""

from __future__ import annotations

from pathlib import Path

SAMPLE_ROOT = Path(__file__).resolve().parents[1] / "data" / "sample"
MAX_SAMPLE_MB = 25


def cut_sample(lake_root: Path | None = None, sample_root: Path = SAMPLE_ROOT,
               showcase_symbols: tuple[str, ...] = (), max_ex99_docs: int = 300) -> dict[str, int]:
    """Copy the lake into sample_root/data/lake/ with filing_text reduced to the showcase names'
    10-K documents plus at most max_ex99_docs EX-99.1 documents (most recent first).
    Every table is written with lake.write_table so it is validated. Raise RuntimeError if the
    result exceeds MAX_SAMPLE_MB. Return {table_name: row_count}.
    """
    raise NotImplementedError("A9")
