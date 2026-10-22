import math

import numpy as np
import pandas as pd
import pytest

from quant import costs, settlement


def test_round_trip_and_cost_return():
    assert costs.round_trip_bps(5.0) == 10.0
    assert costs.cost_return(2.0, 10.0) == pytest.approx(0.002)


def test_turnover_union_of_names():
    old = pd.Series({"A": 0.5, "B": 0.5})
    new = pd.Series({"B": 0.5, "C": 0.5})
    assert costs.turnover(old, new) == pytest.approx(1.0)


def test_expected_alpha_and_net_edge():
    alpha = costs.expected_alpha_bps(0.05, 0.02, 4, 1.5)
    assert alpha == pytest.approx(0.05 * 0.02 * 2 * 1.5 * 1e4)  # 30 bp
    assert costs.net_edge_bps(30.0, 5.0) == pytest.approx(20.0)
    assert costs.net_edge_bps(-30.0, 5.0) == pytest.approx(-20.0)
    s = costs.net_edge_bps(pd.Series([30.0, np.nan]), 5.0)
    assert s.iloc[0] == pytest.approx(20.0) and np.isnan(s.iloc[1])


def test_excess_return_and_hit():
    ex = settlement.excess_return(100, 110, 50, 51)
    assert ex == pytest.approx(0.10 - 0.02)
    assert settlement.hit("OVERWEIGHT", ex) is True
    assert settlement.hit("STRONG_OVERWEIGHT", -0.01) is False
    assert settlement.hit("AVOID", -0.01) is True
    assert settlement.hit("NEUTRAL", 0.5) is None
    assert settlement.hit("NO_CALL", 0.5) is None


def test_brier_score():
    assert settlement.brier_score(pd.Series([1.0, 0.0, 0.5]), pd.Series([1, 1, 0])) == pytest.approx(
        (0 + 1 + 0.25) / 3)


def test_calibration_table():
    probs = pd.Series([0.05, 0.15, 0.95, 1.0, 0.9])
    outs = pd.Series([0, 0, 1, 1, 0])
    tab = settlement.calibration_table(probs, outs, n_buckets=5)
    assert len(tab) == 5
    assert list(tab["n"]) == [2, 0, 0, 0, 3]
    assert tab["predicted"].iloc[4] == pytest.approx((0.95 + 1.0 + 0.9) / 3)
    assert tab["observed"].iloc[4] == pytest.approx(2 / 3)
    assert math.isnan(tab["predicted"].iloc[1])
    assert tab["bucket_low"].iloc[1] == pytest.approx(0.2)
