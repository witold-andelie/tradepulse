"""SD1.5 · Assessing Regime (fragility monitor). Spec: docs/architecture/factors.md (Regime)."""

from __future__ import annotations

from math import isfinite

import pandas as pd

INDICATORS = ("trend", "volatility", "correlation", "breadth", "credit")


def _optional_float(value: float | None) -> float | None:
    """Convert missing or non-finite metrics to JSON null."""
    return None if value is None or not isfinite(value) else float(value)


def classify(points: int, regime_cfg: dict) -> str:
    """'normal' if points < elevated_min_points, 'elevated' if < stressed_min_points, else 'stressed'."""
    if points < regime_cfg["elevated_min_points"]:
        return "normal"
    if points < regime_cfg["stressed_min_points"]:
        return "elevated"
    return "stressed"


def regime_state(pool: str, as_of: str, indicators: dict[str, dict], history: pd.Series,
                 lift: dict | None, regime_cfg: dict) -> dict:
    """Contract-valid RegimeState.

    indicators: name -> {"value", "threshold", "triggered" (bool or None), "note"} for every name
    in INDICATORS (a missing name -> value/threshold/triggered None, note "not available").
    points = number of indicators with triggered is True. state = classify(points).
    history: Series indexed by date (Timestamp) with integer points; becomes
    [{"date": ISO date, "points", "state"}] in date order.
    """
    results = []
    for name in INDICATORS:
        indicator = indicators.get(name, {})
        triggered = indicator.get("triggered")
        results.append({"name": name, "value": _optional_float(indicator.get("value")),
                        "threshold": _optional_float(indicator.get("threshold")),
                        "triggered": None if triggered is None else bool(triggered),
                        "note": str(indicator.get("note", "not available"))})
    points = sum(indicator["triggered"] is True for indicator in results)
    cutoff = pd.Timestamp(as_of).date()
    past = [{"date": date.date().isoformat(), "points": int(value),
             "state": classify(int(value), regime_cfg)}
            for date, value in history.sort_index().items() if date.date() <= cutoff]
    lift_result = None if lift is None else {
        "drawdown_threshold": float(lift["drawdown_threshold"]),
        "horizon_days": int(lift["horizon_days"]),
        "lift_elevated": _optional_float(lift["lift_elevated"]),
        "lift_stressed": _optional_float(lift["lift_stressed"]), "n_days": int(lift["n_days"]),
    }
    return {"pool": str(pool), "as_of": str(as_of), "points": points,
            "state": classify(points, regime_cfg), "indicators": results,
            "history": past, "lift": lift_result}


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
    if horizon < 1:
        raise ValueError("horizon must be positive")
    prices = benchmark.sort_index()
    # Compute windows on benchmark rows before aligning the observation dates.
    forward_min = prices.iloc[::-1].rolling(horizon, min_periods=horizon).min().iloc[::-1].shift(-1)
    dates = prices.index.intersection(points.index).sort_values()
    valid = (prices.reindex(dates).notna() & forward_min.reindex(dates).notna()
             & points.reindex(dates).notna())
    dates = dates[valid]
    events = (forward_min.loc[dates] / prices.loc[dates] - 1) <= -threshold
    states = points.loc[dates].map(lambda value: classify(int(value), regime_cfg))
    base = float(events.mean()) if len(events) else 0.0
    lifts = {}
    for state in ("elevated", "stressed"):
        selected = events.loc[states == state]
        lifts[state] = float(selected.mean() / base) if base > 0 and len(selected) else None
    return {"drawdown_threshold": float(threshold), "horizon_days": int(horizon),
            "lift_elevated": lifts["elevated"], "lift_stressed": lifts["stressed"],
            "n_days": int(len(events))}
