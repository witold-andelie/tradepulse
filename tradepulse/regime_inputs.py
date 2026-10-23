"""Fragility indicator series for one pool (SD1.5 step 1), built from quant.regime_indicators."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant import regime_indicators as ri
from quant.indicators import realized_vol
from tradepulse.regime import drawdown_lift, regime_state

HISTORY_ROWS = 60
DRAWDOWN = {"us_equity": 0.07, "eu_equity": 0.07, "crypto": 0.20}


def indicator_series(pool: str, prices: pd.DataFrame, reference: pd.DataFrame, hy_oas: pd.Series | None,
                     regime_cfg: dict, pool_cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily indicator values and 0/1 flags (NaN = unknown) on prices.index.

    reference: wide adj-close panel of reference symbols (benchmark, ^VIX, ^VIX3M, BTC-USD).
    hy_oas: FRED high-yield OAS in percent (None if unavailable).
    """
    idx = prices.index
    year = int(pool_cfg["rows_per_year"])
    values, flags = pd.DataFrame(index=idx), pd.DataFrame(index=idx)

    bench = reference.get(pool_cfg["benchmark"])
    if bench is not None:
        bench = bench.reindex(idx).ffill(limit=3)
        ma = bench.rolling(regime_cfg["trend_ma_days"], min_periods=regime_cfg["trend_ma_days"]).mean()
        values["trend"] = bench / ma
        flags["trend"] = ri.below_ma(bench, regime_cfg["trend_ma_days"])

    if pool == "crypto" and bench is not None:
        vol_pct = ri.rolling_percentile(realized_vol(bench.to_frame(), 20, year).iloc[:, 0], year)
        values["volatility"] = vol_pct
        flags["volatility"] = (vol_pct > regime_cfg["crypto_vol_pctile_trigger"]).astype(float).where(vol_pct.notna())
    elif "^VIX" in reference and "^VIX3M" in reference:
        ratio = ri.term_structure_ratio(reference["^VIX"], reference["^VIX3M"]).reindex(idx).ffill(limit=3)
        values["volatility"] = ratio
        flags["volatility"] = (ratio > regime_cfg["vix_term_ratio_trigger"]).astype(float).where(ratio.notna())

    corr = ri.avg_pairwise_corr(prices, regime_cfg["corr_window_days"])
    corr_pct = ri.rolling_percentile(corr, year)
    values["correlation"] = corr_pct
    flags["correlation"] = (corr_pct > regime_cfg["corr_pctile_trigger"]).astype(float).where(corr_pct.notna())

    breadth = ri.breadth_above_ma(prices, regime_cfg["trend_ma_days"])
    values["breadth"] = breadth
    flags["breadth"] = (breadth < regime_cfg["breadth_below_ma_trigger"]).astype(float).where(breadth.notna())

    if hy_oas is not None and len(hy_oas):
        change_bp = (ri.change(hy_oas.sort_index(), 20) * 100).reindex(idx, method="ffill")
        values["credit"] = change_bp
        flags["credit"] = (change_bp > regime_cfg["hy_oas_change_bp_trigger"]).astype(float).where(change_bp.notna())
    return values, flags


def assess(pool: str, as_of: str, prices: pd.DataFrame, reference: pd.DataFrame, hy_oas: pd.Series | None,
           regime_cfg: dict, pool_cfg: dict, window_start: str) -> dict:
    """Contract RegimeState for the last row of prices, with history and drawdown lift."""
    values, flags = indicator_series(pool, prices, reference, hy_oas, regime_cfg, pool_cfg)
    thresholds = {
        "trend": 1.0,
        "volatility": regime_cfg["crypto_vol_pctile_trigger"] if pool == "crypto" else regime_cfg["vix_term_ratio_trigger"],
        "correlation": regime_cfg["corr_pctile_trigger"],
        "breadth": regime_cfg["breadth_below_ma_trigger"],
        "credit": regime_cfg["hy_oas_change_bp_trigger"],
    }
    notes = {
        "trend": f"{pool_cfg['benchmark']} close / {regime_cfg['trend_ma_days']}-day MA (triggers below 1)",
        "volatility": ("BTC 20d realised vol percentile over 1 year" if pool == "crypto"
                       else "VIX / VIX3M term structure (triggers above 1 = inversion)"),
        "correlation": f"{regime_cfg['corr_window_days']}d mean pairwise correlation, 1-year percentile",
        "breadth": f"share of pool above its {regime_cfg['trend_ma_days']}-day MA (triggers below threshold)",
        "credit": "20-day change in US high-yield OAS, basis points",
    }
    last = prices.index[-1]
    indicators = {}
    for name in flags.columns:
        value, flag = values.at[last, name], flags.at[last, name]
        indicators[name] = {"value": None if pd.isna(value) else float(value), "threshold": float(thresholds[name]),
                            "triggered": None if pd.isna(flag) else bool(flag), "note": notes[name]}
    points = ri.regime_points(flags)
    history = points.iloc[-HISTORY_ROWS:]
    in_window = points.loc[points.index >= pd.Timestamp(window_start)]
    bench = reference.get(pool_cfg["benchmark"])
    lift = None
    if bench is not None and len(in_window) > 40:
        lift = drawdown_lift(in_window, bench.reindex(prices.index).ffill(limit=3).loc[in_window.index], regime_cfg,
                             horizon=20, threshold=DRAWDOWN[pool])
    return regime_state(pool, as_of, indicators, history.astype(np.int64), lift, regime_cfg)
