"""Gates G1-G5, factor weights and factor cards. Spec: docs/architecture/factors.md (Gates)."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

GATE_NAMES = ("measure", "incremental", "predictive", "net_of_cost", "consistency")
MIN_VALID_DATES = 40


def _optional_float(value: float | None) -> float | None:
    """Convert missing or non-finite metrics to JSON null."""
    return None if value is None or not isfinite(value) else float(value)


@dataclass(frozen=True)
class FactorMetrics:
    """Evaluation results of one factor in one pool (computed with quant.evaluation)."""

    factor: str
    pool: str
    coverage: float                 # non-null share of pool-days
    n_dates: int                    # dates with a valid cross-sectional IC
    spec_complete: bool             # the factor has a complete row in factors.md
    ic_by_horizon: dict = field(default_factory=dict)
    # {horizon: {"mean": float|None, "t_stat": float|None, "ir": float|None, "n": int}}
    # residualised factor, IC with execution lag
    same_day_ic: float | None = None
    long_short: dict = field(default_factory=dict)
    # keys: gross_ann_return, net_ann_return, net_sharpe, turnover_per_rebalance, max_drawdown
    half_split_agree: bool | None = None


def evaluate_gates(m: FactorMetrics, gates_cfg: dict, primary_horizon: int) -> tuple[list[dict], str]:
    """Return (five GateResult dicts in order G1..G5, status).

    G1 measure: value = coverage, threshold = min_coverage,
       passed = spec_complete and coverage >= min_coverage.
    If G1 fails or n_dates < MIN_VALID_DATES: status "INSUFFICIENT_DATA" and G2..G5 have
       passed=None, value=None, note="not evaluated" (threshold still filled where it exists).
    G2 incremental: value = the largest non-null t_stat across horizons (None if none),
       threshold = min_incremental_ic_t, passed = value is not None and value >= threshold.
    G3 predictive: value = mean IC at primary_horizon, threshold = 0.0,
       passed = value is not None and value > 0.
    G4 net_of_cost: value = long_short["net_sharpe"], threshold = min_net_sharpe,
       passed = value is not None and value >= threshold.
    G5 consistency: value = None, threshold = None,
       passed = (half_split_agree is True) if require_half_split_sign_agreement else True.
    status = "ACTIVE" if G2..G5 all passed else "MEASURED_ONLY".
    Every gate has a short human note (e.g. "coverage 0.82 >= 0.60"); evaluated gates never use
    the note "not evaluated".
    """
    thresholds = [float(gates_cfg["min_coverage"]), float(gates_cfg["min_incremental_ic_t"]),
                  0.0, float(gates_cfg["min_net_sharpe"]), None]
    gates = [{"gate": f"G{i}", "name": name, "passed": None, "value": None,
              "threshold": threshold, "note": "not evaluated"}
             for i, (name, threshold) in enumerate(zip(GATE_NAMES, thresholds), start=1)]
    coverage = _optional_float(m.coverage)
    measure_passed = bool(m.spec_complete and coverage is not None and coverage >= thresholds[0])
    gates[0].update(passed=measure_passed, value=coverage,
                    note=f"coverage {coverage}; minimum {thresholds[0]}; "
                         f"specification {'complete' if m.spec_complete else 'incomplete'}")
    if not measure_passed or m.n_dates < MIN_VALID_DATES:
        return gates, "INSUFFICIENT_DATA"

    t_stats = [_optional_float(metrics.get("t_stat")) for metrics in m.ic_by_horizon.values()]
    best_t = max((value for value in t_stats if value is not None), default=None)
    primary_ic = _optional_float(m.ic_by_horizon.get(primary_horizon, {}).get("mean"))
    net_sharpe = _optional_float(m.long_short.get("net_sharpe"))
    require_agreement = gates_cfg["require_half_split_sign_agreement"]
    agrees = m.half_split_agree is not None and bool(m.half_split_agree)
    values = [best_t, primary_ic, net_sharpe, None]
    passed = [best_t is not None and best_t >= thresholds[1],
              primary_ic is not None and primary_ic > thresholds[2],
              net_sharpe is not None and net_sharpe >= thresholds[3],
              agrees if require_agreement else True]
    notes = [f"best residual IC t-stat {best_t}; minimum {thresholds[1]}",
             f"primary IC {primary_ic}; must be positive",
             f"net Sharpe {net_sharpe}; minimum {thresholds[3]}",
             (f"half-window signs {'agree' if agrees else 'do not agree or are unavailable'}"
              if require_agreement else "half-window sign agreement not required")]
    for gate, value, result, note in zip(gates[1:], values, passed, notes):
        gate.update(value=value, passed=bool(result), note=note)
    return gates, "ACTIVE" if all(passed) else "MEASURED_ONLY"


def mostly_descriptive(same_day_ic: float | None, primary_ic: float | None) -> bool:
    """True when both are known and abs(same_day_ic) > 3 * abs(primary_ic)."""
    same_day_ic = _optional_float(same_day_ic)
    primary_ic = _optional_float(primary_ic)
    return bool(same_day_ic is not None and primary_ic is not None
                and abs(same_day_ic) > 3 * abs(primary_ic))


def compute_weights(cards: list[dict], shrinkage: float) -> dict[str, float]:
    """Weights for the cards of ONE pool.

    Each card dict has "factor", "status" and "ir" (IC-IR at the primary horizon, may be None).
    - Only ACTIVE cards get weight; every other factor gets 0.0 (and still appears in the result).
    - raw_f = max(0, ir_f) (None counts as 0). If the raw values of active factors sum to > 0,
      normalise them to sum 1; otherwise use equal weights over active factors.
    - final = (1 - shrinkage) * normalised + shrinkage * (1 / n_active).
    - With no active factor every weight is 0.0.
    Returned weights of active factors sum to 1 (within 1e-9).
    """
    weights = {str(card["factor"]): 0.0 for card in cards}
    active = [card for card in cards if card["status"] == "ACTIVE"]
    if not active:
        return weights
    raw = [max(0.0, _optional_float(card.get("ir")) or 0.0) for card in active]
    total = sum(raw)
    equal = 1.0 / len(active)
    for card, value in zip(active, raw):
        normalised = value / total if total > 0 else equal
        weights[str(card["factor"])] = float((1 - shrinkage) * normalised + shrinkage * equal)
    return weights


def build_card(m: FactorMetrics, spec: dict, gates: list[dict], status: str, weight: float,
               window: dict, primary_horizon: int) -> dict:
    """Assemble a contract-valid FactorCard.

    spec keys: title, measures, definition, sources (list), availability.
    ic_decay = [{"horizon_days", "mean_ic", "t_stat", "n"}] sorted by horizon from ic_by_horizon.
    same_day_ic from m; mostly_descriptive(m.same_day_ic, mean IC at primary_horizon).
    long_short: the five keys from m.long_short, missing keys -> None.
    evaluation_mode = "in_sample_research"; window = {"start", "end"} ISO dates.
    coverage and weight are rounded to 6 decimals.
    """
    return {
        "factor": str(m.factor), "pool": str(m.pool),
        "title": str(spec["title"]), "measures": str(spec["measures"]),
        "definition": str(spec["definition"]), "sources": [str(source) for source in spec["sources"]],
        "availability": str(spec["availability"]), "status": str(status),
        "weight": round(float(weight), 6), "coverage": round(float(m.coverage), 6),
        "gates": [{"gate": str(gate["gate"]), "name": str(gate["name"]),
                   "passed": None if gate["passed"] is None else bool(gate["passed"]),
                   "value": _optional_float(gate["value"]),
                   "threshold": _optional_float(gate["threshold"]), "note": str(gate["note"])}
                  for gate in gates],
        "ic_decay": [{"horizon_days": int(horizon), "mean_ic": _optional_float(metrics.get("mean")),
                      "t_stat": _optional_float(metrics.get("t_stat")), "n": int(metrics["n"])}
                     for horizon, metrics in sorted(m.ic_by_horizon.items())],
        "same_day_ic": _optional_float(m.same_day_ic),
        "mostly_descriptive": mostly_descriptive(
            m.same_day_ic, m.ic_by_horizon.get(primary_horizon, {}).get("mean")),
        "long_short": {key: _optional_float(m.long_short.get(key))
                       for key in ("gross_ann_return", "net_ann_return", "net_sharpe",
                                   "turnover_per_rebalance", "max_drawdown")},
        "evaluation_mode": "in_sample_research",
        "window": {key: str(window[key]) for key in ("start", "end")},
    }
