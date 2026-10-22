"""Fragility indicators for the regime monitor (task C6). No look-ahead: row t uses rows <= t."""

from __future__ import annotations

import pandas as pd


def below_ma(series: pd.Series, window: int = 200) -> pd.Series:
    """1.0 where series < its rolling mean (min_periods=window), 0.0 where >=, NaN where the
    mean is undefined."""
    raise NotImplementedError("C6")


def term_structure_ratio(vix: pd.Series, vix3m: pd.Series) -> pd.Series:
    """vix / vix3m on the union of dates (NaN where either is missing). > 1 means inversion."""
    raise NotImplementedError("C6")


def avg_pairwise_corr(prices: pd.DataFrame, window: int = 20, min_names: int = 5) -> pd.Series:
    """Mean off-diagonal Pearson correlation of simple returns over the last `window` rows, using
    only symbols with complete returns in that window. NaN when fewer than min_names qualify or
    the window is not full."""
    raise NotImplementedError("C6")


def breadth_above_ma(prices: pd.DataFrame, window: int = 200) -> pd.Series:
    """Share of symbols trading above their own moving average, among the symbols whose average
    is defined. NaN when none are defined."""
    raise NotImplementedError("C6")


def rolling_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    """Share of values in the trailing window (including t) that are <= the value at t.
    min_periods = window."""
    raise NotImplementedError("C6")


def change(series: pd.Series, periods: int = 20) -> pd.Series:
    """series[t] - series[t - periods]."""
    raise NotImplementedError("C6")


def regime_points(flags: pd.DataFrame) -> pd.Series:
    """Row sum of 0/1 indicator flags (NaN counts as 0), as int."""
    raise NotImplementedError("C6")


def classify_regime(points: pd.Series, elevated_min: int = 2, stressed_min: int = 4) -> pd.Series:
    """'normal' below elevated_min, 'elevated' below stressed_min, otherwise 'stressed'."""
    raise NotImplementedError("C6")
