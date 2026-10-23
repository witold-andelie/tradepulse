import pandas as pd
import pytest

from tradepulse.config import load_config
from tradepulse.contracts import validate_payload
from tradepulse.regime import classify, drawdown_lift, regime_state

CFG = load_config()["regime"]


@pytest.mark.parametrize("points, state", [(0, "normal"), (1, "normal"), (2, "elevated"), (3, "elevated"),
                                           (4, "stressed"), (5, "stressed")])
def test_classify(points, state):
    assert classify(points, CFG) == state


def test_regime_state_contract():
    ind = {
        "trend": {"value": 0.97, "threshold": 1.0, "triggered": True, "note": "SPY below 200-day MA"},
        "volatility": {"value": 1.05, "threshold": 1.0, "triggered": True, "note": "VIX/VIX3M inverted"},
        "correlation": {"value": 0.5, "threshold": 0.9, "triggered": False, "note": "pctile 0.50"},
        "breadth": {"value": None, "threshold": 0.4, "triggered": None, "note": "insufficient history"},
    }
    hist = pd.Series([0, 1, 2], index=pd.to_datetime(["2026-10-17", "2026-10-20", "2026-10-21"]))
    st = regime_state("us_equity", "2026-10-21", ind, hist, None, CFG)
    assert validate_payload(st, "RegimeState") == []
    assert st["points"] == 2 and st["state"] == "elevated"
    names = [i["name"] for i in st["indicators"]]
    assert names == ["trend", "volatility", "correlation", "breadth", "credit"]
    credit = st["indicators"][-1]
    assert credit["triggered"] is None and credit["note"] == "not available"
    assert st["history"] == [{"date": "2026-10-17", "points": 0, "state": "normal"},
                             {"date": "2026-10-20", "points": 1, "state": "normal"},
                             {"date": "2026-10-21", "points": 2, "state": "elevated"}]


def test_drawdown_lift():
    idx = pd.bdate_range("2026-01-05", periods=8)
    bench = pd.Series([100, 100, 89, 100, 100, 100, 100, 100], index=idx, dtype=float)
    points = pd.Series([4, 1, 2, 0, 0, 2, 0, 0], index=idx)
    out = drawdown_lift(points, bench, CFG, horizon=2, threshold=0.10)
    assert out["n_days"] == 6
    assert out["lift_stressed"] == pytest.approx(3.0)
    assert out["lift_elevated"] == pytest.approx(0.0)
    assert out["drawdown_threshold"] == 0.10 and out["horizon_days"] == 2


def test_drawdown_lift_without_events():
    idx = pd.bdate_range("2026-01-05", periods=6)
    out = drawdown_lift(pd.Series([4] * 6, index=idx), pd.Series(100.0, index=idx), CFG, horizon=2, threshold=0.1)
    assert out["lift_stressed"] is None and out["lift_elevated"] is None
