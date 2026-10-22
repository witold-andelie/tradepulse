"""Scoring settled recommendations (task C7)."""

from __future__ import annotations

import pandas as pd

LONG_TIERS = ("STRONG_OVERWEIGHT", "OVERWEIGHT")
SHORT_TIERS = ("UNDERWEIGHT", "AVOID")


def excess_return(entry_px: float, exit_px: float, bench_entry: float, bench_exit: float) -> float:
    """(exit / entry - 1) - (bench_exit / bench_entry - 1)."""
    raise NotImplementedError("C7")


def hit(tier: str, excess: float) -> bool | None:
    """Long tiers hit when excess > 0, short tiers when excess < 0 (Python bool); NEUTRAL and NO_CALL -> None."""
    raise NotImplementedError("C7")


def brier_score(probs: pd.Series, outcomes: pd.Series) -> float:
    """mean((p - o)^2) with outcomes in {0, 1}."""
    raise NotImplementedError("C7")


def calibration_table(probs: pd.Series, outcomes: pd.Series, n_buckets: int = 5) -> pd.DataFrame:
    """Columns bucket_low, bucket_high, n, predicted (mean p), observed (mean outcome).

    Buckets are [i/n, (i+1)/n), and the last bucket includes 1.0. An empty bucket has n = 0 and
    NaN means. Always returns n_buckets rows.
    """
    raise NotImplementedError("C7")
