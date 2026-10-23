"""SD1 · Reporting: assemble the contract RunOutput from the pipeline's parts."""

from __future__ import annotations

import re
from copy import deepcopy

import pandas as pd

from tradepulse.contracts import assert_payload

DISCLAIMER = (
    "Research and education only. Tiers are research stances, not orders or investment advice. "
    "TradePulse places no trades. Past performance does not predict future results."
)
LONG = ("STRONG_OVERWEIGHT", "OVERWEIGHT")
SHORT = ("UNDERWEIGHT", "AVOID")


def new_run_id(as_of: str, token: str) -> str:
    """f"{as_of}-{token}" lower-cased, e.g. 2026-10-21-a1b2c3d4. token is 8 hex chars; anything
    else raises ValueError. The result matches ^[a-z0-9-]{8,64}$."""
    if not isinstance(token, str) or re.fullmatch(r"[0-9a-fA-F]{8}", token) is None:
        raise ValueError("token must contain exactly 8 hexadecimal characters")
    run_id = f"{as_of}-{token}".lower()
    if re.fullmatch(r"[a-z0-9-]{8,64}", run_id) is None:
        raise ValueError("run ID must contain 8 to 64 lowercase letters, digits or hyphens")
    return run_id


def default_invalidation(tier: str, top_factor: str | None) -> list[str]:
    """Deterministic invalidation conditions:
    long tiers  -> ["Composite percentile falls below 0.50",
                    f"Largest driver {top_factor} turns negative"] (second item only with a factor)
    short tiers -> ["Composite percentile rises above 0.50",
                    f"Largest driver {top_factor} turns positive"] (same rule)
    NEUTRAL     -> ["Score moves into the top or bottom 20% of the pool"]
    NO_CALL     -> ["No stance: insufficient factor coverage or composite skill"]"""
    if tier in LONG:
        conditions = ["Composite percentile falls below 0.50"]
        if top_factor is not None:
            conditions.append(f"Largest driver {top_factor} turns negative")
        return conditions
    if tier in SHORT:
        conditions = ["Composite percentile rises above 0.50"]
        if top_factor is not None:
            conditions.append(f"Largest driver {top_factor} turns positive")
        return conditions
    if tier == "NEUTRAL":
        return ["Score moves into the top or bottom 20% of the pool"]
    if tier == "NO_CALL":
        return ["No stance: insufficient factor coverage or composite skill"]
    raise ValueError(f"unknown tier {tier!r}")


def default_watch(pool: str) -> list[str]:
    """us_equity -> ["Next earnings release (8-K Item 2.02)", "Moves in linked names"];
    other pools -> ["Moves in linked names", "Pool regime state"]."""
    if pool == "us_equity":
        return ["Next earnings release (8-K Item 2.02)", "Moves in linked names"]
    return ["Moves in linked names", "Pool regime state"]


def _number(value: float | None) -> float | None:
    """Convert a nullable numeric scalar to a plain Python value."""
    return None if pd.isna(value) else float(value)


