import numpy as np
import pandas as pd
import pytest

from quant import earnings as ea
from quant import regime_indicators as rg


def _ts(s):
    return pd.Timestamp(s)


def test_first_reported_keeps_earliest_filing():
    facts = pd.DataFrame({
        "period_start": [_ts("2025-01-01"), _ts("2025-01-01")],
        "period_end": [_ts("2025-03-31"), _ts("2025-03-31")],
        "value": [1.10, 1.05],
        "filed": [_ts("2026-05-01"), _ts("2025-05-01")],
    })
    out = ea.first_reported(facts)
    assert len(out) == 1 and out["value"].iloc[0] == pytest.approx(1.05)


def test_quarterly_eps_derives_q4():
    facts = pd.DataFrame({
        "period_start": [_ts("2024-01-01"), _ts("2024-04-01"), _ts("2024-07-01"), _ts("2024-01-01")],
        "period_end": [_ts("2024-03-31"), _ts("2024-06-30"), _ts("2024-09-30"), _ts("2024-12-31")],
        "value": [2.0, 2.5, 3.0, 10.0],
        "filed": [_ts("2024-05-01"), _ts("2024-08-01"), _ts("2024-11-01"), _ts("2025-02-15")],
    })
    out = ea.quarterly_eps(facts)
    assert list(out["period_end"]) == [_ts("2024-03-31"), _ts("2024-06-30"), _ts("2024-09-30"), _ts("2024-12-31")]
    q4 = out.iloc[-1]
    assert q4["value"] == pytest.approx(2.5)
    assert q4["filed"] == _ts("2025-02-15")


def test_sue_definition():
    values = [1, 1, 1, 1, 1.1, 1.2, 1.0, 1.3, 1.2, 1.4, 1.1, 1.6]
    ends = pd.date_range("2023-03-31", periods=12, freq="QE")
    eps = pd.DataFrame({"period_end": ends, "value": values, "filed": ends + pd.Timedelta(days=30)})
    out = ea.sue(eps)
    assert out["diff"].iloc[4] == pytest.approx(0.1)
    assert np.isnan(out["sue"].iloc[7])  # only 3 previous diffs
    assert out["sue"].iloc[8] == pytest.approx(0.1 / np.std([0.1, 0.2, 0.0, 0.3], ddof=1))
    assert out["sue"].iloc[8] == pytest.approx(0.774597, abs=1e-5)
    prev = [0.1, 0.2, 0.0, 0.3, 0.1, 0.2, 0.1]
    assert out["sue"].iloc[11] == pytest.approx(0.3 / np.std(prev, ddof=1))


def test_event_panel_lag_hold_and_replace():
    idx = pd.bdate_range("2025-01-01", periods=10)
    events = pd.DataFrame({"symbol": ["A", "A"], "available_date": [_ts("2025-01-02"), _ts("2025-01-08")],
                           "value": [1.5, -0.5]})
    out = ea.event_panel(events, idx, ["A", "B"], hold=3)
    a = out["A"]
    assert np.isnan(a.loc["2025-01-02"])  # not visible on its own date
    assert list(a.loc["2025-01-03":"2025-01-07"]) == [1.5, 1.5, 1.5]
    assert a.loc["2025-01-09"] == -0.5  # the newer event replaces the older one
    assert out["B"].isna().all()


def test_below_ma_and_ratio():
    s = pd.Series([10.0, 10.0, 10.0, 7.0], index=pd.bdate_range("2025-01-01", periods=4))
    out = rg.below_ma(s, window=3)
    assert np.isnan(out.iloc[1]) and out.iloc[2] == 0.0 and out.iloc[3] == 1.0
    assert rg.term_structure_ratio(pd.Series([20.0]), pd.Series([16.0])).iloc[0] == pytest.approx(1.25)


def test_avg_pairwise_corr_identical_series():
    idx = pd.bdate_range("2025-01-01", periods=30)
    rng = np.random.default_rng(5)
    base = 100 * np.cumprod(1 + rng.normal(0, 0.01, 30))
    p = pd.DataFrame({f"S{i}": base * (i + 1) for i in range(6)}, index=idx)
    out = rg.avg_pairwise_corr(p, window=20, min_names=5)
    assert out.iloc[-1] == pytest.approx(1.0)
    assert out.iloc[:20].isna().all()


def test_breadth_above_ma():
    idx = pd.bdate_range("2025-01-01", periods=3)
    p = pd.DataFrame({"A": [1.0, 1.0, 2.0], "B": [3.0, 3.0, 1.0]}, index=idx)
    out = rg.breadth_above_ma(p, window=2)
    assert np.isnan(out.iloc[0])
    assert out.iloc[2] == pytest.approx(0.5)


def test_rolling_percentile_and_change():
    s = pd.Series([1.0, 2.0, 3.0, 4.0])
    assert rg.rolling_percentile(s, window=4).iloc[-1] == pytest.approx(1.0)
    assert rg.rolling_percentile(s[::-1].reset_index(drop=True), window=4).iloc[-1] == pytest.approx(0.25)
    assert rg.change(s, periods=2).iloc[-1] == pytest.approx(2.0)


def test_points_and_classification():
    flags = pd.DataFrame({"a": [0, 1, 1, 1, 1, 1], "b": [0, 0, 1, 1, 1, 1], "c": [0, 0, 0, 1, 1, 1],
                          "d": [0, 0, 0, 0, 1, 1], "e": [np.nan, 0, 0, 0, 0, 1]})
    pts = rg.regime_points(flags)
    assert list(pts) == [0, 1, 2, 3, 4, 5]
    assert list(rg.classify_regime(pts)) == ["normal", "normal", "elevated", "elevated", "stressed", "stressed"]
