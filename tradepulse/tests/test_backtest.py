import numpy as np
import pandas as pd
import pytest

from tradepulse.backtest import decision_rows, fit_rows, track_record, walk_forward
from tradepulse.config import load_config
from tradepulse.contracts import validate_payload
from tradepulse.research import evaluate
from tradepulse.research.panels import build_pool_panels

CFG = load_config()
POOL = "us_equity"


def test_decision_rows():
    idx = pd.bdate_range("2025-01-01", periods=300)
    rows = decision_rows(idx, str(idx[50].date()), burn_in=120, step=5)
    assert rows[0] == 170 and rows[1] == 175 and rows[-1] == 295 and len(rows) == 26


def test_fit_rows():
    assert fit_rows(170, horizon=5, lag=1, first=50) == (50, 164)
    assert fit_rows(80, horizon=5, lag=1, first=50) is None


def _market(seed=11, n_names=40, n_days=560):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-06-03", periods=n_days)
    cols = [f"S{i:02d}" for i in range(n_names)]
    regime = np.repeat(rng.normal(size=(n_days // 10 + 1, n_names)), 10, axis=0)[:n_days]
    signal = pd.DataFrame(regime, index=dates, columns=cols)
    rets = 0.0003 + 0.003 * signal.shift(1).fillna(0.0).to_numpy() + rng.normal(0, 0.01, size=(n_days, n_names))
    prices = pd.DataFrame(100 * np.cumprod(1 + rets, axis=0), index=dates, columns=cols)
    volume = pd.DataFrame(rng.lognormal(13, 0.3, size=(n_days, n_names)), index=dates, columns=cols)
    bench = prices.mean(axis=1)
    noise = pd.DataFrame(rng.normal(size=(n_days, n_names)), index=dates, columns=cols)
    groups = pd.Series({c: ("tech" if i % 2 else "energy") for i, c in enumerate(cols)})
    panels = build_pool_panels(prices, volume, None, groups, CFG["pools"][POOL], CFG["factors"],
                               extra={"sig_test": signal, "evt_drift": noise})
    return prices, bench, panels


@pytest.fixture(scope="module")
def run():
    prices, bench, panels = _market()
    specs = dict(evaluate.FACTOR_SPECS)
    evaluate.FACTOR_SPECS["sig_test"] = {"title": "t", "measures": "m", "definition": "d", "sources": ["x"],
                                         "availability": "a"}
    try:
        window_start = str(prices.index[300].date())
        points = pd.Series(0, index=prices.index)
        result = walk_forward(POOL, panels, prices, bench, points, CFG, window_start, refit_every=20, burn_in=120)
        late = prices.copy()
        late.iloc[500:] *= np.random.default_rng(5).uniform(0.5, 1.5, size=late.iloc[500:].shape)
        perturbed = walk_forward(POOL, panels, late, bench, points, CFG, window_start, refit_every=20, burn_in=120)
    finally:
        evaluate.FACTOR_SPECS.clear()
        evaluate.FACTOR_SPECS.update(specs)
    return prices, result, perturbed


def test_walk_forward_finds_the_signal_out_of_sample(run):
    _, res, _ = run
    assert res["decisions"] > 20
    assert res["ic_comp_oos"] is not None and res["ic_comp_oos"] > 0.05
    assert "evt_drift" not in res["latest_weights"]
    assert res["latest_weights"]["sig_test"] > 0
    assert res["settled"] > 0 and res["pending"] > 0
    by = {r["tier"]: r for r in res["by_tier"]}
    longs = [by[t] for t in ("STRONG_OVERWEIGHT", "OVERWEIGHT") if t in by]
    assert longs and sum(r["mean_excess_bps"] * r["n"] for r in longs) > 0
    assert all(r["hit_rate"] is None for r in res["by_tier"] if r["tier"] in ("NEUTRAL", "NO_CALL"))


def test_no_look_ahead(run):
    prices, res, perturbed = run
    cutoff = prices.index[500]
    early = [d for d in res["decision_tiers"] if pd.Timestamp(d) < cutoff]
    assert early, "need decisions before the perturbation"
    for d in early:
        assert res["decision_tiers"][d] == perturbed["decision_tiers"][d], d


def test_track_record_contract(run):
    _, res, _ = run
    tr = track_record([res], {"start": "2025-08-01", "end": "2026-07-31"})
    assert validate_payload(tr, "TrackRecord") == []
    assert tr["mode"] == "walk_forward" and tr["settled_count"] == res["settled"]
    assert len(tr["calibration"]) == 5
    assert tr["composite_ic_series"] and all(r["pool"] == POOL for r in tr["composite_ic_series"])
