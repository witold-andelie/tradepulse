import numpy as np
import pandas as pd
import pytest

from quant import indicators as ind


def _col(values, start="2025-01-01", name="A"):
    idx = pd.bdate_range(start, periods=len(values))
    return pd.DataFrame({name: np.asarray(values, dtype=float)}, index=idx)


def test_simple_returns():
    out = ind.simple_returns(_col([100, 110, 99]))["A"]
    assert np.isnan(out.iloc[0])
    assert out.iloc[1] == pytest.approx(0.10)
    assert out.iloc[2] == pytest.approx(-0.10)


def test_momentum_and_skip():
    p = _col(np.arange(1, 31))
    assert ind.momentum(p, 5)["A"].iloc[10] == pytest.approx(11 / 6 - 1)
    assert ind.momentum(p, 5, skip=2)["A"].iloc[10] == pytest.approx(9 / 6 - 1)
    assert np.isnan(ind.momentum(p, 5)["A"].iloc[4])


def test_reversal_is_negative_momentum():
    p = _col(np.arange(1, 31))
    pd.testing.assert_frame_equal(ind.reversal(p, 5), -ind.momentum(p, 5))


def test_realized_vol_matches_definition(random_prices):
    out = ind.realized_vol(random_prices, window=20)
    r = random_prices.pct_change()
    expected = np.std(r["S0"].iloc[31:51].to_numpy(), ddof=1) * np.sqrt(252)
    assert out["S0"].iloc[50] == pytest.approx(expected)
    assert out["S0"].iloc[:20].isna().all()


def test_volume_zscore_excludes_current_row():
    vol = np.full(70, 1000.0)
    vol[::2] = 2000.0
    vol[-1] = 8000.0
    out = ind.volume_zscore(_col(vol), window=60)["A"]
    base = np.log(vol[-61:-1])
    expected = (np.log(8000.0) - base.mean()) / base.std(ddof=1)
    assert out.iloc[-1] == pytest.approx(expected)
    assert out.iloc[:60].isna().all()


def test_volume_zscore_zero_std_is_nan():
    out = ind.volume_zscore(_col(np.full(70, 1000.0)), window=60)["A"]
    assert out.iloc[-1:].isna().all()


def test_distance_to_high():
    out = ind.distance_to_high(_col([1, 3, 2]), window=2)["A"]
    assert np.isnan(out.iloc[0])
    assert out.iloc[1] == pytest.approx(0.0)
    assert out.iloc[2] == pytest.approx(2 / 3 - 1)


def test_moving_average():
    out = ind.moving_average(_col([1, 2, 3, 4]), 2)["A"]
    assert list(out.iloc[1:]) == pytest.approx([1.5, 2.5, 3.5])


def test_rolling_beta_recovers_known_beta(dates):
    rng = np.random.default_rng(1)
    rb = rng.normal(0, 0.01, len(dates))
    bench = pd.Series(100 * np.cumprod(1 + rb), index=dates)
    stock = pd.DataFrame({"X": 50 * np.cumprod(1 + 2.0 * rb)}, index=dates)
    beta = ind.rolling_beta(stock, bench, window=20)["X"]
    assert beta.iloc[30:].to_numpy() == pytest.approx(2.0)
    assert beta.iloc[:20].isna().all()


def test_attention_change():
    views = np.full(120, 100.0)
    views[-8:-1] = 300.0  # the last row is not visible because of lag=1
    out = ind.attention_change(_col(views), short=7, long=83, lag=1)["A"]
    assert out.iloc[-1] == pytest.approx(np.log1p(300.0) - np.log1p(100.0))
    assert out.iloc[-9] == pytest.approx(0.0)
    assert out.iloc[:90].isna().all()


@pytest.mark.parametrize("fn", [
    lambda p: ind.simple_returns(p),
    lambda p: ind.momentum(p, 20, skip=5),
    lambda p: ind.reversal(p, 5),
    lambda p: ind.realized_vol(p, 20),
    lambda p: ind.volume_zscore(p, 60),
    lambda p: ind.distance_to_high(p, 50),
    lambda p: ind.moving_average(p, 30),
    lambda p: ind.rolling_beta(p, p["S0"], 60),
    lambda p: ind.attention_change(p),
])
def test_no_look_ahead(fn, random_prices):
    """Changing the last row must not change any earlier output row."""
    base = fn(random_prices)
    shocked = random_prices.copy()
    shocked.iloc[-1] = shocked.iloc[-1] * 3.0
    after = fn(shocked)
    pd.testing.assert_frame_equal(base.iloc[:-1], after.iloc[:-1])
