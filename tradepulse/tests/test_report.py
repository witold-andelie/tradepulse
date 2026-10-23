import json

import numpy as np
import pandas as pd
import pytest

from tradepulse.config import load_config
from tradepulse.contracts import CONTRACTS_DIR, ContractError
from tradepulse.report import (DISCLAIMER, default_invalidation, default_watch, empty_track_record, new_run_id,
                               pool_summary, recommendation_rows, run_output)

FIX = json.loads((CONTRACTS_DIR / "fixtures" / "run_output.fixture.json").read_text(encoding="utf-8"))
CONTRIB = [{"factor": "pv_mom_1m", "z": 1.0, "weight": 0.6, "contribution": 0.6},
           {"factor": "att_pageviews", "z": -2.0, "weight": 0.4, "contribution": -0.8}]


def _book():
    return pd.DataFrame({
        "score": [-0.2, 0.1, 0.0], "coverage": [1.0, 0.9, 0.3],
        "contributions": [CONTRIB, CONTRIB[:1], []],
        "rank": [1, 2, 3], "percentile": [1.0, 2 / 3, 1 / 3],
        "expected_alpha_bps": [np.float64(25.0), 12.5, np.nan], "cost_bps_round_trip": 10.0,
        "net_edge_bps": [15.0, 2.5, None], "tier": ["OVERWEIGHT", "NEUTRAL", "NO_CALL"],
        "regime_adjusted": [True, False, False],
    }, index=["AAA", "BBB", "CCC"])


def test_run_id():
    assert new_run_id("2026-10-21", "A1B2C3D4") == "2026-10-21-a1b2c3d4"
    with pytest.raises(ValueError):
        new_run_id("2026-10-21", "xyz")


def test_defaults():
    assert default_invalidation("OVERWEIGHT", "pv_mom_1m") == [
        "Composite percentile falls below 0.50", "Largest driver pv_mom_1m turns negative"]
    assert default_invalidation("AVOID", None) == ["Composite percentile rises above 0.50"]
    assert default_invalidation("NEUTRAL", "x") == ["Score moves into the top or bottom 20% of the pool"]
    assert default_invalidation("NO_CALL", "x") == ["No stance: insufficient factor coverage or composite skill"]
    assert default_watch("us_equity")[0].startswith("Next earnings release")
    assert default_watch("crypto") == ["Moves in linked names", "Pool regime state"]


def test_recommendation_rows():
    meta = pd.DataFrame({"name": ["Alpha", "Beta", "Gamma"], "sector": ["Tech", "Energy", "Tech"]},
                        index=["AAA", "BBB", "CCC"])
    exp = {"AAA": {"explanation": {"explanation_id": "exp-us_equity-aaa"}, "what_to_watch": ["Supplier guidance"]}}
    rows = recommendation_rows("us_equity", _book(), meta, pd.Series({"AAA": 10.0, "BBB": 20.0, "CCC": 5.0}),
                               pd.Series({"AAA": 0.01, "BBB": -0.02}), 5, pd.Series({"AAA": 0.4}), exp)
    assert [r["symbol"] for r in rows] == ["AAA", "BBB"]  # CCC has no 1-day return
    a = rows[0]
    assert a["explanation_id"] == "exp-us_equity-aaa" and a["what_to_watch"] == ["Supplier guidance"]
    assert a["invalidation"][1] == "Largest driver att_pageviews turns negative"
    assert a["regime_adjusted"] is True and a["valuation_pctile"] == 0.4
    assert type(a["expected_alpha_bps"]) is float and type(a["rank"]) is int
    assert rows[1]["valuation_pctile"] is None and rows[1]["explanation_id"] is None
    assert rows[1]["what_to_watch"] == default_watch("us_equity")


def test_run_output_validates_and_rejects():
    cfg = load_config()
    book = _book()
    summary = pool_summary("us_equity", cfg["pools"]["us_equity"], 520, book, 0.0412345678, "normal", "2026-10-21")
    assert summary["n_ranked"] == 2 and summary["composite_ic"] == 0.041235
    window = {"start": "2025-10-21", "end": "2026-10-21"}
    tr = empty_track_record(window)
    args = dict(run_id="2026-10-21-a1b2c3d4", created_at="2026-10-22T08:00:00Z", as_of="2026-10-21",
                data_mode="REPLAY", sample_mode=True, horizon=5,
                request={"as_of": "2026-10-21", "pools": ["us_equity"], "tickers": [], "horizon_days": 5, "top_k": 5},
                pools=[summary], recommendations=[FIX["recommendations"][0]], factor_cards=[FIX["factor_cards"][0]],
                regimes=[FIX["regimes"][0]], explanations=[], track_record=tr, warnings=[],
                trace_path="logs/trace-2026-10-21-a1b2c3d4.jsonl")
    out = run_output(**args)
    assert out["schema_version"] == "1.0" and out["disclaimer"] == DISCLAIMER
    assert out["track_record"]["settled_count"] == 0
    with pytest.raises(ContractError):
        run_output(**dict(args, data_mode="LIVE"))
