"""SD1.5 · Ranking: composite score, expected alpha, net edge, tiers, regime overlay, focus list.
Spec: docs/architecture/factors.md (From score to recommendation)."""

from __future__ import annotations

import pandas as pd

TIERS = ("STRONG_OVERWEIGHT", "OVERWEIGHT", "NEUTRAL", "UNDERWEIGHT", "AVOID", "NO_CALL")
MIN_COVERAGE = 0.5


def composite(z: dict[str, pd.Series], weights: dict[str, float]) -> pd.DataFrame:
    """Composite score for one pool on one date.

    z maps factor -> Series (index = symbol) of standardised values (NaN = missing).
    Only factors with weight > 0 are used. The union of symbols across z is the row index,
    sorted. Returns columns:
      score         = sum_f w_f * z_f (a missing z contributes 0)
      coverage      = sum of w_f over factors where z_f is present
      contributions = list of {"factor", "z" (None if missing), "weight", "contribution"} in
                      the order of `weights`, only factors with weight > 0
    """
    raise NotImplementedError


def expected_alpha_bps(ic_comp: float, sigma_daily: pd.Series, horizon: int, score: pd.Series) -> pd.Series:
    """Grinold: ic_comp * sigma_daily * sqrt(horizon) * score * 1e4 (aligned on index)."""
    raise NotImplementedError


def assign_tiers(df: pd.DataFrame, *, ic_comp: float | None, cost_bps_one_way: float, horizon: int,
                 tiers_cfg: dict, valuation_pctile: pd.Series | None = None) -> pd.DataFrame:
    """Add rank, percentile, expected_alpha_bps, cost_bps_round_trip, net_edge_bps, tier.

    df has columns score, coverage, sigma_daily (index = symbol).
    - rank: 1 = highest score; ties broken by symbol ascending. percentile = (n - rank + 1) / n.
    - cost_bps_round_trip = 2 * cost_bps_one_way.
    - If ic_comp is None or <= 0: expected_alpha_bps and net_edge_bps are None, every tier NO_CALL.
    - Else expected_alpha_bps = expected_alpha_bps(...) and
      net_edge_bps = sign(alpha) * (abs(alpha) - cost_bps_round_trip).
    - coverage < MIN_COVERAGE -> NO_CALL, and its alpha and net edge are None.
    - Otherwise, with RT = round-trip cost and the tiers_cfg thresholds:
        percentile >= 1 - strong_overweight_pct and net >= strong_net_edge_cost_multiple * RT -> STRONG_OVERWEIGHT
        percentile >= 1 - overweight_pct and net >= min_net_edge_cost_multiple * RT          -> OVERWEIGHT
        percentile <= avoid_pct and net <= -strong_net_edge_cost_multiple * RT               -> AVOID
        percentile <= underweight_pct and net <= -min_net_edge_cost_multiple * RT            -> UNDERWEIGHT
        else NEUTRAL
      (checked in that order).
    - valuation_pctile (US only): STRONG_OVERWEIGHT with valuation_pctile > valuation_block_pct
      becomes OVERWEIGHT.
    Returns a new frame sorted by rank; the input is not modified.
    """
    raise NotImplementedError


def apply_regime(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """Add regime_adjusted (bool) and downgrade tiers.
    elevated: STRONG_OVERWEIGHT -> OVERWEIGHT.
    stressed: STRONG_OVERWEIGHT -> OVERWEIGHT and OVERWEIGHT -> NEUTRAL (one notch each, based on
    the tier before the overlay). normal: unchanged. Underweight tiers never change.
    Unknown state -> ValueError. Returns a new frame."""
    raise NotImplementedError


def select_focus(df: pd.DataFrame, *, top_k: int, movers_k: int, ret_1d: pd.Series,
                 requested: list[str]) -> list[str]:
    """Symbols to explain, in this order, without duplicates:
    the top_k best ranks excluding NO_CALL, the top_k worst ranks excluding NO_CALL (worst first),
    the movers_k largest abs(ret_1d) among df's symbols (ties by symbol), then requested
    symbols that exist in df."""
    raise NotImplementedError
