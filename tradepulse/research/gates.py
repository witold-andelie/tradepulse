"""Gates G1-G5, factor weights and factor cards. Spec: docs/architecture/factors.md (Gates)."""

from __future__ import annotations

from dataclasses import dataclass, field

GATE_NAMES = ("measure", "incremental", "predictive", "net_of_cost", "consistency")
MIN_VALID_DATES = 40


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
    raise NotImplementedError


def mostly_descriptive(same_day_ic: float | None, primary_ic: float | None) -> bool:
    """True when both are known and abs(same_day_ic) > 3 * abs(primary_ic)."""
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError
