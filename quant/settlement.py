"""Scoring settled recommendations (task C7)."""

from __future__ import annotations

import numpy as np
import pandas as pd

LONG_TIERS = ("STRONG_OVERWEIGHT", "OVERWEIGHT")
SHORT_TIERS = ("UNDERWEIGHT", "AVOID")


def excess_return(entry_px: float, exit_px: float, bench_entry: float, bench_exit: float) -> float:
    """(exit / entry - 1) - (bench_exit / bench_entry - 1)."""
    return float((exit_px / entry_px - 1) - (bench_exit / bench_entry - 1))


def hit(tier: str, excess: float) -> bool | None:
    """Long tiers hit when excess > 0, short tiers when excess < 0 (Python bool).

    NEUTRAL and NO_CALL return None. Unknown tiers raise ValueError.
    """
    if tier in LONG_TIERS:
        return bool(excess > 0)
    if tier in SHORT_TIERS:
        return bool(excess < 0)
    if tier in ("NEUTRAL", "NO_CALL"):
        return None
    raise ValueError(f"Unknown tier: {tier}")


def brier_score(probs: pd.Series, outcomes: pd.Series) -> float:
    """mean((p - o)^2) with outcomes in {0, 1}, aligned by index and omitting missing pairs."""
    return float(((probs - outcomes) ** 2).mean())


def calibration_table(probs: pd.Series, outcomes: pd.Series, n_buckets: int = 5) -> pd.DataFrame:
    """Columns bucket_low, bucket_high, n, predicted (mean p), observed (mean outcome).

    Buckets are [i/n, (i+1)/n), and the last bucket includes 1.0. An empty bucket has n = 0 and
    NaN means. Always returns n_buckets rows.
    Inputs align by index and missing pairs are omitted. n_buckets must be positive;
    nonmissing probabilities outside [0, 1] raise ValueError.
    """
    if n_buckets < 1:
        raise ValueError("n_buckets must be positive")
    if ((probs < 0) | (probs > 1)).any():
        raise ValueError("probabilities must be within [0, 1]")
    paired = pd.concat([probs.rename("predicted"), outcomes.rename("observed")], axis=1)
    paired = paired.dropna()
    edges = np.arange(n_buckets + 1) / n_buckets
    buckets = np.minimum(
        np.searchsorted(edges, paired["predicted"], side="right") - 1, n_buckets - 1
    )
    grouped = paired.groupby(buckets).agg(
        n=("predicted", "size"),
        predicted=("predicted", "mean"),
        observed=("observed", "mean"),
    ).reindex(range(n_buckets))
    grouped["n"] = grouped["n"].fillna(0).astype(int)
    grouped.insert(0, "bucket_low", edges[:-1])
    grouped.insert(1, "bucket_high", edges[1:])
    return grouped
