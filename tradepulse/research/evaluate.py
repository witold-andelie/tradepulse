"""SD1.4 steps 4-6: evaluate standardised factor panels, gate them, weight them, build cards.
Evaluation here is the in-sample research window; cards say so (evaluation_mode)."""

from __future__ import annotations

import pandas as pd

from tradepulse.research.gates import FactorMetrics

FACTOR_SPECS: dict[str, dict] = {
    "pv_mom_12_1": {"title": "12-1 month momentum", "measures": "12-month trend, skipping the last month",
                    "definition": "P[t-m]/P[t-y] - 1", "sources": ["price_bar"], "availability": "close t"},
    "pv_mom_1m": {"title": "1-month momentum", "measures": "1-month trend",
                  "definition": "P[t]/P[t-m] - 1", "sources": ["price_bar"], "availability": "close t"},
    "pv_rev_5d": {"title": "5-day reversal", "measures": "short-term reversal",
                  "definition": "-(P[t]/P[t-5] - 1)", "sources": ["price_bar"], "availability": "close t"},
    "pv_lowvol_20d": {"title": "Low volatility", "measures": "low-volatility premium",
                      "definition": "-std(r[t-19..t]) * sqrt(rows_per_year)", "sources": ["price_bar"],
                      "availability": "close t"},
    "pv_volume_z": {"title": "Volume z-score", "measures": "abnormal trading activity",
                    "definition": "(log V[t] - mean(log V[t-60..t-1])) / std(...)", "sources": ["price_bar"],
                    "availability": "close t"},
    "pv_dist_52w_high": {"title": "Distance to 52-week high", "measures": "anchoring to the 52-week high",
                         "definition": "P[t]/max(P[t-y+1..t]) - 1", "sources": ["price_bar"],
                         "availability": "close t"},
    "att_pageviews": {"title": "Wikipedia attention", "measures": "abnormal public attention not explained by price-volume",
                      "definition": "log1p(7d mean views) - log1p(83d base), residualised on |5d return|, volume z, low vol",
                      "sources": ["pageview", "price_bar"], "availability": "day t-1"},
    "earn_sue": {"title": "Earnings surprise (SUE)", "measures": "standardised unexpected diluted EPS",
                 "definition": "seasonal random-walk SUE, first-reported values, held 60 rows",
                 "sources": ["fundamental_fact"], "availability": "filing acceptance + 1 row"},
    "earn_demand_language": {"title": "Demand language", "measures": "management says demand exceeds supply",
                             "definition": "signed demand-signal intensity from 8-K EX-99.1, held 60 rows",
                             "sources": ["filing_text"], "availability": "filing acceptance + 1 row"},
    "evt_drift": {"title": "Event drift", "measures": "post-event drift after 8-K events",
                  "definition": "sum prior(type) * direction * exp(-(t-d)/10), rows 1..20 after the event",
                  "sources": ["filing", "filing_text"], "availability": "filing acceptance + 1 row"},
    "rel_spillover": {"title": "Relational spillover", "measures": "shocks at linked companies not yet priced",
                      "definition": "weighted 5-day residual-return shock of validated graph neighbours, lagged 1 row",
                      "sources": ["price_bar", "graph"], "availability": "close t-1"},
}


def factor_metrics(factor: str, pool: str, z: pd.DataFrame, prices: pd.DataFrame, *, horizons: list[int],
                   primary_horizon: int, lag: int, cost_bps_one_way: float, rows_per_year: int,
                   min_names: int) -> FactorMetrics:
    """Evaluate one standardised panel with quant.evaluation.

    - coverage = non-null cells of z / non-null cells of prices (0 when prices is empty).
    - ic_by_horizon[h] = ic_summary(rank_ic(z, forward_returns(prices, h, lag), min_names), h) mapped
      to {"mean", "t_stat", "ir", "n" (int)}; NaN values become None.
    - n_dates = number of non-NaN rank ICs at primary_horizon.
    - same_day_ic = mean of same_day_ic(z, prices, min_names) (None if no value).
    - long_short from quantile_long_short(z, prices, primary_horizon, lag, 0.2, cost_bps_one_way,
      rows_per_year): gross_ann_return, net_ann_return, net_sharpe (= sharpe_net), max_drawdown,
      turnover_per_rebalance (= mean turnover). NaN -> None.
    - half_split_agree = half_split_sign_agreement(primary-horizon rank IC series).
    - spec_complete = factor in FACTOR_SPECS.
    """
    raise NotImplementedError


def research_pool(pool: str, panels: dict[str, pd.DataFrame], prices: pd.DataFrame, cfg: dict,
                  window: tuple[str, str]) -> dict:
    """Gate and weight every factor of one pool on the research window.

    - Evaluate only rows whose date is within [window start, window end] (ISO strings) for both
      panels and prices.
    - cfg is the full config (load_config()). Uses cfg["backtest"] (horizons, primary_horizon,
      execution_lag_days), cfg["gates"], cfg["factors"]["min_names_per_date"] and
      cfg["pools"][pool] (cost_bps_one_way, rows_per_year).
    - For each factor (sorted by name): factor_metrics -> evaluate_gates -> later build_card.
    - weights = compute_weights([{"factor", "status", "ir" at primary horizon}], gates
      ic_weight_shrinkage).
    - cards = build_card(...) for every factor, with its weight, window {"start", "end"} and
      FACTOR_SPECS[factor].
    Returns {"cards": [FactorCard], "weights": {factor: w}, "metrics": {factor: FactorMetrics}}.
    """
    raise NotImplementedError


def composite_ic(panels: dict[str, pd.DataFrame], weights: dict[str, float], prices: pd.DataFrame, *,
                 primary_horizon: int, lag: int, min_names: int) -> float | None:
    """Mean rank IC (primary horizon) of the composite sum_f w_f * z_f, where a missing z
    contributes 0 but a cell with no factor present at all stays NaN. Factors with weight 0 are
    ignored. Returns None when no weight is positive or no IC is defined."""
    raise NotImplementedError
