"""Cost model and expected alpha (task C4). All costs are in basis points (1 bp = 0.0001)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def round_trip_bps(cost_bps_one_way: float) -> float:
    """Entering and exiting a position: 2 x the one-way cost."""
    return float(2 * cost_bps_one_way)


def turnover(w_old: pd.Series, w_new: pd.Series) -> float:
    """sum |w_new - w_old| over the union of symbols (a missing weight counts as 0)."""
    old, new = w_old.align(w_new, join="outer")
    return float((new.fillna(0) - old.fillna(0)).abs().sum())


def cost_return(turnover_value: float, cost_bps_one_way: float) -> float:
    """Return lost to costs: turnover * cost_bps_one_way / 1e4."""
    return float(turnover_value * cost_bps_one_way / 1e4)


def expected_alpha_bps(ic, sigma_daily, horizon: int, score):
    """Grinold: alpha = IC * sigma * z, with sigma scaled to the horizon.
    = ic * sigma_daily * sqrt(horizon) * score * 1e4. Works element-wise on Series."""
    return ic * sigma_daily * np.sqrt(horizon) * score * 1e4


def net_edge_bps(alpha_bps, cost_bps_one_way: float):
    """sign(alpha) * (|alpha| - round_trip_bps(cost)). NaN stays NaN. Works on Series."""
    return np.sign(alpha_bps) * (np.abs(alpha_bps) - round_trip_bps(cost_bps_one_way))
