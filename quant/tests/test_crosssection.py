import numpy as np
import pandas as pd
import pytest

from quant import crosssection as cs

IDX = pd.to_datetime(["2025-01-02", "2025-01-03"])


def test_zscore_cs():
    df = pd.DataFrame({"A": [1.0, 5.0], "B": [2.0, np.nan], "C": [3.0, np.nan]}, index=IDX)
    out = cs.zscore_cs(df)
    assert list(out.iloc[0]) == pytest.approx([-1.0, 0.0, 1.0])
    assert out.iloc[1].isna().all()


def test_zscore_cs_zero_std_is_nan():
    df = pd.DataFrame({"A": [2.0], "B": [2.0], "C": [2.0]}, index=IDX[:1])
    assert cs.zscore_cs(df).isna().all().all()


def test_winsorize_cs_clips_outlier_to_band():
    row = [0.0] * 20 + [100.0]
    df = pd.DataFrame([row], index=IDX[:1], columns=[f"S{i}" for i in range(21)])
    out = cs.winsorize_cs(df, n_sigma=3.0)
    arr = np.array(row)
    upper = arr.mean() + 3 * arr.std(ddof=1)
    assert out.iloc[0, -1] == pytest.approx(upper)
    assert out.iloc[0, 0] == pytest.approx(0.0)


def test_winsorize_cs_leaves_tiny_rows():
    df = pd.DataFrame({"A": [5.0], "B": [np.nan]}, index=IDX[:1])
    pd.testing.assert_frame_equal(cs.winsorize_cs(df), df)


def test_rank_pct_cs_averages_ties():
    df = pd.DataFrame({"A": [10.0], "B": [20.0], "C": [20.0], "D": [30.0]}, index=IDX[:1])
    assert list(cs.rank_pct_cs(df).iloc[0]) == pytest.approx([0.25, 0.625, 0.625, 1.0])


def test_neutralize_groups():
    df = pd.DataFrame({"A": [1.0], "B": [3.0], "C": [10.0], "D": [7.0]}, index=IDX[:1])
    groups = pd.Series({"A": "tech", "B": "tech", "C": "energy"})
    out = cs.neutralize_groups(df, groups)
    assert list(out.iloc[0]) == pytest.approx([-1.0, 1.0, 0.0, 0.0])


def test_residualize_cs_removes_linear_part():
    rng = np.random.default_rng(3)
    cols = [f"S{i}" for i in range(30)]
    x = pd.DataFrame(rng.normal(size=(2, 30)), index=IDX, columns=cols)
    noise = pd.DataFrame(rng.normal(scale=0.1, size=(2, 30)), index=IDX, columns=cols)
    y = 2.0 + 3.0 * x + noise
    res = cs.residualize_cs(y, {"x": x})
    for t in IDX:
        r = res.loc[t].to_numpy()
        assert abs(r.mean()) < 1e-10
        assert abs(np.corrcoef(r, x.loc[t].to_numpy())[0, 1]) < 1e-8
        assert np.std(r) < 0.2


def test_residualize_cs_too_few_names_is_nan():
    y = pd.DataFrame({"A": [1.0], "B": [2.0]}, index=IDX[:1])
    x = pd.DataFrame({"A": [0.5], "B": [1.0]}, index=IDX[:1])
    assert cs.residualize_cs(y, {"x": x}).isna().all().all()


def test_residualize_cs_missing_regressor_excludes_name():
    rng = np.random.default_rng(4)
    cols = [f"S{i}" for i in range(10)]
    x = pd.DataFrame(rng.normal(size=(1, 10)), index=IDX[:1], columns=cols)
    y = pd.DataFrame(rng.normal(size=(1, 10)), index=IDX[:1], columns=cols)
    x.iloc[0, 0] = np.nan
    res = cs.residualize_cs(y, {"x": x})
    assert np.isnan(res.iloc[0, 0])
    assert res.iloc[0, 1:].notna().all()
