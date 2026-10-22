import math

import numpy as np
import pandas as pd
import pytest

from quant import evaluation as ev


def _panel(values, n_dates=1):
    idx = pd.bdate_range("2025-01-01", periods=n_dates)
    return pd.DataFrame(values, index=idx)


def test_forward_returns_with_execution_lag():
    p = pd.DataFrame({"A": np.arange(1.0, 11.0)}, index=pd.bdate_range("2025-01-01", periods=10))
    fwd = ev.forward_returns(p, horizon=2, lag=1)["A"]
    assert fwd.iloc[0] == pytest.approx(4 / 2 - 1)
    assert fwd.iloc[-3:].isna().all()
    assert fwd.iloc[:-3].notna().all()


def test_rank_ic_perfect_and_inverse():
    cols = [f"S{i}" for i in range(25)]
    f = _panel([list(range(25))], 1)
    f.columns = cols
    t = f * 2.0 + 1.0
    assert ev.rank_ic(f, t, min_names=20).iloc[0] == pytest.approx(1.0)
    assert ev.rank_ic(f, -t, min_names=20).iloc[0] == pytest.approx(-1.0)


def test_rank_ic_is_rank_based():
    cols = [f"S{i}" for i in range(25)]
    f = _panel([list(range(25))], 1)
    f.columns = cols
    t = np.exp(f)  # monotone, non-linear
    assert ev.rank_ic(f, t, min_names=20).iloc[0] == pytest.approx(1.0)


def test_rank_ic_too_few_names_is_nan():
    f = _panel([[1.0, 2.0, 3.0]], 1)
    assert np.isnan(ev.rank_ic(f, f, min_names=20).iloc[0])


def test_ic_summary_overlapping_and_not():
    ic = pd.Series([0.1, 0.2, 0.3, 0.4])
    s1 = ev.ic_summary(ic, horizon=1)
    assert s1["mean"] == pytest.approx(0.25)
    assert s1["std"] == pytest.approx(np.std([0.1, 0.2, 0.3, 0.4], ddof=1))
    assert s1["t_stat"] == pytest.approx(0.25 / (s1["std"] / 2))
    assert s1["n"] == 4
    s2 = ev.ic_summary(ic, horizon=2)
    assert s2["n"] == 2
    assert s2["mean"] == pytest.approx(0.2)
    assert s2["t_stat"] == pytest.approx(2.0)


def test_ic_summary_degenerate():
    s = ev.ic_summary(pd.Series([0.1, np.nan]), horizon=1)
    assert s["n"] == 1 and math.isnan(s["t_stat"])


def _drifting_prices(n_names=10, n_dates=60, step=0.001):
    idx = pd.bdate_range("2025-01-01", periods=n_dates)
    data = {f"S{i}": 100 * (1 + step * i) ** np.arange(n_dates) for i in range(n_names)}
    return pd.DataFrame(data, index=idx)


def test_ic_decay_shape(random_prices):
    f = random_prices.pct_change(5)
    out = ev.ic_decay(f, random_prices, horizons=(1, 5, 20), min_names=5)
    assert list(out.index) == [1, 5, 20]
    assert {"mean_ic", "t_stat", "n"} <= set(out.columns)


def test_same_day_ic_detects_description():
    p = _drifting_prices()
    r = p.pct_change()
    ic = ev.same_day_ic(r, p, min_names=5)
    assert ic.dropna().to_numpy() == pytest.approx(1.0)


def test_quantile_long_short_values():
    p = _drifting_prices()
    factor = pd.DataFrame(np.tile(np.arange(10.0), (len(p), 1)), index=p.index, columns=p.columns)
    out = ev.quantile_long_short(factor, p, horizon=5, lag=1, quantile=0.2, cost_bps_one_way=10.0)
    fwd = lambda i: (1 + 0.001 * i) ** 5 - 1  # noqa: E731
    gross = (fwd(8) + fwd(9)) / 2 - (fwd(0) + fwd(1)) / 2
    assert out["gross"].iloc[0] == pytest.approx(gross)
    assert out["turnover"].iloc[0] == pytest.approx(2.0)
    assert out["turnover"].iloc[1] == pytest.approx(0.0)
    assert out["net"].iloc[0] == pytest.approx(gross - 2.0 * 10.0 / 1e4)
    assert out["net"].iloc[1] == pytest.approx(gross)
    assert out["max_drawdown"] == pytest.approx(0.0)
    assert out["ann_return_gross"] == pytest.approx(out["gross"].mean() * 252 / 5)


def test_half_split_sign_agreement():
    assert ev.half_split_sign_agreement(pd.Series([0.1, 0.2, -0.1, 0.3])) is True
    assert ev.half_split_sign_agreement(pd.Series([0.1, 0.2, -0.3, -0.1])) is False
    assert ev.half_split_sign_agreement(pd.Series([0.1, 0.2, 0.3])) is False


def test_lead_lag_tstat():
    rng = np.random.default_rng(11)
    idx = pd.bdate_range("2025-01-01", periods=250)
    leader = pd.Series(rng.normal(size=250), index=idx)
    follower = leader.shift(1) + pd.Series(rng.normal(scale=0.3, size=250), index=idx)
    out = ev.lead_lag_tstat(leader, follower, lag=1)
    assert out["r"] > 0.9 and out["t_stat"] > 20 and out["n"] == 249
    unrelated = pd.Series(rng.normal(size=250), index=idx)
    assert abs(ev.lead_lag_tstat(unrelated, follower, lag=1)["t_stat"]) < 3.5
