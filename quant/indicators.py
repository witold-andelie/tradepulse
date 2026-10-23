"""Per-instrument time-series indicators (task C1).

Every function takes wide panels (index = sorted DatetimeIndex, columns = symbols) and returns a
panel of the same shape. A value at row t uses rows <= t only (no look-ahead). Windows need full
history: min_periods = window, otherwise NaN.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """r[t] = P[t] / P[t-1] - 1. No filling of missing prices."""
    return prices / prices.shift(1) - 1


def momentum(prices: pd.DataFrame, lookback: int, skip: int = 0) -> pd.DataFrame:
    """P[t-skip] / P[t-lookback] - 1. Negative lookback or skip raises ValueError."""
    if lookback < 0 or skip < 0:
        raise ValueError("lookback and skip must be non-negative")
    return prices.shift(skip) / prices.shift(lookback) - 1


def reversal(prices: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """-(P[t] / P[t-lookback] - 1). Negative lookback raises ValueError."""
    return -momentum(prices, lookback)


def realized_vol(prices: pd.DataFrame, window: int = 20, periods_per_year: int = 252) -> pd.DataFrame:
    """Rolling std (ddof=1) of simple returns over `window` rows, times sqrt(periods_per_year)."""
    returns = simple_returns(prices)
    return returns.rolling(window, min_periods=window).std(ddof=1) * np.sqrt(periods_per_year)


def volume_zscore(volume: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """(log V[t] - mean(log V[t-window..t-1])) / std(log V[t-window..t-1], ddof=1).

    Non-positive volume counts as missing. The baseline excludes row t. A zero std gives NaN.
    """
    log_volume = np.log(volume.where(volume > 0))
    baseline = log_volume.shift(1).rolling(window, min_periods=window)
    std = baseline.std(ddof=1)
    return (log_volume - baseline.mean()) / std.where(std != 0)


def distance_to_high(prices: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    """P[t] / max(P[t-window+1..t]) - 1 (always <= 0)."""
    return prices / prices.rolling(window, min_periods=window).max() - 1


def moving_average(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling mean over `window` rows."""
    return prices.rolling(window, min_periods=window).mean()


def rolling_beta(prices: pd.DataFrame, benchmark: pd.Series, window: int = 252) -> pd.DataFrame:
    """cov(r_i, r_b) / var(r_b) of simple returns over `window` rows (ddof=1 for both).

    benchmark is a price series; align it to prices.index before computing returns.
    Zero benchmark variance gives NaN.
    """
    aligned = benchmark.reindex(prices.index)
    benchmark_returns = aligned / aligned.shift(1) - 1
    covariance = simple_returns(prices).rolling(window, min_periods=window).cov(benchmark_returns)
    variance = benchmark_returns.rolling(window, min_periods=window).var(ddof=1)
    return covariance.div(variance.where(variance != 0), axis=0)


def attention_change(views: pd.DataFrame, short: int = 7, long: int = 83, lag: int = 1) -> pd.DataFrame:
    """Abnormal attention from daily pageviews.

    v = views shifted down by `lag` rows (day t's views are only complete after the close).
    recent = mean of v over the last `short` rows; base = mean of v over the `long` rows before
    those. Result = log1p(recent) - log1p(base). Negative lag raises ValueError.
    """
    if lag < 0:
        raise ValueError("lag must be non-negative")
    visible = views.shift(lag)
    recent = visible.rolling(short, min_periods=short).mean()
    base = visible.shift(short).rolling(long, min_periods=long).mean()
    return np.log1p(recent) - np.log1p(base)
