"""SD1.5 · Ranking: composite score, expected alpha, net edge, tiers, regime overlay, focus list.
Spec: docs/architecture/factors.md (From score to recommendation)."""

from __future__ import annotations

from math import sqrt

import numpy as np
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
    symbols = sorted({symbol for values in z.values() for symbol in values.index})
    active = [(str(factor), float(weight)) for factor, weight in weights.items() if weight > 0]
    rows = []
    for symbol in symbols:
        score, coverage = 0.0, 0.0
        contributions = []
        for factor, weight in active:
            value = z[factor].get(symbol) if factor in z else None
            value = None if pd.isna(value) else float(value)
            contribution = 0.0 if value is None else weight * value
            score += contribution
            if value is not None:
                coverage += weight
            contributions.append({"factor": factor, "z": value, "weight": weight,
                                  "contribution": contribution})
        rows.append({"score": score, "coverage": coverage, "contributions": contributions})
    return pd.DataFrame(rows, index=symbols, columns=["score", "coverage", "contributions"])


def expected_alpha_bps(ic_comp: float, sigma_daily: pd.Series, horizon: int, score: pd.Series) -> pd.Series:
    """Grinold: ic_comp * sigma_daily * sqrt(horizon) * score * 1e4 (aligned on index)."""
    return float(ic_comp) * sigma_daily * sqrt(horizon) * score * 1e4


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
    out = df.sort_index().sort_values("score", ascending=False, kind="stable").copy()
    out["rank"] = range(1, len(out) + 1)
    out["percentile"] = (len(out) - out["rank"] + 1) / len(out)
    round_trip = float(2 * cost_bps_one_way)
    out["cost_bps_round_trip"] = round_trip
    out["expected_alpha_bps"] = None
    out["net_edge_bps"] = None
    out["tier"] = "NO_CALL"
    if ic_comp is None or not np.isfinite(ic_comp) or ic_comp <= 0:
        return out

    alpha = expected_alpha_bps(ic_comp, out["sigma_daily"], horizon, out["score"])
    valid = (out["coverage"] >= MIN_COVERAGE) & np.isfinite(alpha)
    alpha = alpha.where(valid)
    net = np.sign(alpha) * (alpha.abs() - round_trip)
    out["expected_alpha_bps"] = alpha
    out["net_edge_bps"] = net
    strong_edge = tiers_cfg["strong_net_edge_cost_multiple"] * round_trip
    min_edge = tiers_cfg["min_net_edge_cost_multiple"] * round_trip
    percentile = out["percentile"]
    out["tier"] = np.select(
        [~valid,
         (percentile >= 1 - tiers_cfg["strong_overweight_pct"]) & (net >= strong_edge),
         (percentile >= 1 - tiers_cfg["overweight_pct"]) & (net >= min_edge),
         (percentile <= tiers_cfg["avoid_pct"]) & (net <= -strong_edge),
         (percentile <= tiers_cfg["underweight_pct"]) & (net <= -min_edge)],
        ["NO_CALL", "STRONG_OVERWEIGHT", "OVERWEIGHT", "AVOID", "UNDERWEIGHT"],
        default="NEUTRAL")
    if valuation_pctile is not None:
        blocked = ((out["tier"] == "STRONG_OVERWEIGHT")
                   & (valuation_pctile.reindex(out.index) > tiers_cfg["valuation_block_pct"]))
        out.loc[blocked, "tier"] = "OVERWEIGHT"
    return out


def apply_regime(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """Add regime_adjusted (bool) and downgrade tiers.
    elevated: STRONG_OVERWEIGHT -> OVERWEIGHT.
    stressed: STRONG_OVERWEIGHT -> OVERWEIGHT and OVERWEIGHT -> NEUTRAL (one notch each, based on
    the tier before the overlay). normal: unchanged. Underweight tiers never change.
    Unknown state -> ValueError. Returns a new frame."""
    if state not in ("normal", "elevated", "stressed"):
        raise ValueError(f"unknown regime state {state!r}")
    downgrades = {}
    if state in ("elevated", "stressed"):
        downgrades["STRONG_OVERWEIGHT"] = "OVERWEIGHT"
    if state == "stressed":
        downgrades["OVERWEIGHT"] = "NEUTRAL"
    out = df.copy()
    out["tier"] = df["tier"].map(lambda tier: downgrades.get(tier, tier))
    out["regime_adjusted"] = out["tier"] != df["tier"]
    return out


def select_focus(df: pd.DataFrame, *, top_k: int, movers_k: int, ret_1d: pd.Series,
                 requested: list[str]) -> list[str]:
    """Symbols to explain, in this order, without duplicates:
    the top_k best ranks excluding NO_CALL, the top_k worst ranks excluding NO_CALL (worst first),
    the movers_k largest abs(ret_1d) among df's symbols (ties by symbol), then requested
    symbols that exist in df."""
    eligible = df.loc[df["tier"] != "NO_CALL"].sort_index().sort_values("rank", kind="stable")
    best = list(eligible.head(max(0, top_k)).index)
    worst = list(eligible.sort_values("rank", ascending=False, kind="stable").head(max(0, top_k)).index)
    movers = ret_1d.reindex(df.index).dropna().abs().sort_index().sort_values(
        ascending=False, kind="stable").head(max(0, movers_k))
    candidates = best + worst + list(movers.index) + [symbol for symbol in requested if symbol in df.index]
    return list(dict.fromkeys(candidates))
