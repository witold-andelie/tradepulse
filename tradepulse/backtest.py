"""Walk-forward evaluation: simulate past decisions with only the data available at the time,
then settle them against realised returns. Fills the TrackRecord and supplies an out-of-sample
composite IC and point-in-time weights for today's ranking.

Timeline for a decision on row d (L = execution lag, h = primary horizon):
- weights and IC_comp are fitted on rows whose forward returns are already known at d:
  rows [window_start, d - h - L] (inclusive) of the factor panels and prices;
- the decision uses the panels' row d (each panel row is point-in-time by construction);
- the outcome is the excess return from close d+L to close d+L+h over the pool benchmark.
"""

from __future__ import annotations

import pandas as pd

WF_FACTORS_EXCLUDED = ("evt_drift", "rel_spillover")  # their priors/edges are fitted in-sample


def decision_rows(index: pd.DatetimeIndex, window_start: str, *, burn_in: int, step: int) -> list[int]:
    """Row positions of decision dates: start at the first row >= window_start plus burn_in rows,
    then every `step` rows, up to and including the last row."""
    raise NotImplementedError


def fit_rows(d: int, *, horizon: int, lag: int, first: int) -> tuple[int, int] | None:
    """(start, end) inclusive row range used to fit weights for a decision on row d:
    start = first (window-start row), end = d - horizon - lag. None when end - start + 1 < 40."""
    raise NotImplementedError


def walk_forward(pool: str, panels: dict[str, pd.DataFrame], prices: pd.DataFrame, benchmark: pd.Series,
                 regime_points: pd.Series, cfg: dict, window_start: str, *, refit_every: int = 20,
                 burn_in: int = 120) -> dict:
    """Run the walk-forward for one pool.

    - Factors in WF_FACTORS_EXCLUDED are dropped before anything else.
    - Decisions on decision_rows(prices.index, window_start, burn_in=burn_in,
      step=cfg["backtest"]["primary_horizon"]).
    - Weights are refitted (tradepulse.research.evaluate.research_pool on the fit_rows slice, window =
      the slice's first and last dates) on the first decision and then whenever at least refit_every
      rows passed since the last fit; between refits the latest weights are reused. IC_comp at
      a refit = composite_ic on the same slice (primary horizon, execution lag, min names). Decisions
      without any fit yet are skipped.
    - At a decision: tradepulse.ranking.composite on the panels' row d with the current weights ->
      join sigma_daily (20-row realised vol on prices up to d, per row) -> assign_tiers with the
      current IC_comp, the pool cost and cfg["tiers"] -> apply_regime with
      tradepulse.regime.classify(regime_points at row d) (normal when unknown).
    - Outcome per symbol: settled when row d + L + h exists: excess = quant.settlement.excess_return
      (P[d+L], P[d+L+h], B[d+L], B[d+L+h]); hit = quant.settlement.hit(tier, excess). Otherwise pending.
    - Realised composite rank IC per decision: Spearman between composite score and the symbol
      forward return P[d+L+h]/P[d+L]-1 (quant.evaluation.rank_ic semantics, min_names from cfg).

    Returns {
      "by_tier": [{"pool", "tier", "n", "hit_rate", "mean_excess_bps"}] for every tier with n > 0
                 (hit_rate None for NEUTRAL / NO_CALL),
      "calibration_rows": list of (score percentile, 1 if excess > 0 else 0) for settled outcomes,
      "ic_series": [{"date", "pool", "ic"}] per settled decision,
      "settled": int, "pending": int,
      "ic_comp_oos": mean of the realised composite ICs (None if none),
      "latest_weights": weights fitted on the latest possible fit range for the last row of prices
                        (the point-in-time weights to use today), "latest_ic_comp": its IC_comp,
      "decisions": int (number of decision dates evaluated),
      "decision_tiers": {ISO date of row d: {symbol: tier}} for every evaluated decision,
    }. All numbers are plain Python types; never mutates inputs. A decision on row d may only use
    prices and panel rows <= d (outcomes excepted), which tests check by perturbing later prices.
    """
    raise NotImplementedError


def track_record(results: list[dict], window: dict, n_buckets: int = 5) -> dict:
    """Merge per-pool walk_forward results into a contract TrackRecord:
    mode "walk_forward", window, settled_count / pending_count (sums), by_tier (concatenated),
    calibration = quant.settlement.calibration_table over all calibration_rows (predicted = mean
    score percentile, observed = share outperforming the benchmark; empty buckets -> n 0 and None
    means), composite_ic_series (concatenated, ic None when NaN). Validates with
    tradepulse.contracts.assert_payload(..., "TrackRecord")."""
    raise NotImplementedError
