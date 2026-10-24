"""C9 property tests for costs, earnings surprise and settlement scoring."""

import numpy as np
import pandas as pd
import pytest

from quant import costs, settlement
from quant import earnings as ea

SEEDS = range(5)


# --- costs ----------------------------------------------------------------------------------

def _weights(rng, names):
    w = pd.Series(rng.normal(size=len(names)), index=names)
    return w / w.abs().sum()


@pytest.mark.parametrize("seed", SEEDS)
def test_turnover_is_a_distance(seed):
    rng = np.random.default_rng(seed)
    a = _weights(rng, list("ABCDE"))
    b = _weights(rng, list("CDEFG"))
    c = _weights(rng, list("AEGHI"))
    assert costs.turnover(a, a) == 0.0
    assert costs.turnover(a, b) == pytest.approx(costs.turnover(b, a))
    assert costs.turnover(a, c) <= costs.turnover(a, b) + costs.turnover(b, c) + 1e-12
    assert costs.turnover(pd.Series(dtype=float), a) == pytest.approx(a.abs().sum())


@pytest.mark.parametrize("seed", SEEDS)
def test_expected_alpha_scaling(seed):
    rng = np.random.default_rng(seed)
    ic, sigma = rng.uniform(-0.1, 0.1), rng.uniform(0.005, 0.05)
    score = pd.Series(rng.normal(size=20))
    base = costs.expected_alpha_bps(ic, sigma, 1, score)
    pd.testing.assert_series_equal(costs.expected_alpha_bps(ic, sigma, 4, score), 2 * base)
    pd.testing.assert_series_equal(costs.expected_alpha_bps(ic, sigma, 1, -score), -base)


@pytest.mark.parametrize("seed", SEEDS)
def test_net_edge_is_odd_and_cost_free_identity(seed):
    alpha = pd.Series(np.random.default_rng(seed).normal(0, 30, 50))
    pd.testing.assert_series_equal(costs.net_edge_bps(alpha, 0.0), alpha)
    pd.testing.assert_series_equal(costs.net_edge_bps(-alpha, 5.0), -costs.net_edge_bps(alpha, 5.0))
    # Costs always shrink the magnitude by exactly the round trip before the sign is applied.
    net = costs.net_edge_bps(alpha, 5.0)
    assert np.allclose(np.abs(net), np.abs(alpha.abs() - costs.round_trip_bps(5.0)))


# --- earnings -------------------------------------------------------------------------------

def _facts(seed, n_periods=8, n_restatements=2):
    rng = np.random.default_rng(seed)
    ends = pd.date_range("2022-03-31", periods=n_periods, freq="QE")
    rows = []
    for end in ends:
        start = end - pd.offsets.QuarterBegin(startingMonth=1)
        first_filed = end + pd.Timedelta(days=int(rng.integers(20, 40)))
        for k in range(n_restatements + 1):
            rows.append({"period_start": start, "period_end": end,
                         "value": float(rng.normal(1.0, 0.3)),
                         "filed": first_filed + pd.Timedelta(days=200 * k)})
    return pd.DataFrame(rows)


@pytest.mark.parametrize("seed", SEEDS)
def test_first_reported_keeps_earliest_and_ignores_row_order(seed):
    facts = _facts(seed)
    out = ea.first_reported(facts)
    assert not out.duplicated(["period_start", "period_end"]).any()
    earliest = facts.groupby(["period_start", "period_end"])["filed"].min()
    assert (out.set_index(["period_start", "period_end"])["filed"] == earliest).all()
    shuffled = facts.sample(frac=1.0, random_state=seed)
    pd.testing.assert_frame_equal(ea.first_reported(shuffled), out)
    assert out["period_end"].is_monotonic_increasing


@pytest.mark.parametrize("seed", SEEDS)
def test_first_reported_does_not_see_later_restatements(seed):
    """Adding a restatement filed later must never change the first-reported value."""
    facts = _facts(seed)
    out = ea.first_reported(facts)
    late = facts.assign(value=facts["value"] + 99.0, filed=facts["filed"] + pd.Timedelta(days=999))
    pd.testing.assert_frame_equal(ea.first_reported(pd.concat([facts, late])), out)


