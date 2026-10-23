import math

import numpy as np
import pandas as pd
import pytest

from tradepulse.contracts import validate_payload
from tradepulse.research import signals as sg

IDX = pd.bdate_range("2026-10-13", periods=40)  # Tue 2026-10-13 ...
SHA = "a" * 64


def _ev(symbol="A", etype="guidance_raise", direction=1, at="2026-10-15T20:05:00Z", signals=(), sha=SHA):
    return {"event_id": "x" * 24, "doc_sha256": sha, "accession_number": "0000000000-26-000001", "symbol": symbol,
            "event_type": etype, "direction": direction, "counterparty": None, "counterparty_symbol": None,
            "magnitude_usd": None, "novelty": "new", "demand_signals": list(signals), "quote": "q",
            "available_at": at, "extractor_model": "m", "schema_version": "1.0"}


def test_effective_row():
    assert sg.effective_row(IDX, "2026-10-15T20:05:00Z") == 3  # 2026-10-16
    assert sg.effective_row(IDX, pd.Timestamp("2026-10-15 23:00")) == 3
    assert sg.effective_row(IDX, "2026-10-12T10:00:00Z") == 0
    assert sg.effective_row(IDX, "2030-01-01T00:00:00Z") == len(IDX)


def test_sue_panel():
    ends = pd.date_range("2023-03-31", periods=12, freq="QE")
    values = [1, 1, 1, 1, 1.1, 1.2, 1.0, 1.3, 1.2, 1.4, 1.1, 1.6]
    facts = pd.DataFrame({"symbol": "A", "tag": sg.EPS_TAG, "unit": sg.EPS_UNIT, "value": values,
                          "period_start": ends - pd.Timedelta(days=89), "period_end": ends,
                          "filed": ends + pd.Timedelta(days=30)})
    noise = facts.assign(tag="Revenues", unit="USD", value=1e9)
    idx = pd.bdate_range("2023-01-02", "2026-03-31")
    panel = sg.sue_panel(pd.concat([facts, noise]), idx, ["A", "B"], hold=10)
    filed8 = ends[8] + pd.Timedelta(days=30)
    first = idx[idx > filed8][0]
    assert panel.loc[first, "A"] == pytest.approx(0.1 / np.std([0.1, 0.2, 0.0, 0.3], ddof=1))
    assert math.isnan(panel.loc[idx[idx <= filed8][-1], "A"])
    assert panel["B"].isna().all()


def test_event_drift_panel():
    events = [_ev(), _ev(etype="unknown_type_x"), _ev(direction=0), _ev(symbol="ZZZ")]
    panel = sg.event_drift_panel(events, IDX, ["A", "B"], {"guidance_raise": 0.01, "other": 0.5}, window=20, decay=10.0)
    assert math.isnan(panel.loc["2026-10-15", "A"])
    assert panel.loc["2026-10-16", "A"] == pytest.approx(0.01 * math.exp(-0.1))
    assert panel.loc["2026-10-19", "A"] == pytest.approx(0.01 * math.exp(-0.2))
    assert panel["A"].notna().sum() == 20
    assert panel["B"].isna().all()
    two = sg.event_drift_panel([_ev(), _ev(direction=-1, at="2026-10-16T21:00:00Z")], IDX, ["A"], {"guidance_raise": 0.01})
    assert two.loc["2026-10-19", "A"] == pytest.approx(0.01 * math.exp(-0.2) - 0.01 * math.exp(-0.1))


def test_demand_panel():
    pos = [{"type": "demand_exceeds_supply", "polarity": 1, "quote": "q"},
           {"type": "price_increase", "polarity": 1, "quote": "q"}]
    events = [_ev(signals=pos), _ev(signals=[], at="2026-10-15T21:00:00Z"), _ev(symbol="B", signals=[], sha="b" * 64)]
    panel = sg.demand_panel(events, IDX, ["A", "B"], hold=3)
    assert math.isnan(panel.loc["2026-10-15", "A"])
    assert list(panel.loc["2026-10-16":"2026-10-20", "A"]) == pytest.approx([2 / 3] * 3)
    assert math.isnan(panel.loc["2026-10-21", "A"])
    assert panel["B"].isna().all()


