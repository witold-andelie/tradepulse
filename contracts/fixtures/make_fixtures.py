"""Generate SYNTHETIC fixtures that satisfy contracts/api/tradepulse.schema.json.

The fixtures exist only so the web app and tests can be built before the engine runs.
Every symbol and company name is fictional (SYN###, SYE##.XX, SYC##-USD), the data_mode is
SYNTHETIC, and the web app must show a banner. Never present these numbers as results.

    py -3 contracts/fixtures/make_fixtures.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED = 20261022
AS_OF = dt.date(2026, 10, 21)
RUN_ID = "synthetic-fixture-0001"
HORIZON = 5

POOLS = {
    "us_equity": {"label": "US equities", "benchmark": "SPY", "n": 520, "cost": 5.0, "filings": True},
    "eu_equity": {"label": "European equities", "benchmark": "^STOXX50E", "n": 60, "cost": 8.0, "filings": False},
    "crypto": {"label": "Crypto", "benchmark": "BTC-USD", "n": 40, "cost": 15.0, "filings": False},
}
EQUITY_SECTORS = [
    "Information Technology", "Health Care", "Financials", "Consumer Discretionary",
    "Communication Services", "Industrials", "Consumer Staples", "Energy", "Utilities",
    "Real Estate", "Materials",
]
CRYPTO_SECTORS = ["layer-1", "layer-2", "defi", "payments", "exchange-token", "oracle", "meme"]
FACTORS = {
    "pv_mom_12_1": ("12-1 month momentum", "12-month trend, skipping the last month", False),
    "pv_mom_1m": ("1-month momentum", "1-month trend", False),
    "pv_rev_5d": ("5-day reversal", "short-term reversal", False),
    "pv_lowvol_20d": ("Low volatility", "low-volatility premium", False),
    "pv_volume_z": ("Volume z-score", "abnormal trading activity", False),
    "pv_dist_52w_high": ("Distance to 52-week high", "anchoring to the 52-week high", False),
    "att_pageviews": ("Wikipedia attention", "abnormal public attention, residual vs price-volume", False),
    "earn_sue": ("Earnings surprise (SUE)", "standardised unexpected earnings", True),
    "earn_demand_language": ("Demand language", "management statements that demand exceeds supply", True),
    "evt_drift": ("Event drift", "post-event drift after 8-K events", True),
    "rel_spillover": ("Relational spillover", "shocks at linked companies not yet priced", False),
}
GATE_NAMES = ["measure", "incremental", "predictive", "net_of_cost", "consistency"]
DISCLAIMER = (
    "SYNTHETIC FIXTURE for interface development. Fictional instruments, generated numbers. "
    "Not a result, not investment advice."
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _symbols(pool: str, n: int) -> list[str]:
    if pool == "us_equity":
        return [f"SYN{i:03d}" for i in range(1, n + 1)]
    if pool == "eu_equity":
        return [f"SYE{i:02d}.XX" for i in range(1, n + 1)]
    return [f"SYC{i:02d}-USD" for i in range(1, n + 1)]


def _factor_card(rng: np.random.Generator, factor: str, pool: str, filings: bool) -> dict:
    title, measures, needs_filings = FACTORS[factor]
    start = (AS_OF - dt.timedelta(days=365)).isoformat()
    if needs_filings and not filings:
        status, coverage = "INSUFFICIENT_DATA", 0.0
        passed = [False, None, None, None, None]
    else:
        coverage = float(np.round(rng.uniform(0.65, 0.99), 3))
        passed = [True] + [bool(rng.random() > 0.3) for _ in range(4)]
        status = "ACTIVE" if all(passed) else "MEASURED_ONLY"
    thresholds = [0.60, 2.0, 0.0, 0.5, None]
    values = [coverage, float(np.round(rng.normal(1.8, 1.0), 2)), float(np.round(rng.normal(0.02, 0.02), 4)),
              float(np.round(rng.normal(0.6, 0.5), 2)), None]
    gates = []
    for i, name in enumerate(GATE_NAMES):
        gates.append({
            "gate": f"G{i + 1}", "name": name, "passed": passed[i],
            "value": values[i] if passed[i] is not None else None,
            "threshold": thresholds[i], "note": "synthetic" if passed[i] is not None else "not evaluated",
        })
    ic = [] if status == "INSUFFICIENT_DATA" else [
        {"horizon_days": h, "mean_ic": float(np.round(rng.normal(0.02, 0.015) / np.sqrt(h) ** 0.3, 4)),
         "t_stat": float(np.round(rng.normal(1.8, 0.8), 2)), "n": int(250 // h)}
        for h in (1, 5, 20)
    ]
    return {
        "factor": factor, "pool": pool, "title": title, "measures": measures,
        "definition": "See docs/architecture/factors.md", "sources": ["synthetic"],
        "availability": "close t (synthetic)", "status": status, "weight": 0.0,
        "coverage": coverage, "gates": gates, "ic_decay": ic,
        "same_day_ic": None if not ic else float(np.round(rng.normal(0.05, 0.03), 4)),
        "mostly_descriptive": False,
        "long_short": {k: (None if not ic else float(np.round(rng.normal(m, s), 4))) for k, m, s in [
            ("gross_ann_return", 0.08, 0.05), ("net_ann_return", 0.05, 0.05), ("net_sharpe", 0.6, 0.4),
            ("turnover_per_rebalance", 0.8, 0.2), ("max_drawdown", -0.08, 0.03)]},
        "evaluation_mode": "in_sample_research",
        "window": {"start": start, "end": AS_OF.isoformat()},
    }


def _tier(pct: float, net: float | None, cost_rt: float) -> str:
    if net is None:
        return "NO_CALL"
    if pct >= 0.95 and net >= 2 * cost_rt:
        return "STRONG_OVERWEIGHT"
    if pct >= 0.80 and net >= cost_rt:
        return "OVERWEIGHT"
    if pct <= 0.05 and net <= -2 * cost_rt:
        return "AVOID"
    if pct <= 0.20 and net <= -cost_rt:
        return "UNDERWEIGHT"
    return "NEUTRAL"


def build() -> tuple[dict, list[dict]]:
    rng = np.random.default_rng(SEED)
    pools, recs, cards, regimes, explanations = [], [], [], [], []
    states = {"us_equity": "normal", "eu_equity": "elevated", "crypto": "stressed"}

    for pool, meta in POOLS.items():
        pool_cards = [_factor_card(rng, f, pool, meta["filings"]) for f in FACTORS]
        active = [c for c in pool_cards if c["status"] == "ACTIVE"] or pool_cards[:1]
        raw_w = rng.uniform(0.5, 1.5, len(active))
        for card, w in zip(active, raw_w / raw_w.sum()):
            card["weight"] = float(np.round(w, 4))
            if card["status"] != "ACTIVE":
                card["status"] = "ACTIVE"
                card["gates"] = [dict(g, passed=True, note="synthetic") for g in card["gates"]]
        cards.extend(pool_cards)
        weights = {c["factor"]: c["weight"] for c in pool_cards if c["weight"] > 0}

        symbols = _symbols(pool, meta["n"])
        sectors = CRYPTO_SECTORS if pool == "crypto" else EQUITY_SECTORS
        rows = []
        for sym in symbols:
            z = {f: (None if rng.random() < 0.08 else float(np.round(rng.normal(), 3))) for f in weights}
            contribs = [{"factor": f, "z": z[f], "weight": w,
                         "contribution": float(np.round(w * (z[f] or 0.0), 6))} for f, w in weights.items()]
            score = float(np.round(sum(c["contribution"] for c in contribs), 6))
            coverage = float(np.round(sum(w for f, w in weights.items() if z[f] is not None), 4))
            rows.append((sym, score, coverage, contribs))
        rows.sort(key=lambda r: r[1], reverse=True)
        n = len(rows)
        cost_rt = 2 * meta["cost"]
        ic_comp = float(np.round(rng.uniform(0.06, 0.12), 4))
        for rank, (sym, score, coverage, contribs) in enumerate(rows, start=1):
            pct = float(np.round((n - rank + 1) / n, 6))
            sigma = rng.uniform(0.01, 0.04 if pool == "crypto" else 0.025)
            alpha = float(np.round(ic_comp * sigma * np.sqrt(HORIZON) * score * 1e4, 2))
            net = None if coverage < 0.5 else float(np.round(np.sign(alpha) * (abs(alpha) - cost_rt), 2))
            tier = _tier(pct, net, cost_rt)
            adjusted = False
            if states[pool] == "elevated" and tier == "STRONG_OVERWEIGHT":
                tier, adjusted = "OVERWEIGHT", True
            if states[pool] == "stressed" and tier in ("STRONG_OVERWEIGHT", "OVERWEIGHT"):
                tier, adjusted = ("OVERWEIGHT" if tier == "STRONG_OVERWEIGHT" else "NEUTRAL"), True
            idx = int(sym[3:6].rstrip(".-") or 0) if pool == "us_equity" else int(sym[3:5])
            recs.append({
                "pool": pool, "symbol": sym, "name": f"Synthetic {pool.split('_')[0].upper()} {idx:03d}",
                "sector": sectors[idx % len(sectors)], "rank": rank, "percentile": pct, "score": score,
                "coverage": coverage, "tier": tier,
                "expected_alpha_bps": None if net is None else alpha, "cost_bps_round_trip": cost_rt,
                "net_edge_bps": net, "horizon_days": HORIZON, "contributions": contribs,
                "valuation_pctile": float(np.round(rng.random(), 3)) if pool == "us_equity" else None,
                "regime_adjusted": adjusted,
                "invalidation": ["Close below the 50-day moving average", "Composite score falls below the pool median"],
                "what_to_watch": ["Next earnings release", "Moves in linked names"],
                "explanation_id": None,
                "last_close": float(np.round(rng.uniform(5, 900), 2)),
                "ret_1d": float(np.round(rng.normal(0, 0.02), 4)),
            })

        focus = [r for r in recs if r["pool"] == pool and (r["rank"] <= 5 or r["rank"] > n - 5)]
        for i, r in enumerate(focus):
            eid = f"exp-{pool}-{r['symbol'].lower()}"
            r["explanation_id"] = eid
            abstain = i % 4 == 3
            evidence = {
                "evidence_id": f"ev-{eid}-1", "query_template": "factor_contributions",
                "params": {"symbol": r["symbol"], "as_of": AS_OF.isoformat()},
                "rows_sha256": _sha(eid), "source_table": "factor_value",
                "as_of": AS_OF.isoformat(), "url": None,
            }
            claims = [{
                "claim_id": f"{eid}-c1",
                "text": f"{r['symbol']} ranks {r['rank']} of {n}; the largest contribution comes from "
                        f"{max(r['contributions'], key=lambda c: abs(c['contribution']))['factor']}.",
                "kind": "factor", "evidence": [evidence], "status": "verified",
                "checks": [{"name": "rerun_hash_match", "passed": True, "detail": "synthetic"},
                           {"name": "contributions_sum", "passed": True, "detail": "synthetic"},
                           {"name": "no_future_data", "passed": True, "detail": "synthetic"}],
            }, {
                "claim_id": f"{eid}-c2", "text": "A linked supplier reported a capacity constraint.",
                "kind": "relation", "evidence": [dict(evidence, evidence_id=f"ev-{eid}-2", rows_sha256=_sha(eid + '2'))],
                "status": "rejected" if abstain else "verified",
                "checks": [{"name": "cause_before_move", "passed": not abstain,
                            "detail": "synthetic: event dated after the move" if abstain else "synthetic"}],
            }]
            explanations.append({
                "explanation_id": eid, "pool": pool, "symbol": r["symbol"],
                "verdict": "abstained" if abstain else "explained",
                "summary": "Synthetic explanation for interface development.",
                "claims": claims,
                "counter_case": ["Part of the move may already be priced in.", "Sector-wide flows could explain the score."],
                "ruled_out": ["Index rebalancing (no membership change in the window)."],
                "models": {"analyst": "synthetic-analyst", "skeptic": "synthetic-skeptic"},
                "retries": int(abstain) * 2,
            })

        points = {"normal": 1, "elevated": 3, "stressed": 4}[states[pool]]
        names = ["trend", "volatility", "correlation", "breadth", "credit"]
        regimes.append({
            "pool": pool, "as_of": AS_OF.isoformat(), "points": points, "state": states[pool],
            "indicators": [{"name": nm, "value": float(np.round(rng.random(), 3)), "threshold": 0.5,
                            "triggered": i < points, "note": "synthetic"} for i, nm in enumerate(names)],
            "history": [{"date": (AS_OF - dt.timedelta(days=d)).isoformat(),
                         "points": int(min(5, max(0, points + rng.integers(-1, 2)))),
                         "state": states[pool]} for d in range(30, -1, -1)],
            "lift": {"drawdown_threshold": 0.2 if pool == "crypto" else 0.07, "horizon_days": 20,
                     "lift_elevated": 1.4, "lift_stressed": 2.1, "n_days": 250},
        })
        for h in regimes[-1]["history"]:
            p = h["points"]
            h["state"] = "normal" if p <= 1 else "elevated" if p <= 3 else "stressed"
        pools.append({
            "pool": pool, "label": meta["label"], "benchmark": meta["benchmark"], "n_members": n,
            "n_ranked": sum(1 for r in recs if r["pool"] == pool and r["tier"] != "NO_CALL"),
            "composite_ic": ic_comp, "regime_state": states[pool], "as_of_close": AS_OF.isoformat(),
        })

    tiers = ["STRONG_OVERWEIGHT", "OVERWEIGHT", "NEUTRAL", "UNDERWEIGHT", "AVOID"]
    track = {
        "mode": "walk_forward",
        "window": {"start": (AS_OF - dt.timedelta(days=365)).isoformat(), "end": AS_OF.isoformat()},
        "settled_count": 1200, "pending_count": 40,
        "by_tier": [{"pool": p, "tier": t, "n": int(rng.integers(10, 200)),
                     "hit_rate": float(np.round(rng.uniform(0.45, 0.6), 3)),
                     "mean_excess_bps": float(np.round(rng.normal(0, 30), 1))} for p in POOLS for t in tiers],
        "calibration": [{"bucket_low": b / 5, "bucket_high": (b + 1) / 5, "n": int(rng.integers(20, 120)),
                         "predicted": (b + 0.5) / 5,
                         "observed": float(np.round(min(1, max(0, (b + 0.5) / 5 + rng.normal(0, 0.05))), 3))}
                        for b in range(5)],
        "composite_ic_series": [{"date": (AS_OF - dt.timedelta(days=7 * w)).isoformat(), "pool": p,
                                 "ic": float(np.round(rng.normal(0.03, 0.05), 4))}
                                for p in POOLS for w in range(52, -1, -1)],
    }
    output = {
        "schema_version": "1.0", "run_id": RUN_ID, "created_at": "2026-10-22T08:00:00Z",
        "as_of": AS_OF.isoformat(), "data_mode": "SYNTHETIC", "sample_mode": True,
        "horizon_days": HORIZON,
        "request": {"as_of": AS_OF.isoformat(), "pools": list(POOLS), "tickers": [], "horizon_days": HORIZON, "top_k": 5},
        "pools": pools, "recommendations": recs, "factor_cards": cards, "regimes": regimes,
        "explanations": explanations, "track_record": track,
        "warnings": ["SYNTHETIC FIXTURE: fictional instruments and generated numbers."],
        "trace_path": f"logs/trace-{RUN_ID}.jsonl", "disclaimer": DISCLAIMER,
    }

    nodes = ["guard_request", "settle", "extract_link", "research_factors", "assess_regime", "rank",
             "explain", "verify", "report"]
    trace, seq, t = [], 0, dt.datetime(2026, 10, 22, 8, 0, 0, tzinfo=dt.timezone.utc)
    for node in nodes:
        for kind in ("node_start", "node_end"):
            dur = int(rng.integers(50, 4000)) if kind == "node_end" else None
            trace.append({
                "ts": t.isoformat().replace("+00:00", "Z"), "run_id": RUN_ID, "seq": seq, "node": node,
                "kind": kind, "status": "ok", "duration_ms": dur,
                "model": "synthetic-analyst" if node == "explain" and kind == "node_end" else None,
                "tokens_in": 1200 if node == "explain" and kind == "node_end" else None,
                "tokens_out": 300 if node == "explain" and kind == "node_end" else None,
                "data_mode": "SYNTHETIC", "message": f"{node} {kind.split('_')[1]}", "payload": {},
            })
            seq += 1
            t += dt.timedelta(milliseconds=dur or 5)
        if node == "verify":
            trace.append({
                "ts": t.isoformat().replace("+00:00", "Z"), "run_id": RUN_ID, "seq": seq, "node": node,
                "kind": "retry", "status": "ok", "duration_ms": None, "model": None, "tokens_in": None,
                "tokens_out": None, "data_mode": "SYNTHETIC",
                "message": "claim rejected (cause_before_move); returned to explain, retry 1 of 2",
                "payload": {"claim_id": "synthetic"},
            })
            seq += 1
    return output, trace


def main() -> None:
    output, trace = build()
    (HERE / "run_output.fixture.json").write_text(json.dumps(output, separators=(",", ":")) + "\n", encoding="utf-8")
    with (HERE / "trace.fixture.jsonl").open("w", encoding="utf-8") as fh:
        for event in trace:
            fh.write(json.dumps(event) + "\n")
    print(f"wrote {len(output['recommendations'])} recommendations, {len(trace)} trace events")


if __name__ == "__main__":
    main()
