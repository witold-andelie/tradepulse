"""Fragility indicators for the regime monitor (task C6). No look-ahead: row t uses rows <= t."""

from __future__ import annotations

import numpy as np
import pandas as pd


def below_ma(series: pd.Series, window: int = 200) -> pd.Series:
    """1.0 where series < its rolling mean (min_periods=window), 0.0 where >=, NaN where the
    mean is undefined."""
    mean = series.rolling(window, min_periods=window).mean()
    return series.lt(mean).astype(float).where(mean.notna())


def term_structure_ratio(vix: pd.Series, vix3m: pd.Series) -> pd.Series:
    """vix / vix3m on the union of dates (NaN where either is missing). > 1 means inversion."""
    return vix / vix3m


def avg_pairwise_corr(prices: pd.DataFrame, window: int = 20, min_names: int = 5) -> pd.Series:
    """Mean off-diagonal Pearson correlation of simple returns over the last `window` rows, using
    only symbols with complete returns in that window. NaN when fewer than min_names qualify or
    the window is not full. Nonfinite returns are incomplete. Constant symbols count toward
    min_names but their undefined correlations are excluded; no defined pairs gives NaN."""
    if window < 1:
        raise ValueError("window must be positive")
    returns = prices.pct_change(fill_method=None).to_numpy(dtype=float)
    result = np.full(len(prices), np.nan)
    for end in range(window, len(prices) + 1):
        trailing = returns[end - window:end]
        complete = trailing[:, np.isfinite(trailing).all(axis=0)]
        if complete.shape[1] < min_names:
            continue
        centered = complete - complete.mean(axis=0)
        norms = np.sqrt(np.square(centered).sum(axis=0))
        varying = norms > 0
        count = int(varying.sum())
        if count < 2:
            continue
        standardized = centered[:, varying] / norms[varying]
        # The squared norm of the sum includes all pairwise dot products and the diagonal.
        squared_sum = np.square(standardized.sum(axis=1)).sum()
        result[end - 1] = np.clip((squared_sum - count) / (count * (count - 1)), -1, 1)
    return pd.Series(result, index=prices.index)


def breadth_above_ma(prices: pd.DataFrame, window: int = 200) -> pd.Series:
    """Share of symbols trading above their own moving average, among the symbols whose average
    is defined. NaN when none are defined."""
    mean = prices.rolling(window, min_periods=window).mean()
    count = mean.notna().sum(axis=1)
    return prices.gt(mean).sum(axis=1) / count.where(count.ne(0))


def rolling_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    """Share of values in the trailing window (including t) that are <= the value at t.
    min_periods = window."""
    return series.rolling(window, min_periods=window).rank(method="max", pct=True)


def change(series: pd.Series, periods: int = 20) -> pd.Series:
    """series[t] - series[t - periods]. Negative periods are rejected to prevent look-ahead."""
    if periods < 0:
        raise ValueError("periods must be nonnegative")
    return series.diff(periods)


def regime_points(flags: pd.DataFrame) -> pd.Series:
    """Row sum of 0/1 indicator flags (NaN counts as 0), as int."""
    return flags.sum(axis=1).astype(int)


def classify_regime(points: pd.Series, elevated_min: int = 2, stressed_min: int = 4) -> pd.Series:
    """'normal' below elevated_min, 'elevated' below stressed_min, otherwise 'stressed'."""
    return pd.Series(
        np.select(
            [points < elevated_min, points < stressed_min],
            ["normal", "elevated"],
            default="stressed",
        ),
        index=points.index,
        name=points.name,
    )
