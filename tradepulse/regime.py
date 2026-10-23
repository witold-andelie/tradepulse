"""SD1.5 · Assessing Regime (fragility monitor). Spec: docs/architecture/factors.md (Regime)."""

from __future__ import annotations

import pandas as pd

INDICATORS = ("trend", "volatility", "correlation", "breadth", "credit")


def classify(points: int, regime_cfg: dict) -> str:
    """'normal' if points < elevated_min_points, 'elevated' if < stressed_min_points, else 'stressed'."""
    raise NotImplementedError


def regime_state(pool: str, as_of: str, indicators: dict[str, dict], history: pd.Series,
                 lift: dict | None, regime_cfg: dict) -> dict:
    """Contract-valid RegimeState.

    indicators: name -> {"value", "threshold", "triggered" (bool or None), "note"} for every name
    in INDICATORS (a missing name -> value/threshold/triggered None, note "not available").
    points = number of indicators with triggered is True. state = classify(points).
    history: Series indexed by date (Timestamp) with integer points; becomes
    [{"date": ISO date, "points", "state"}] in date order.
    """
    raise NotImplementedError


def drawdown_lift(points: pd.Series, benchmark: pd.Series, regime_cfg: dict, horizon: int = 20,
                  threshold: float = 0.07) -> dict:
    """How much more often a large drawdown follows elevated/stressed days than any day.

    For each date t with a full forward window (t+1..t+horizon rows of benchmark):
      event(t) = min(P[t+1..t+horizon]) / P[t] - 1 <= -threshold.
    base = mean(event) over those dates. For state s in {elevated, stressed}:
      lift_s = mean(event | classify(points[t]) == s) / base, or None when base == 0 or there
      are no such days. Dates are aligned on the intersection of both indexes.
    Returns {"drawdown_threshold": threshold, "horizon_days": horizon, "lift_elevated",
    "lift_stressed", "n_days"} (n_days = number of dates with a full window).
    """
    raise NotImplementedError