def recommendation_rows(pool: str, book: pd.DataFrame, meta: pd.DataFrame, last_close: pd.Series,
                        ret_1d: pd.Series, horizon: int, valuation: pd.Series | None,
                        explanations: dict[str, dict]) -> list[dict]:
    """One contract Recommendation per row of book, in rank order.

    book (index = symbol) has score, coverage, contributions, rank, percentile, expected_alpha_bps,
    cost_bps_round_trip, net_edge_bps, tier and optionally regime_adjusted (default False).
    meta (index = symbol) has name and sector. explanations maps symbol ->
    {"explanation": Explanation, "what_to_watch": [str]}.
    - NaN/None numbers -> None; all numbers are plain Python float/int (never numpy types).
    - top_factor = factor with the largest abs(contribution) (None when there is none).
    - invalidation = default_invalidation(tier, top_factor).
    - what_to_watch = the explanation's what_to_watch when non-empty, else default_watch(pool).
    - explanation_id = the explanation's explanation_id or None.
    - valuation_pctile from valuation (None when valuation is None or missing).
    - A symbol without last_close is skipped (cannot be shown honestly); ret_1d missing -> 0.0 is
      NOT allowed: such a row is skipped too.
    """
    rows = []
    for symbol, row in book.sort_values("rank", kind="stable").iterrows():
        close, daily_return = _number(last_close.get(symbol)), _number(ret_1d.get(symbol))
        if close is None or daily_return is None:
            continue
        contributions = [
            {"factor": str(item["factor"]), "z": _number(item["z"]),
             "weight": _number(item["weight"]), "contribution": _number(item["contribution"])}
            for item in row["contributions"]
        ]
        drivers = [item for item in contributions if item["contribution"] is not None]
        top_factor = (max(drivers, key=lambda item: abs(item["contribution"]))["factor"]
                      if drivers else None)
        details = explanations.get(symbol, {})
        explanation = details.get("explanation") or {}
        tier = str(row["tier"])
        rows.append({
            "pool": pool, "symbol": str(symbol), "name": str(meta.at[symbol, "name"]),
            "sector": str(meta.at[symbol, "sector"]),
            "rank": None if pd.isna(row["rank"]) else int(row["rank"]),
            "percentile": _number(row["percentile"]), "score": _number(row["score"]),
            "coverage": _number(row["coverage"]), "tier": tier,
            "expected_alpha_bps": _number(row["expected_alpha_bps"]),
            "cost_bps_round_trip": _number(row["cost_bps_round_trip"]),
            "net_edge_bps": _number(row["net_edge_bps"]), "horizon_days": int(horizon),
            "contributions": contributions,
            "valuation_pctile": None if valuation is None else _number(valuation.get(symbol)),
            "regime_adjusted": bool(row.get("regime_adjusted", False)),
            "invalidation": default_invalidation(tier, top_factor),
            "what_to_watch": list(details.get("what_to_watch") or default_watch(pool)),
            "explanation_id": explanation.get("explanation_id") or None,
            "last_close": close, "ret_1d": daily_return,
        })
    return rows


def pool_summary(pool: str, pool_cfg: dict, n_members: int, book: pd.DataFrame, ic_comp: float | None,
                 regime_state: str, as_of_close: str) -> dict:
    """Contract PoolSummary: label and benchmark from pool_cfg, n_ranked = rows whose tier is not
    NO_CALL, composite_ic rounded to 6 decimals (None stays None)."""
    composite_ic = _number(ic_comp)
    return {"pool": pool, "label": pool_cfg["label"], "benchmark": pool_cfg["benchmark"],
            "n_members": int(n_members), "n_ranked": int((book["tier"] != "NO_CALL").sum()),
            "composite_ic": None if composite_ic is None else round(composite_ic, 6),
            "regime_state": regime_state, "as_of_close": as_of_close}


def empty_track_record(window: dict) -> dict:
    """Contract TrackRecord with mode walk_forward, the given window, zero counts and empty lists."""
    return {"mode": "walk_forward", "window": deepcopy(window), "settled_count": 0,
            "pending_count": 0, "by_tier": [], "calibration": [], "composite_ic_series": []}


def run_output(*, run_id: str, created_at: str, as_of: str, data_mode: str, sample_mode: bool,
               horizon: int, request: dict, pools: list[dict], recommendations: list[dict],
               factor_cards: list[dict], regimes: list[dict], explanations: list[dict],
               track_record: dict, warnings: list[str], trace_path: str) -> dict:
    """Assemble RunOutput (schema_version "1.0", disclaimer = DISCLAIMER), validate it with
    tradepulse.contracts.assert_payload and return it."""
    output = deepcopy({
        "schema_version": "1.0", "run_id": run_id, "created_at": created_at, "as_of": as_of,
        "data_mode": data_mode, "sample_mode": sample_mode, "horizon_days": horizon,
        "request": request, "pools": pools, "recommendations": recommendations,
        "factor_cards": factor_cards, "regimes": regimes, "explanations": explanations,
        "track_record": track_record, "warnings": warnings, "trace_path": trace_path,
        "disclaimer": DISCLAIMER,
    })
    assert_payload(output)
    return output