def test_event_priors():
    idx = pd.bdate_range("2026-01-05", periods=60)
    a = np.full(60, 100.0)
    # event 1 effective at row 10: +1% per row on rows 10..14
    for k in range(10, 15):
        a[k:] *= 1.01
    # event 2 effective at row 30: -1% per row on rows 30..34
    for k in range(30, 35):
        a[k:] *= 0.99
    prices = pd.DataFrame({"A": a}, index=idx)
    bench = pd.Series(100.0, index=idx)
    at = lambda r: f"{idx[r - 1].date()}T21:00:00Z"  # noqa: E731 - available after the close of row r-1
    events = [_ev(etype="guidance_raise", direction=1, at=at(10)), _ev(etype="guidance_cut", direction=-1, at=at(30)),
              _ev(etype="guidance_raise", direction=1, at=at(50))]
    priors = sg.event_priors(events, prices, bench, train_end=str(idx[45].date()), shrink=20.0)
    assert priors["guidance_raise"] == pytest.approx((1.01 ** 5 - 1) / 21)  # third event is after train_end
    assert priors["guidance_cut"] == pytest.approx(-(0.99 ** 5 - 1) / 21)
    assert set(priors) == {"guidance_raise", "guidance_cut"}


def _market(n=420, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2025-01-01", periods=n)
    rb = rng.normal(0, 0.008, n)
    rl = rng.normal(0, 0.02, n)
    rf = 0.5 * np.concatenate([[0.0], rl[:-1]]) + rng.normal(0, 0.01, n)
    ru = rng.normal(0, 0.02, n)
    prices = pd.DataFrame({"L": 100 * np.cumprod(1 + rl), "F": 50 * np.cumprod(1 + rf),
                           "U": 80 * np.cumprod(1 + ru)}, index=idx)
    return prices, pd.Series(100 * np.cumprod(1 + rb), index=idx)


def test_leader_shocks_no_look_ahead():
    prices, bench = _market()
    z = sg.leader_shocks(prices, bench)
    assert z.shape == prices.shape and z["L"].iloc[-50:].notna().all()
    shocked = prices.copy()
    shocked.iloc[-1] *= 1.3
    pd.testing.assert_frame_equal(z.iloc[:-1], sg.leader_shocks(shocked, bench).iloc[:-1])


def test_spillover_panel():
    prices, bench = _market()
    z = sg.leader_shocks(prices, bench)
    late = str(prices.index[300].date())
    edges = [{"src_symbol": "L", "dst_symbol": "F", "weight": 0.5, "status": "validated", "valid_from": "2025-01-01"},
             {"src_symbol": "L", "dst_symbol": "U", "weight": 0.5, "status": "validated", "valid_from": late},
             {"src_symbol": "U", "dst_symbol": "L", "weight": 0.9, "status": "rejected", "valid_from": "2025-01-01"}]
    panel = sg.spillover_panel(prices, bench, edges, ["F", "U", "L"], prices.index)
    t = prices.index[-1]
    assert panel.loc[t, "F"] == pytest.approx(z["L"].iloc[-2])
    assert panel.loc[prices.index[299], "U"] != panel.loc[prices.index[299], "U"]  # NaN before valid_from
    assert panel.loc[t, "U"] == pytest.approx(z["L"].iloc[-2])
    assert panel["L"].isna().all()  # its only incoming edge is rejected


def test_validate_edges():
    prices, bench = _market()
    seeds = pd.DataFrame({"src_symbol": ["L", "U", "L"], "dst_symbol": ["F", "F", "GHOST"],
                          "relation": ["supplier_of", "peer", "peer"], "weight": [0.6, 0.6, 0.6],
                          "evidence_note": ["h", "h", "h"]})
    out = sg.validate_edges(seeds, prices, bench, train_start=str(prices.index[100].date()),
                            train_end=str(prices.index[-1].date()), as_of=str(prices.index[-1].date()))
    by = {(e["src_symbol"], e["dst_symbol"]): e for e in out}
    for edge in out:
        assert validate_payload(edge, "GraphEdge") == []
    assert by[("L", "F")]["status"] == "validated" and by[("L", "F")]["lead_lag_t"] > 2
    assert by[("U", "F")]["status"] == "rejected"
    assert by[("L", "GHOST")]["status"] == "rejected" and by[("L", "GHOST")]["lead_lag_t"] is None
    assert len(by[("L", "F")]["edge_id"]) == 16
