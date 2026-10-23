import math

import numpy as np
import pandas as pd
import pytest

from tradepulse.config import load_config
from tradepulse.ranking import apply_regime, assign_tiers, composite, expected_alpha_bps, select_focus

TIERS_CFG = load_config()["tiers"]


def test_composite():
    z = {"a": pd.Series({"X": 1.0, "Y": -1.0, "Z": np.nan}), "b": pd.Series({"X": 0.5, "Y": np.nan, "W": 2.0})}
    out = composite(z, {"a": 0.6, "b": 0.4, "c": 0.0})
    assert list(out.index) == ["W", "X", "Y", "Z"]
    assert out.loc["X", "score"] == pytest.approx(0.8) and out.loc["X", "coverage"] == pytest.approx(1.0)
    assert out.loc["Y", "score"] == pytest.approx(-0.6) and out.loc["Y", "coverage"] == pytest.approx(0.6)
    assert out.loc["Z", "score"] == pytest.approx(0.0) and out.loc["Z", "coverage"] == pytest.approx(0.0)
    assert out.loc["W", "score"] == pytest.approx(0.8) and out.loc["W", "coverage"] == pytest.approx(0.4)
    contrib = out.loc["Y", "contributions"]
    assert [c["factor"] for c in contrib] == ["a", "b"]
    assert contrib[1] == {"factor": "b", "z": None, "weight": 0.4, "contribution": 0.0}
    assert sum(c["contribution"] for c in out.loc["X", "contributions"]) == pytest.approx(out.loc["X", "score"])


def test_expected_alpha():
    s = expected_alpha_bps(0.05, pd.Series({"A": 0.02}), 4, pd.Series({"A": 1.5}))
    assert s["A"] == pytest.approx(30.0)


def _book():
    scores = [3.0, 1.2, 1.1, 0.6, 0.55] + list(np.linspace(0.5, -0.5, 11)) + [-1.2, -1.3, -1.4, -2.0]
    idx = [f"S{i:02d}" for i in range(20)]
    df = pd.DataFrame({"score": scores, "coverage": 1.0, "sigma_daily": 0.02}, index=idx)
    df.loc["S10", "coverage"] = 0.4
    return df


def _tiers(**kw):
    args = dict(ic_comp=0.05, cost_bps_one_way=5.0, horizon=4, tiers_cfg=TIERS_CFG)
    args.update(kw)
    return assign_tiers(_book(), **args)


def test_assign_tiers():
    out = _tiers()
    assert list(out.index[:3]) == ["S00", "S01", "S02"]
    assert out.loc["S00", "rank"] == 1 and out.loc["S19", "rank"] == 20
    assert out.loc["S01", "percentile"] == pytest.approx(0.95)
    assert out.loc["S00", "expected_alpha_bps"] == pytest.approx(60.0)
    assert out.loc["S00", "net_edge_bps"] == pytest.approx(50.0)
    assert out.loc["S19", "net_edge_bps"] == pytest.approx(-30.0)
    assert (out["cost_bps_round_trip"] == 10.0).all()
    expected = {"S00": "STRONG_OVERWEIGHT", "S01": "OVERWEIGHT", "S02": "OVERWEIGHT", "S03": "NEUTRAL",
                "S04": "NEUTRAL", "S10": "NO_CALL", "S16": "UNDERWEIGHT", "S17": "UNDERWEIGHT",
                "S18": "UNDERWEIGHT", "S19": "AVOID"}
    for sym, tier in expected.items():
        assert out.loc[sym, "tier"] == tier, sym
    assert out.loc["S10", "expected_alpha_bps"] is None or math.isnan(out.loc["S10", "expected_alpha_bps"])


def test_valuation_block():
    out = _tiers(valuation_pctile=pd.Series({"S00": 0.95, "S01": 0.99}))
    assert out.loc["S00", "tier"] == "OVERWEIGHT"
    assert out.loc["S01", "tier"] == "OVERWEIGHT"


@pytest.mark.parametrize("ic", [None, 0.0, -0.01])
def test_no_composite_skill_means_no_call(ic):
    out = _tiers(ic_comp=ic)
    assert (out["tier"] == "NO_CALL").all()
    assert out["net_edge_bps"].isna().all() or all(v is None for v in out["net_edge_bps"])


def test_rank_ties_by_symbol():
    df = pd.DataFrame({"score": [1.0, 1.0, 0.0], "coverage": 1.0, "sigma_daily": 0.01}, index=["B", "A", "C"])
    out = assign_tiers(df, ic_comp=0.05, cost_bps_one_way=5.0, horizon=5, tiers_cfg=TIERS_CFG)
    assert list(out.index) == ["A", "B", "C"] and list(out["rank"]) == [1, 2, 3]


def test_input_not_modified():
    df = _book()
    before = df.copy()
    assign_tiers(df, ic_comp=0.05, cost_bps_one_way=5.0, horizon=4, tiers_cfg=TIERS_CFG)
    pd.testing.assert_frame_equal(df, before)


def test_apply_regime():
    tiers = ["STRONG_OVERWEIGHT", "OVERWEIGHT", "NEUTRAL", "UNDERWEIGHT", "AVOID", "NO_CALL"]
    df = pd.DataFrame({"tier": tiers}, index=list("ABCDEF"))
    el = apply_regime(df, "elevated")
    assert list(el["tier"]) == ["OVERWEIGHT", "OVERWEIGHT", "NEUTRAL", "UNDERWEIGHT", "AVOID", "NO_CALL"]
    assert list(el["regime_adjusted"]) == [True, False, False, False, False, False]
    st = apply_regime(df, "stressed")
    assert list(st["tier"]) == ["OVERWEIGHT", "NEUTRAL", "NEUTRAL", "UNDERWEIGHT", "AVOID", "NO_CALL"]
    assert list(st["regime_adjusted"]) == [True, True, False, False, False, False]
    assert list(apply_regime(df, "normal")["tier"]) == tiers
    assert list(df["tier"]) == tiers
    with pytest.raises(ValueError):
        apply_regime(df, "panic")


def test_select_focus():
    out = _tiers()
    ret = pd.Series({"S05": 0.09, "S10": -0.12, "S00": 0.20})
    focus = select_focus(out, top_k=2, movers_k=2, ret_1d=ret, requested=["NVDA", "S07"])
    assert focus == ["S00", "S01", "S19", "S18", "S10", "S07"]
