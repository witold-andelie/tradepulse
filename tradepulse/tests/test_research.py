import numpy as np
import pandas as pd
import pytest

from tradepulse.config import load_config
from tradepulse.contracts import validate_payload
from tradepulse.research.evaluate import FACTOR_SPECS, composite_ic, factor_metrics, research_pool
from tradepulse.research.panels import PV_FACTORS, attention_factor, build_pool_panels, price_volume_factors

CFG = load_config()
POOL = "us_equity"
N_NAMES, N_DAYS = 40, 560


@pytest.fixture(scope="module")
def market():
    """A synthetic market where `signal` (known at t) drives returns from t+1 on, and `noise` does not."""
    rng = np.random.default_rng(2026)
    dates = pd.bdate_range("2025-01-01", periods=N_DAYS)
    cols = [f"S{i:02d}" for i in range(N_NAMES)]
    regime = np.repeat(rng.normal(size=(N_DAYS // 10 + 1, N_NAMES)), 10, axis=0)[:N_DAYS]
    signal = pd.DataFrame(regime, index=dates, columns=cols)
    drift = 0.003 * signal.shift(1).fillna(0.0).to_numpy()
    rets = 0.0003 + drift + rng.normal(0, 0.01, size=(N_DAYS, N_NAMES))
    prices = pd.DataFrame(100 * np.cumprod(1 + rets, axis=0), index=dates, columns=cols)
    volume = pd.DataFrame(rng.lognormal(13, 0.3, size=(N_DAYS, N_NAMES)), index=dates, columns=cols)
    views = pd.DataFrame(rng.poisson(1000, size=(N_DAYS, N_NAMES)).astype(float), index=dates, columns=cols)
    noise = pd.DataFrame(rng.normal(size=(N_DAYS, N_NAMES)), index=dates, columns=cols)
    groups = pd.Series({c: ("tech" if i % 2 else "energy") for i, c in enumerate(cols)})
    return {"prices": prices, "volume": volume, "views": views, "signal": signal, "noise": noise, "groups": groups}


@pytest.fixture(scope="module")
def panels(market):
    return build_pool_panels(market["prices"], market["volume"], market["views"], market["groups"],
                             CFG["pools"][POOL], CFG["factors"],
                             extra={"sig_test": market["signal"], "noise_test": market["noise"]})


def test_price_volume_factors_shapes(market):
    raw = price_volume_factors(market["prices"], market["volume"], 252, 21)
    assert set(raw) == set(PV_FACTORS)
    for panel in raw.values():
        assert panel.shape == market["prices"].shape
    assert (raw["pv_dist_52w_high"].dropna() <= 1e-12).all().all()
    assert (raw["pv_lowvol_20d"].dropna() <= 0).all().all()


def test_panels_are_standardised_and_aligned(panels, market):
    assert set(panels) == set(PV_FACTORS) | {"att_pageviews", "sig_test", "noise_test"}
    for name, panel in panels.items():
        assert panel.shape == market["prices"].shape, name
        row = panel.iloc[-1].dropna()
        assert abs(row.mean()) < 1e-8, name


def test_non_baseline_panels_are_residualised(panels):
    t = panels["sig_test"].index[-1]
    sig = panels["sig_test"].loc[t]
    for base in PV_FACTORS:
        both = pd.concat([sig, panels[base].loc[t]], axis=1).dropna()
        assert abs(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1]) < 1e-6, base


def test_attention_is_residual_to_volume(market):
    raw = price_volume_factors(market["prices"], market["volume"], 252, 21)
    att = attention_factor(market["views"], market["prices"], raw["pv_volume_z"], raw["pv_lowvol_20d"])
    t = att.dropna(how="all").index[-1]
    both = pd.concat([att.loc[t], raw["pv_volume_z"].loc[t]], axis=1).dropna()
    assert len(both) > 10
    assert abs(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1]) < 1e-6


def test_no_look_ahead_in_panels(market):
    shocked = market["prices"].copy()
    shocked.iloc[-1] *= 1.5
    args = (market["volume"], market["views"], market["groups"], CFG["pools"][POOL], CFG["factors"])
    a = build_pool_panels(market["prices"], *args)
    b = build_pool_panels(shocked, *args)
    for name in PV_FACTORS:
        pd.testing.assert_frame_equal(a[name].iloc[:-1], b[name].iloc[:-1])


def test_factor_metrics_signal(panels, market):
    z, prices = panels["sig_test"].iloc[-250:], market["prices"].iloc[-250:]
    m = factor_metrics("sig_test", POOL, z, prices, horizons=[1, 5, 20],
                       primary_horizon=5, lag=1, cost_bps_one_way=5.0, rows_per_year=252, min_names=20)
    assert set(m.ic_by_horizon) == {1, 5, 20}
    assert isinstance(m.ic_by_horizon[5]["n"], int)
    assert m.ic_by_horizon[5]["mean"] > 0.1
    assert m.n_dates > 100 and 0.9 <= m.coverage <= 1.0
    assert m.spec_complete is False  # not in FACTOR_SPECS
    assert m.long_short["net_sharpe"] > 1.0


def test_research_pool_gates_and_weights(panels, market):
    specs_backup = dict(FACTOR_SPECS)
    FACTOR_SPECS["sig_test"] = {"title": "t", "measures": "m", "definition": "d", "sources": ["x"], "availability": "a"}
    FACTOR_SPECS["noise_test"] = FACTOR_SPECS["sig_test"]
    try:
        window = (str(market["prices"].index[-250].date()), str(market["prices"].index[-1].date()))
        out = research_pool(POOL, panels, market["prices"], CFG, window)
    finally:
        FACTOR_SPECS.clear()
        FACTOR_SPECS.update(specs_backup)
    cards = {c["factor"]: c for c in out["cards"]}
    assert set(cards) == set(panels)
    for card in out["cards"]:
        assert validate_payload(card, "FactorCard") == [], card["factor"]
        assert card["window"] == {"start": window[0], "end": window[1]}
    assert cards["sig_test"]["status"] == "ACTIVE"
    assert cards["noise_test"]["status"] != "ACTIVE"
    assert out["weights"]["sig_test"] > 0 and out["weights"]["noise_test"] == 0.0
    active = [w for f, w in out["weights"].items() if cards[f]["status"] == "ACTIVE"]
    assert sum(active) == pytest.approx(1.0)
    ic = composite_ic(panels, out["weights"], market["prices"], primary_horizon=5, lag=1, min_names=20)
    assert ic is not None and ic > 0.05
    assert composite_ic(panels, {k: 0.0 for k in panels}, market["prices"], primary_horizon=5, lag=1,
                        min_names=20) is None
