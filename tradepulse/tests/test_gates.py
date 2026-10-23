import pytest

from tradepulse.config import load_config
from tradepulse.contracts import validate_payload
from tradepulse.research.gates import FactorMetrics, build_card, compute_weights, evaluate_gates, mostly_descriptive

CFG = load_config()["gates"]
LS = {"gross_ann_return": 0.12, "net_ann_return": 0.08, "net_sharpe": 0.8, "turnover_per_rebalance": 0.6,
      "max_drawdown": -0.05}
IC = {1: {"mean": 0.01, "t_stat": 1.5, "ir": 0.10, "n": 200},
      5: {"mean": 0.02, "t_stat": 2.5, "ir": 0.18, "n": 40},
      20: {"mean": 0.015, "t_stat": None, "ir": None, "n": 10}}


def _m(**kw):
    base = dict(factor="pv_mom_1m", pool="us_equity", coverage=0.8, n_dates=200, spec_complete=True,
                ic_by_horizon=IC, same_day_ic=0.03, long_short=LS, half_split_agree=True)
    base.update(kw)
    return FactorMetrics(**base)


def test_active_factor():
    gates, status = evaluate_gates(_m(), CFG, 5)
    assert status == "ACTIVE"
    assert [g["gate"] for g in gates] == ["G1", "G2", "G3", "G4", "G5"]
    assert [g["name"] for g in gates] == ["measure", "incremental", "predictive", "net_of_cost", "consistency"]
    assert all(g["passed"] is True for g in gates)
    assert gates[0]["value"] == 0.8 and gates[0]["threshold"] == CFG["min_coverage"]
    assert gates[1]["value"] == 2.5 and gates[1]["threshold"] == CFG["min_incremental_ic_t"]
    assert gates[2]["value"] == 0.02 and gates[2]["threshold"] == 0.0
    assert gates[3]["value"] == 0.8
    assert all(g["note"] and g["note"] != "not evaluated" for g in gates)
    for g in gates:
        assert validate_payload(g, "GateResult") == []


@pytest.mark.parametrize("kw, failing", [
    (dict(long_short=dict(LS, net_sharpe=0.3)), "G4"),
    (dict(long_short=dict(LS, net_sharpe=None)), "G4"),
    (dict(half_split_agree=None), "G5"),
    (dict(half_split_agree=False), "G5"),
    (dict(ic_by_horizon={5: {"mean": -0.01, "t_stat": 2.2, "ir": -0.1, "n": 40}}), "G3"),
    (dict(ic_by_horizon={5: {"mean": 0.01, "t_stat": 1.9, "ir": 0.1, "n": 40}}), "G2"),
])
def test_measured_only(kw, failing):
    gates, status = evaluate_gates(_m(**kw), CFG, 5)
    assert status == "MEASURED_ONLY"
    assert {g["gate"]: g["passed"] for g in gates}[failing] is False


@pytest.mark.parametrize("kw, g1", [
    (dict(coverage=0.5), False),
    (dict(spec_complete=False), False),
    (dict(n_dates=30), True),
])
def test_insufficient_data(kw, g1):
    gates, status = evaluate_gates(_m(**kw), CFG, 5)
    assert status == "INSUFFICIENT_DATA"
    assert gates[0]["passed"] is g1
    for g in gates[1:]:
        assert g["passed"] is None and g["value"] is None and g["note"] == "not evaluated"


def test_mostly_descriptive():
    assert mostly_descriptive(0.10, 0.02) is True
    assert mostly_descriptive(0.05, 0.02) is False
    assert mostly_descriptive(None, 0.02) is False
    assert mostly_descriptive(0.10, None) is False


def test_compute_weights():
    cards = [{"factor": "a", "status": "ACTIVE", "ir": 0.3}, {"factor": "b", "status": "ACTIVE", "ir": 0.1},
             {"factor": "c", "status": "MEASURED_ONLY", "ir": 0.9}, {"factor": "d", "status": "ACTIVE", "ir": -0.2}]
    w = compute_weights(cards, 0.5)
    assert w["a"] == pytest.approx(0.5 * 0.75 + 0.5 / 3)
    assert w["b"] == pytest.approx(0.5 * 0.25 + 0.5 / 3)
    assert w["d"] == pytest.approx(0.5 / 3)
    assert w["c"] == 0.0
    assert sum(w.values()) == pytest.approx(1.0)


def test_compute_weights_degenerate():
    w = compute_weights([{"factor": "a", "status": "ACTIVE", "ir": -1.0}, {"factor": "b", "status": "ACTIVE", "ir": None}], 0.5)
    assert w == pytest.approx({"a": 0.5, "b": 0.5})
    assert compute_weights([{"factor": "a", "status": "INSUFFICIENT_DATA", "ir": 0.5}], 0.5) == {"a": 0.0}


def test_build_card_is_contract_valid():
    m = _m(same_day_ic=0.09)
    gates, status = evaluate_gates(m, CFG, 5)
    spec = {"title": "1-month momentum", "measures": "1-month trend", "definition": "P[t]/P[t-21]-1",
            "sources": ["price_bar"], "availability": "close t"}
    card = build_card(m, spec, gates, status, 0.1234567891, {"start": "2025-10-21", "end": "2026-10-21"}, 5)
    assert validate_payload(card, "FactorCard") == []
    assert [d["horizon_days"] for d in card["ic_decay"]] == [1, 5, 20]
    assert card["mostly_descriptive"] is True  # 0.09 > 3 * 0.02
    assert card["weight"] == 0.123457
    assert card["evaluation_mode"] == "in_sample_research"
    assert card["long_short"]["net_sharpe"] == 0.8
