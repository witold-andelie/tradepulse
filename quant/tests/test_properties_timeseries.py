"""C9 property tests for time-series functions (indicators and regime indicators).

Each property is checked on several seeded random panels, some with missing values.
"""

import numpy as np
import pandas as pd
import pytest

from quant import indicators as ind
from quant import regime_indicators as rg

SEEDS = range(5)


def _prices(seed, n_dates=260, n_names=12, nan_share=0.0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2024-01-01", periods=n_dates)
    rets = rng.normal(0.0003, 0.02, size=(n_dates, n_names))
    prices = 100 * np.cumprod(1 + rets, axis=0)
    if nan_share:
        prices[rng.random(prices.shape) < nan_share] = np.nan
    return pd.DataFrame(prices, index=idx, columns=[f"S{i}" for i in range(n_names)])


def _finite(df):
    """All finite values of a frame or series as a flat array (missing values dropped)."""
    values = np.asarray(df, dtype=float).ravel()
    return values[np.isfinite(values)]


TIME_SERIES_FUNCTIONS = {
    "simple_returns": lambda p: ind.simple_returns(p),
    "momentum": lambda p: ind.momentum(p, 20, skip=5),
    "reversal": lambda p: ind.reversal(p, 5),
    "realized_vol": lambda p: ind.realized_vol(p, 20),
    "volume_zscore": lambda p: ind.volume_zscore(p, 60),
    "distance_to_high": lambda p: ind.distance_to_high(p, 50),
    "moving_average": lambda p: ind.moving_average(p, 30),
    "rolling_beta": lambda p: ind.rolling_beta(p, p["S0"], 60),
    "attention_change": lambda p: ind.attention_change(p),
    "below_ma": lambda p: rg.below_ma(p["S1"], 50).to_frame(),
    "avg_pairwise_corr": lambda p: rg.avg_pairwise_corr(p, 20).to_frame(),
    "breadth_above_ma": lambda p: rg.breadth_above_ma(p, 50).to_frame(),
    "rolling_percentile": lambda p: rg.rolling_percentile(p["S2"], 60).to_frame(),
    "change": lambda p: rg.change(p["S3"], 20).to_frame(),
}


@pytest.mark.parametrize("name", list(TIME_SERIES_FUNCTIONS))
@pytest.mark.parametrize("cut", [61, 150, 259])
def test_truncation_does_not_change_history(name, cut):
    """Point-in-time: computing on rows [:cut] gives exactly the first `cut` rows of the full run.

    Stronger than shocking the last row: no row may depend on any later row.
    """
    fn = TIME_SERIES_FUNCTIONS[name]
    prices = _prices(0, nan_share=0.02)
    full = fn(prices)
    partial = fn(prices.iloc[:cut])
    pd.testing.assert_frame_equal(partial, full.iloc[:cut])


@pytest.mark.parametrize("name", list(TIME_SERIES_FUNCTIONS))
def test_inputs_are_not_mutated(name):
    prices = _prices(1, nan_share=0.02)
    before = prices.copy()
    TIME_SERIES_FUNCTIONS[name](prices)
    pd.testing.assert_frame_equal(prices, before)


@pytest.mark.parametrize("seed", SEEDS)
def test_price_scale_invariance(seed):
    """Return-based indicators must not care about the currency or unit of a price."""
    prices = _prices(seed, nan_share=0.02)
    scaled = prices * 37.5
    for fn in (
        lambda p: ind.simple_returns(p),
        lambda p: ind.momentum(p, 20, skip=5),
        lambda p: ind.realized_vol(p, 20),
        lambda p: ind.distance_to_high(p, 50),
        lambda p: ind.rolling_beta(p, p["S0"], 60),
        lambda p: rg.avg_pairwise_corr(p, 20).to_frame(),
        lambda p: rg.breadth_above_ma(p, 50).to_frame(),
    ):
        pd.testing.assert_frame_equal(fn(scaled), fn(prices), rtol=1e-9, atol=1e-12)


@pytest.mark.parametrize("seed", SEEDS)
def test_volume_zscore_is_invariant_to_volume_units(seed):
    volume = _prices(seed, nan_share=0.02) * 1e4
    pd.testing.assert_frame_equal(
        ind.volume_zscore(volume * 1000.0, 60), ind.volume_zscore(volume, 60), rtol=1e-9, atol=1e-9
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_momentum_identities(seed):
    prices = _prices(seed, nan_share=0.02)
    pd.testing.assert_frame_equal(ind.momentum(prices, 1), ind.simple_returns(prices))
    pd.testing.assert_frame_equal(ind.reversal(prices, 10), -ind.momentum(prices, 10))
    # Compounding: (1 + mom(20, skip=5)) * (1 + mom(5)) == 1 + mom(20). The identity needs the
    # middle price P[t-5], so it is checked on a panel without gaps.
    dense = _prices(seed)
    lhs = (1 + ind.momentum(dense, 20, skip=5)) * (1 + ind.momentum(dense, 5))
    pd.testing.assert_frame_equal(lhs, 1 + ind.momentum(dense, 20), rtol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_distance_to_high_bounds(seed):
    prices = _prices(seed, nan_share=0.02)
    out = ind.distance_to_high(prices, 50)
    finite = _finite(out)
    assert len(finite) > 0
    assert (finite <= 1e-15).all() and (finite > -1).all()
    # A new rolling high has distance zero.
    at_high = prices.eq(prices.rolling(50, min_periods=50).max())
    assert at_high.to_numpy().any()
    assert np.allclose(_finite(out.where(at_high)), 0.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_realized_vol_non_negative_and_full_window(seed):
    prices = _prices(seed)
    out = ind.realized_vol(prices, 20)
    assert (_finite(out) >= 0).all()
    assert out.iloc[:20].isna().all().all()
    assert out.iloc[20:].notna().all().all()


@pytest.mark.parametrize("seed", SEEDS)
def test_beta_of_benchmark_with_itself_is_one(seed):
    prices = _prices(seed)
    beta = ind.rolling_beta(prices[["S0"]], prices["S0"], 60)["S0"]
    assert np.allclose(beta.dropna().to_numpy(), 1.0)
    assert beta.iloc[:60].isna().all()


@pytest.mark.parametrize("seed", SEEDS)
def test_constant_inputs(seed):
    idx = pd.bdate_range("2024-01-01", periods=150)
    level = float(np.random.default_rng(seed).uniform(1, 500))
    flat = pd.DataFrame({"A": np.full(150, level)}, index=idx)
    assert np.allclose(ind.moving_average(flat, 30)["A"].dropna(), level)
    assert np.allclose(ind.attention_change(flat)["A"].dropna(), 0.0)
    assert np.allclose(ind.distance_to_high(flat, 30)["A"].dropna(), 0.0)
    assert ind.volume_zscore(flat, 60)["A"].isna().all()


@pytest.mark.parametrize("seed", SEEDS)
def test_regime_indicator_ranges(seed):
    prices = _prices(seed, nan_share=0.02)
    corr = rg.avg_pairwise_corr(prices, 20).dropna()
    assert ((corr >= -1) & (corr <= 1)).all()
    breadth = rg.breadth_above_ma(prices, 50).dropna()
    assert ((breadth >= 0) & (breadth <= 1)).all()
    pct = rg.rolling_percentile(prices["S0"], 60).dropna()
    assert ((pct > 0) & (pct <= 1)).all()
    flags = rg.below_ma(prices["S0"], 50).dropna()
    assert set(flags.unique()) <= {0.0, 1.0}


@pytest.mark.parametrize("seed", SEEDS)
def test_breadth_ignores_symbols_without_an_average(seed):
    """A newly listed symbol, or one with no data, must not dilute breadth."""
    prices = _prices(seed)
    base = rg.breadth_above_ma(prices, 50)
    widened = prices.assign(EMPTY=np.nan, LATE=prices["S0"].where(prices.index >= prices.index[150]))
    out = rg.breadth_above_ma(widened, 50)
    ma = widened.rolling(50, min_periods=50).mean()
    expected = widened.gt(ma).sum(axis=1) / ma.notna().sum(axis=1)
    pd.testing.assert_series_equal(out.iloc[:199], base.iloc[:199])  # LATE has no average yet
    pd.testing.assert_series_equal(out, expected.where(ma.notna().any(axis=1)))


@pytest.mark.parametrize("seed", SEEDS)
def test_avg_pairwise_corr_matches_corrcoef(seed):
    prices = _prices(seed)
    returns = ind.simple_returns(prices).iloc[-20:].to_numpy()
    c = np.corrcoef(returns.T)
    k = c.shape[0]
    expected = (c.sum() - k) / (k * (k - 1))
    assert rg.avg_pairwise_corr(prices, 20).iloc[-1] == pytest.approx(expected)


@pytest.mark.parametrize("seed", SEEDS)
def test_rolling_percentile_is_one_at_window_max(seed):
    s = _prices(seed)["S0"]
    pct = rg.rolling_percentile(s, 60)
    at_max = s.eq(s.rolling(60, min_periods=60).max())
    assert (pct[at_max] == 1.0).all()


@pytest.mark.parametrize("seed", SEEDS)
def test_regime_points_and_classification(seed):
    rng = np.random.default_rng(seed)
    flags = pd.DataFrame(rng.integers(0, 2, size=(50, 5)).astype(float))
    flags[rng.random(flags.shape) < 0.1] = np.nan
    points = rg.regime_points(flags)
    assert ((points >= 0) & (points <= flags.shape[1])).all()
    assert (points == flags.fillna(0).sum(axis=1)).all()
    order = {"normal": 0, "elevated": 1, "stressed": 2}
    levels = rg.classify_regime(points).map(order)
    by_points = pd.DataFrame({"p": points, "lvl": levels}).sort_values("p")
    assert by_points["lvl"].is_monotonic_increasing  # more points never means a calmer state
