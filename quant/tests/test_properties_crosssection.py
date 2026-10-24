"""C9 property tests for cross-sectional transforms and factor evaluation."""

import numpy as np
import pandas as pd
import pytest

from quant import crosssection as cs
from quant import evaluation as ev
from quant import indicators as ind

SEEDS = range(5)


def _panel(seed, n_dates=40, n_names=30, nan_share=0.1):
    rng = np.random.default_rng(seed)
    values = rng.standard_t(df=4, size=(n_dates, n_names))
    values[rng.random(values.shape) < nan_share] = np.nan
    idx = pd.bdate_range("2025-01-01", periods=n_dates)
    return pd.DataFrame(values, index=idx, columns=[f"S{i}" for i in range(n_names)])


def _prices(seed, n_dates=120, n_names=30):
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0, 0.02, size=(n_dates, n_names))
    idx = pd.bdate_range("2025-01-01", periods=n_dates)
    return pd.DataFrame(100 * np.cumprod(1 + rets, axis=0), index=idx,
                        columns=[f"S{i}" for i in range(n_names)])


# --- cross-sectional transforms -------------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_zscore_rows_have_mean_zero_and_std_one(seed):
    out = cs.zscore_cs(_panel(seed))
    assert np.allclose(out.mean(axis=1), 0.0, atol=1e-12)
    assert np.allclose(out.std(axis=1, ddof=1), 1.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_zscore_ignores_positive_affine_changes(seed):
    df = _panel(seed)
    pd.testing.assert_frame_equal(cs.zscore_cs(3.0 * df - 7.0), cs.zscore_cs(df), atol=1e-12)


@pytest.mark.parametrize("seed", SEEDS)
def test_rank_pct_range_and_monotone_invariance(seed):
    df = _panel(seed)
    ranks = cs.rank_pct_cs(df)
    values = ranks.to_numpy()[~np.isnan(ranks.to_numpy())]
    assert ((values > 0) & (values <= 1)).all()
    assert np.allclose(ranks.max(axis=1), 1.0)
    pd.testing.assert_frame_equal(cs.rank_pct_cs(np.exp(df)), ranks)
    pd.testing.assert_frame_equal(ranks.isna(), df.isna())


@pytest.mark.parametrize("seed", SEEDS)
def test_winsorize_stays_in_band_and_keeps_order(seed):
    df = _panel(seed)
    out = cs.winsorize_cs(df, n_sigma=2.0)
    mean, std = df.mean(axis=1), df.std(axis=1, ddof=1)
    tol = 1e-12
    present = df.notna().to_numpy()
    assert (out.sub(mean - 2.0 * std, axis=0).to_numpy()[present] >= -tol).all()
    assert (out.sub(mean + 2.0 * std, axis=0).to_numpy()[present] <= tol).all()
    pd.testing.assert_frame_equal(out.isna(), df.isna())
    # Clipping is monotone: a larger input never maps to a strictly smaller output.
    for t in df.index:
        row = pd.DataFrame({"x": df.loc[t], "y": out.loc[t]}).dropna().sort_values("x")
        assert row["y"].is_monotonic_increasing


@pytest.mark.parametrize("seed", SEEDS)
def test_neutralize_groups_zero_group_means_and_idempotent(seed):
    df = _panel(seed)
    labels = pd.Series({c: f"g{i % 4}" for i, c in enumerate(df.columns[:-3])})  # last 3 ungrouped
    out = cs.neutralize_groups(df, labels)
    full_labels = labels.reindex(df.columns).fillna("__none__")
    group_means = out.T.groupby(full_labels.to_numpy()).mean().T
    assert np.allclose(group_means.to_numpy()[np.isfinite(group_means.to_numpy())], 0.0, atol=1e-12)
    pd.testing.assert_frame_equal(cs.neutralize_groups(out, labels), out, atol=1e-12)


@pytest.mark.parametrize("seed", SEEDS)
def test_residuals_are_orthogonal_and_ignore_the_explained_part(seed):
    rng = np.random.default_rng(seed)
    y = _panel(seed)
    x1 = pd.DataFrame(rng.normal(size=y.shape), index=y.index, columns=y.columns)
    x2 = pd.DataFrame(rng.normal(size=y.shape), index=y.index, columns=y.columns)
    res = cs.residualize_cs(y, {"a": x1, "b": x2})
    for t in y.index:
        r = res.loc[t].dropna()
        assert abs(r.sum()) < 1e-9
        assert abs((r * x1.loc[t, r.index]).sum()) < 1e-9
        assert abs((r * x2.loc[t, r.index]).sum()) < 1e-9
    # Adding any linear combination of the regressors (plus a constant) leaves residuals unchanged.
    shifted = y + 2.0 * x1 - 0.5 * x2 + 4.0
    pd.testing.assert_frame_equal(cs.residualize_cs(shifted, {"a": x1, "b": x2}), res, atol=1e-9)


GROUPS = pd.Series({f"S{i}": f"g{i % 3}" for i in range(30)})  # fixed per symbol, not position

ROW_WISE = {
    "winsorize_cs": lambda d: cs.winsorize_cs(d),
    "zscore_cs": lambda d: cs.zscore_cs(d),
    "rank_pct_cs": lambda d: cs.rank_pct_cs(d),
    "neutralize_groups": lambda d: cs.neutralize_groups(d, GROUPS),
}


@pytest.mark.parametrize("name", list(ROW_WISE))
def test_rows_are_independent_and_columns_permutable(name):
    """No information crosses dates, and symbol order does not matter."""
    fn = ROW_WISE[name]
    df = _panel(11)
    before = df.copy()
    full = fn(df)
    pd.testing.assert_frame_equal(df, before)  # input not mutated
    pd.testing.assert_frame_equal(fn(df.iloc[[5, 17]]), full.iloc[[5, 17]])
    perm = list(np.random.default_rng(2).permutation(df.columns))
    pd.testing.assert_frame_equal(fn(df[perm])[df.columns], full, atol=1e-12)


# --- factor evaluation ----------------------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_rank_ic_bounds_symmetry_and_invariance(seed):
    factor, target = _panel(seed), _panel(seed + 100)
    ic = ev.rank_ic(factor, target, min_names=10)
    finite = ic.dropna()
    assert len(finite) > 0 and ((finite >= -1) & (finite <= 1)).all()
    pd.testing.assert_series_equal(ev.rank_ic(target, factor, min_names=10), ic)
    pd.testing.assert_series_equal(ev.rank_ic(factor, -target, min_names=10), -ic)
    pd.testing.assert_series_equal(ev.rank_ic(factor ** 3, target, min_names=10), ic)
    assert np.allclose(ev.rank_ic(factor, factor, min_names=10).dropna(), 1.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_forward_returns_line_up_with_later_simple_returns(seed):
    prices = _prices(seed)
    fwd = ev.forward_returns(prices, horizon=1, lag=0)
    r = ind.simple_returns(prices)
    # fwd(h=1, lag=0) at row t is the simple return realised at row t+1.
    assert np.allclose(fwd.iloc[:-1].to_numpy(), r.iloc[1:].to_numpy())
    assert fwd.iloc[-1].isna().all()
    # A longer horizon compounds the one-day returns over the same span.
    fwd5 = ev.forward_returns(prices, horizon=5, lag=1)
    gross = (1 + r).rolling(5).apply(np.prod, raw=True)
    assert np.allclose(fwd5.iloc[:-6].to_numpy(), gross.iloc[6:].to_numpy() - 1)


@pytest.mark.parametrize("seed", SEEDS)
def test_ic_summary_relations(seed):
    ic = pd.Series(np.random.default_rng(seed).normal(0.02, 0.1, 200))
    for h in (1, 5, 20):
        s = ev.ic_summary(ic, h)
        assert s["n"] == len(ic.iloc[::h])
        assert s["t_stat"] == pytest.approx(s["ir"] * np.sqrt(s["n"]))


@pytest.mark.parametrize("seed", SEEDS)
def test_long_short_properties(seed):
    prices = _prices(seed)
    factor = _panel(seed, n_dates=len(prices), nan_share=0.05)
    factor.index = prices.index
    out = ev.quantile_long_short(factor, prices, horizon=5, cost_bps_one_way=10.0)
    assert (out["net"] <= out["gross"] + 1e-15).all()
    assert ((out["turnover"] >= 0) & (out["turnover"] <= 4 + 1e-12)).all()
    assert out["turnover"].iloc[0] == pytest.approx(2.0)
    assert out["max_drawdown"] <= 0
    free = ev.quantile_long_short(factor, prices, horizon=5, cost_bps_one_way=0.0)
    pd.testing.assert_series_equal(free["net"], free["gross"], check_names=False)
    # Flipping the signal swaps the long and short legs.
    flipped = ev.quantile_long_short(-factor, prices, horizon=5, cost_bps_one_way=10.0)
    pd.testing.assert_series_equal(flipped["gross"], -out["gross"])
    pd.testing.assert_series_equal(flipped["turnover"], out["turnover"])


@pytest.mark.parametrize("seed", SEEDS)
def test_half_split_and_lead_lag_types_and_bounds(seed):
    rng = np.random.default_rng(seed)
    ic = pd.Series(rng.normal(0, 0.1, 30))
    result = ev.half_split_sign_agreement(ic)
    assert result is True or result is False
    assert ev.half_split_sign_agreement(-ic) is result  # sign agreement survives a sign flip
    idx = pd.bdate_range("2025-01-01", periods=100)
    a, b = pd.Series(rng.normal(size=100), index=idx), pd.Series(rng.normal(size=100), index=idx)
    out = ev.lead_lag_tstat(a, b, lag=2)
    assert -1 <= out["r"] <= 1 and out["n"] == 98
    assert np.sign(out["t_stat"]) == np.sign(out["r"])
