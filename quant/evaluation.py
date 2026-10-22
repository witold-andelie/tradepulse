"""Factor evaluation: forward returns, rank IC, IC decay, long-short, lead-lag (task C3).

This is the only module that may look forward in time, and only to build evaluation targets.
"""

from __future__ import annotations

import pandas as pd


def forward_returns(prices: pd.DataFrame, horizon: int, lag: int = 1) -> pd.DataFrame:
    """fwd[t] = P[t+lag+horizon] / P[t+lag] - 1. A signal known at the close of t is traded at
    the close of t+lag. The last lag+horizon rows are NaN."""
    raise NotImplementedError("C3")


def rank_ic(factor: pd.DataFrame, target: pd.DataFrame, min_names: int = 20) -> pd.Series:
    """Spearman correlation between factor and target per date, using the symbols where both are
    present. Fewer than min_names symbols, or zero variance -> NaN. Indexed by factor's dates."""
    raise NotImplementedError("C3")


def ic_summary(ic: pd.Series, horizon: int = 1) -> dict[str, float]:
    """Summary of an IC series using non-overlapping observations.

    x = ic.dropna().iloc[::horizon]. Returns {"mean", "std" (ddof=1), "t_stat" =
    mean / (std / sqrt(n)), "ir" = mean / std, "n"}. With n < 2 or std == 0, std, t_stat and ir
    are NaN.
    """
    raise NotImplementedError("C3")


def ic_decay(factor: pd.DataFrame, prices: pd.DataFrame, horizons=(1, 5, 20), lag: int = 1,
             min_names: int = 20) -> pd.DataFrame:
    """For each horizon h, ic_summary(rank_ic(factor, forward_returns(prices, h, lag)), h).
    Returns a DataFrame indexed by horizon with columns mean_ic, t_stat, n."""
    raise NotImplementedError("C3")


def same_day_ic(factor: pd.DataFrame, prices: pd.DataFrame, min_names: int = 20) -> pd.Series:
    """rank_ic of the factor against the SAME day's simple return: a descriptive check
    ("does it explain today's move?"), never a predictive one."""
    raise NotImplementedError("C3")


def quantile_long_short(factor: pd.DataFrame, prices: pd.DataFrame, horizon: int, lag: int = 1,
                        quantile: float = 0.2, cost_bps_one_way: float = 0.0,
                        periods_per_year: int = 252) -> dict:
    """Equal-weight top-minus-bottom portfolio, rebalanced every `horizon` rows.

    - Rebalance dates: factor.index[::horizon].
    - Eligible names on a date: factor and forward return (forward_returns(prices, horizon, lag))
      both present.
    - k = max(1, floor(n_eligible * quantile)). Long the k highest factor values, short the k
      lowest. Ties are broken by column order (rank method "first").
    - Weights +1/k and -1/k. A date with fewer than 2*k eligible names, or with k < 1, is skipped.
    - gross = mean fwd(long) - mean fwd(short).
    - turnover = sum of abs(w_new - w_prev) over the union of names (the first rebalance is
      measured against zero weights, so its turnover is 2).
    - net = gross - turnover * cost_bps_one_way / 1e4.

    Returns {"gross": Series, "net": Series, "turnover": Series (all indexed by rebalance date),
    "ann_return_gross", "ann_return_net" (mean * periods_per_year / horizon),
    "sharpe_net" (mean / std(ddof=1) * sqrt(periods_per_year / horizon); NaN if std is 0 or
    there is one period), "max_drawdown" (min of cumprod(1 + net) / its running max - 1)}.
    """
    raise NotImplementedError("C3")


def half_split_sign_agreement(ic: pd.Series) -> bool:
    """True when the mean of the first half and the mean of the second half of ic.dropna() have
    the same strict sign (len // 2 split). Fewer than 4 observations -> False. Return a Python bool."""
    raise NotImplementedError("C3")


def lead_lag_tstat(leader: pd.Series, follower: pd.Series, lag: int = 1) -> dict[str, float]:
    """Does the leader's move predict the follower's move `lag` rows later?

    r = Pearson correlation of leader.shift(lag) and follower over the dates where both are
    present. Returns {"r", "t_stat" = r * sqrt(n - 2) / sqrt(1 - r**2), "n"}. With n < 3,
    r and t_stat are NaN.
    """
    raise NotImplementedError("C3")
