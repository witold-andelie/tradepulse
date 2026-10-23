"""Factor evaluation: forward returns, rank IC, IC decay, long-short, lead-lag (task C3).

This is the only module that may look forward in time, and only to build evaluation targets.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant.indicators import simple_returns


def forward_returns(prices: pd.DataFrame, horizon: int, lag: int = 1) -> pd.DataFrame:
    """fwd[t] = P[t+lag+horizon] / P[t+lag] - 1. A signal known at the close of t is traded at
    the close of t+lag. The last lag+horizon rows are NaN.
    Non-positive horizon or negative lag raises ValueError.
    """
    if horizon <= 0 or lag < 0:
        raise ValueError("horizon must be positive and lag must be non-negative")
    return prices.shift(-(lag + horizon)) / prices.shift(-lag) - 1


def rank_ic(factor: pd.DataFrame, target: pd.DataFrame, min_names: int = 20) -> pd.Series:
    """Spearman correlation between factor and target per date, using the symbols where both are
    present. Fewer than min_names symbols, or zero variance -> NaN. Indexed by factor's dates.
    Target labels are aligned to factor before selecting pairs and ranking.
    """
    target = target.reindex(index=factor.index, columns=factor.columns)
    complete = factor.notna() & target.notna()
    factor_ranks = factor.where(complete).rank(axis=1, method="average")
    target_ranks = target.where(complete).rank(axis=1, method="average")
    left = factor_ranks.sub(factor_ranks.mean(axis=1), axis=0).to_numpy(dtype=float)
    right = target_ranks.sub(target_ranks.mean(axis=1), axis=0).to_numpy(dtype=float)
    numerator = np.nansum(left * right, axis=1)
    denominator = np.sqrt(np.nansum(left**2, axis=1) * np.nansum(right**2, axis=1))
    valid = (complete.sum(axis=1).to_numpy() >= min_names) & (denominator > 0)
    correlation = np.full(len(factor), np.nan)
    np.divide(numerator, denominator, out=correlation, where=valid)
    return pd.Series(np.clip(correlation, -1.0, 1.0), index=factor.index)


def ic_summary(ic: pd.Series, horizon: int = 1) -> dict[str, float]:
    """Summary of an IC series using non-overlapping observations.

    x = ic.dropna().iloc[::horizon]. Returns {"mean", "std" (ddof=1), "t_stat" =
    mean / (std / sqrt(n)), "ir" = mean / std, "n"}. With n < 2 or std == 0, std, t_stat and ir
    are NaN. Non-positive horizon raises ValueError.
    """
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    x = ic.dropna().iloc[::horizon]
    n = len(x)
    mean = float(x.mean())
    std = float(x.std(ddof=1)) if n >= 2 else float("nan")
    if std == 0:
        std = float("nan")
    return {
        "mean": mean,
        "std": std,
        "t_stat": float(mean / (std / np.sqrt(n))) if n >= 2 else float("nan"),
        "ir": float(mean / std),
        "n": float(n),
    }


def ic_decay(factor: pd.DataFrame, prices: pd.DataFrame, horizons=(1, 5, 20), lag: int = 1,
             min_names: int = 20) -> pd.DataFrame:
    """For each horizon h, ic_summary(rank_ic(factor, forward_returns(prices, h, lag)), h).
    Returns a DataFrame indexed by horizon with columns mean_ic, t_stat, n."""
    rows = []
    index = []
    for horizon in horizons:
        target = forward_returns(prices, horizon, lag)
        summary = ic_summary(rank_ic(factor, target, min_names), horizon)
        rows.append((summary["mean"], summary["t_stat"], summary["n"]))
        index.append(horizon)
    return pd.DataFrame(rows, index=index, columns=["mean_ic", "t_stat", "n"])


def same_day_ic(factor: pd.DataFrame, prices: pd.DataFrame, min_names: int = 20) -> pd.Series:
    """rank_ic of the factor against the SAME day's simple return: a descriptive check
    ("does it explain today's move?"), never a predictive one."""
    return rank_ic(factor, simple_returns(prices), min_names)


def quantile_long_short(factor: pd.DataFrame, prices: pd.DataFrame, horizon: int, lag: int = 1,
                        quantile: float = 0.2, cost_bps_one_way: float = 0.0,
                        periods_per_year: int = 252) -> dict:
    """Equal-weight top-minus-bottom portfolio, rebalanced every `horizon` rows.

    - Rebalance dates: factor.index[::horizon].
    - Eligible names on a date: factor and forward return (forward_returns(prices, horizon, lag))
      both present.
    - k = max(1, floor(n_eligible * quantile)). Long the k highest factor values, short the k
      lowest. Ties are broken by column order (ascending rank method "first").
    - Weights +1/k and -1/k. A date with fewer than 2*k eligible names, or with k < 1, is skipped.
    - gross = mean fwd(long) - mean fwd(short).
    - turnover = sum of abs(w_new - w_prev) over the union of names (the first rebalance is
      measured against zero weights, so its turnover is 2).
    - net = gross - turnover * cost_bps_one_way / 1e4.

    Returns {"gross": Series, "net": Series, "turnover": Series (all indexed by rebalance date),
    "ann_return_gross", "ann_return_net" (mean * periods_per_year / horizon),
    "sharpe_net" (mean / std(ddof=1) * sqrt(periods_per_year / horizon); NaN if std is 0 or
    there is one period), "max_drawdown" (min of cumprod(1 + net) / its running max - 1)}.
    Skipped dates retain the previous weights for the next turnover calculation. With no valid
    rebalances, the series are empty and scalar statistics are NaN. Horizon and lag restrictions
    are the same as forward_returns.
    """
    target = forward_returns(prices, horizon, lag).reindex(
        index=factor.index, columns=factor.columns
    ).iloc[::horizon]
    signals = factor.iloc[::horizon]
    eligible = signals.notna() & target.notna()
    counts = eligible.sum(axis=1).to_numpy()
    sizes = np.maximum(1, np.floor(counts * quantile))
    valid = counts >= 2 * sizes
    ranks = signals.where(eligible).rank(axis=1, method="first").to_numpy()[valid]
    sizes = sizes[valid, None]
    counts = counts[valid, None]
    weights = np.where(
        ranks > counts - sizes, 1 / sizes, np.where(ranks <= sizes, -1 / sizes, 0.0)
    )
    index = signals.index[valid]
    gross = pd.Series(
        np.nansum(weights * target.to_numpy(dtype=float)[valid], axis=1),
        index=index, name="gross",
    )
    turnover = pd.Series(
        np.abs(np.diff(weights, axis=0, prepend=np.zeros((1, weights.shape[1])))).sum(axis=1),
        index=index, name="turnover",
    )
    net = (gross - turnover * cost_bps_one_way / 1e4).rename("net")
    annualization = periods_per_year / horizon
    std = float(net.std(ddof=1)) if len(net) >= 2 else float("nan")
    sharpe = float(net.mean() / std * np.sqrt(annualization)) if std > 0 else float("nan")
    wealth = (1 + net).cumprod()
    return {
        "gross": gross,
        "net": net,
        "turnover": turnover,
        "ann_return_gross": float(gross.mean() * annualization),
        "ann_return_net": float(net.mean() * annualization),
        "sharpe_net": sharpe,
        "max_drawdown": float((wealth / wealth.cummax() - 1).min()),
    }


def half_split_sign_agreement(ic: pd.Series) -> bool:
    """True when the mean of the first half and the mean of the second half of ic.dropna() have
    the same strict sign (len // 2 split). Fewer than 4 observations -> False. Return a Python bool."""
    x = ic.dropna()
    if len(x) < 4:
        return False
    split = len(x) // 2
    first, second = x.iloc[:split].mean(), x.iloc[split:].mean()
    return bool((first > 0 and second > 0) or (first < 0 and second < 0))


def lead_lag_tstat(leader: pd.Series, follower: pd.Series, lag: int = 1) -> dict[str, float]:
    """Does the leader's move predict the follower's move `lag` rows later?

    r = Pearson correlation of leader.shift(lag) and follower over the dates where both are
    present. Returns {"r", "t_stat" = r * sqrt(n - 2) / sqrt(1 - r**2), "n"}. With n < 3,
    r and t_stat are NaN. Constant inputs also give NaN; perfect correlation gives a signed
    infinite t-statistic. Negative lag raises ValueError.
    """
    if lag < 0:
        raise ValueError("lag must be non-negative")
    pairs = pd.concat([leader.shift(lag), follower], axis=1, join="inner").dropna()
    n = len(pairs)
    r = t_stat = float("nan")
    if n >= 3 and (pairs.std(ddof=1) > 0).all():
        r = float(np.clip(pairs.iloc[:, 0].corr(pairs.iloc[:, 1]), -1.0, 1.0))
        if abs(r) == 1:
            t_stat = float(np.copysign(np.inf, r))
        else:
            t_stat = float(r * np.sqrt(n - 2) / np.sqrt(1 - r**2))
    return {"r": r, "t_stat": t_stat, "n": float(n)}