@pytest.mark.parametrize("seed", SEEDS)
def test_sue_scale_and_sign(seed):
    rng = np.random.default_rng(seed)
    ends = pd.date_range("2020-03-31", periods=20, freq="QE")
    eps = pd.DataFrame({"period_end": ends, "value": rng.normal(1.0, 0.3, 20),
                        "filed": ends + pd.Timedelta(days=30)})
    before = eps.copy()
    base = ea.sue(eps)
    scaled = ea.sue(eps.assign(value=eps["value"] * 2.5))
    assert np.allclose(scaled["sue"], base["sue"], equal_nan=True)
    assert np.allclose(scaled["diff"], 2.5 * base["diff"], equal_nan=True)
    negated = ea.sue(eps.assign(value=-eps["value"]))
    assert np.allclose(negated["sue"], -base["sue"], equal_nan=True)
    assert base["sue"].iloc[:8].isna().all()  # needs 4 diffs before q, and diffs need 4 quarters
    pd.testing.assert_frame_equal(eps, before)  # sue must not modify its input


@pytest.mark.parametrize("seed", SEEDS)
def test_event_panel_point_in_time_and_hold(seed):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2025-01-01", periods=80)
    symbols = ["A", "B", "C"]
    events = pd.DataFrame({
        "symbol": rng.choice(symbols + ["Z"], size=12),
        "available_date": idx[rng.integers(0, 80, size=12)],
        "value": rng.normal(size=12),
    })
    hold = 7
    panel = ea.event_panel(events, idx, symbols, hold=hold)
    assert list(panel.columns) == symbols
    # Only event values appear, each symbol only shows its own events.
    for s in symbols:
        seen = set(panel[s].dropna().unique())
        assert seen <= set(events.loc[events["symbol"] == s, "value"])
        # Nothing is visible before the symbol's first event becomes available.
        mine = events.loc[events["symbol"] == s, "available_date"]
        if len(mine):
            assert panel.loc[panel.index <= mine.min(), s].isna().all()
        else:
            assert panel[s].isna().all()
        # No value is shown for more than `hold` consecutive rows.
        run = 0
        prev = None
        for v in panel[s]:
            run = run + 1 if (not np.isnan(v) and v == prev) else (0 if np.isnan(v) else 1)
            prev = v
            assert run <= hold
    # A shorter calendar is a prefix of the longer one: the past never depends on later dates.
    pd.testing.assert_frame_equal(ea.event_panel(events, idx[:40], symbols, hold=hold), panel.iloc[:40])


# --- settlement -----------------------------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_excess_return_and_hit_symmetry(seed):
    rng = np.random.default_rng(seed)
    entry, exit_ = rng.uniform(10, 200, 2)
    assert settlement.excess_return(entry, exit_, entry, exit_) == pytest.approx(0.0, abs=1e-15)
    for e in rng.normal(0, 0.05, 20):
        assert settlement.hit("OVERWEIGHT", e) is settlement.hit("UNDERWEIGHT", -e)
        assert settlement.hit("STRONG_OVERWEIGHT", e) is settlement.hit("AVOID", -e)
    assert settlement.hit("OVERWEIGHT", 0.0) is False and settlement.hit("AVOID", 0.0) is False


@pytest.mark.parametrize("seed", SEEDS)
def test_brier_score_bounds(seed):
    rng = np.random.default_rng(seed)
    p = pd.Series(rng.uniform(0, 1, 100))
    o = pd.Series(rng.integers(0, 2, 100))
    score = settlement.brier_score(p, o)
    assert 0.0 <= score <= 1.0
    assert settlement.brier_score(o.astype(float), o) == 0.0
    assert settlement.brier_score(1.0 - o.astype(float), o) == 1.0


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("n_buckets", [1, 5, 10])
def test_calibration_table_partitions_the_sample(seed, n_buckets):
    rng = np.random.default_rng(seed)
    p = pd.Series(np.append(rng.uniform(0, 1, 200), [0.0, 1.0, 0.5]))
    o = pd.Series(rng.integers(0, 2, len(p)))
    tab = settlement.calibration_table(p, o, n_buckets=n_buckets)
    assert len(tab) == n_buckets
    assert tab["n"].sum() == len(p)
    filled = tab[tab["n"] > 0]
    assert (filled["predicted"] >= filled["bucket_low"]).all()
    assert (filled["predicted"] <= filled["bucket_high"]).all()
    assert ((filled["observed"] >= 0) & (filled["observed"] <= 1)).all()
    # Bucket means reproduce the overall means when weighted by n.
    assert (filled["predicted"] * filled["n"]).sum() == pytest.approx(p.sum())
    assert (filled["observed"] * filled["n"]).sum() == pytest.approx(o.sum())
