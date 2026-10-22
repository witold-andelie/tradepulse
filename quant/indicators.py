"""Per-instrument time-series indicators (task C1).

Every function takes wide panels (index = sorted DatetimeIndex, columns = symbols) and returns a
panel of the same shape. A value at row t uses rows <= t only (no look-ahead). Windows need full
history: min_periods = window, otherwise NaN.
"""

from __future__ import annotations

import pandas as pd


def simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """r[t] = P[t] / P[t-1] - 1. No filling of missing prices."""
    raise NotImplementedError("C1")


def momentum(prices: pd.DataFrame, lookback: int, skip: int = 0) -> pd.DataFrame:
    """P[t-skip] / P[t-lookback] - 1."""
    raise NotImplementedError("C1")


def reversal(prices: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """-(P[t] / P[t-lookback] - 1)."""
    raise NotImplementedError("C1")


def realized_vol(prices: pd.DataFrame, window: int = 20, periods_per_year: int = 252) -> pd.DataFrame:
    """Rolling std (ddof=1) of simple returns over `window` rows, times sqrt(periods_per_year)."""
    raise NotImplementedError("C1")


def volume_zscore(volume: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """(log V[t] - mean(log V[t-window..t-1])) / std(log V[t-window..t-1], ddof=1).

    Non-positive volume counts as missing. The baseline excludes row t. A zero std gives NaN.
    """
    raise NotImplementedError("C1")


def distance_to_high(prices: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    """P[t] / max(P[t-window+1..t]) - 1 (always <= 0)."""
    raise NotImplementedError("C1")


def moving_average(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling mean over `window` rows."""
    raise NotImplementedError("C1")


def rolling_beta(prices: pd.DataFrame, benchmark: pd.Series, window: int = 252) -> pd.DataFrame:
    """cov(r_i, r_b) / var(r_b) of simple returns over `window` rows (ddof=1 for both).

    benchmark is a price series; align it to prices.index before computing returns.
    """
    raise NotImplementedError("C1")


def attention_change(views: pd.DataFrame, short: int = 7, long: int = 83, lag: int = 1) -> pd.DataFrame:
    """Abnormal attention from daily pageviews.

    v = views shifted down by `lag` rows (day t's views are only complete after the close).
    recent = mean of v over the last `short` rows; base = mean of v over the `long` rows before
    those. Result = log1p(recent) - log1p(base).
    """
    raise NotImplementedError("C1")
