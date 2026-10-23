"""SD1 · Reporting: assemble the contract RunOutput from the pipeline's parts."""

from __future__ import annotations

import pandas as pd

DISCLAIMER = (
    "Research and education only. Tiers are research stances, not orders or investment advice. "
    "TradePulse places no trades. Past performance does not predict future results."
)
LONG = ("STRONG_OVERWEIGHT", "OVERWEIGHT")
SHORT = ("UNDERWEIGHT", "AVOID")


def new_run_id(as_of: str, token: str) -> str:
    """f"{as_of}-{token}" lower-cased, e.g. 2026-10-21-a1b2c3d4. token is 8 hex chars; anything
    else raises ValueError. The result matches ^[a-z0-9-]{8,64}$."""
    raise NotImplementedError


def default_invalidation(tier: str, top_factor: str | None) -> list[str]:
    """Deterministic invalidation conditions:
    long tiers  -> ["Composite percentile falls below 0.50",
                    f"Largest driver {top_factor} turns negative"] (second item only with a factor)
    short tiers -> ["Composite percentile rises above 0.50",
                    f"Largest driver {top_factor} turns positive"] (same rule)
    NEUTRAL     -> ["Score moves into the top or bottom 20% of the pool"]
    NO_CALL     -> ["No stance: insufficient factor coverage or composite skill"]"""
    raise NotImplementedError


def default_watch(pool: str) -> list[str]:
    """us_equity -> ["Next earnings release (8-K Item 2.02)", "Moves in linked names"];
    other pools -> ["Moves in linked names", "Pool regime state"]."""
    raise NotImplementedError


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
    raise NotImplementedError


def pool_summary(pool: str, pool_cfg: dict, n_members: int, book: pd.DataFrame, ic_comp: float | None,
                 regime_state: str, as_of_close: str) -> dict:
    """Contract PoolSummary: label and benchmark from pool_cfg, n_ranked = rows whose tier is not
    NO_CALL, composite_ic rounded to 6 decimals (None stays None)."""
    raise NotImplementedError


def empty_track_record(window: dict) -> dict:
    """Contract TrackRecord with mode walk_forward, the given window, zero counts and empty lists."""
    raise NotImplementedError


def run_output(*, run_id: str, created_at: str, as_of: str, data_mode: str, sample_mode: bool,
               horizon: int, request: dict, pools: list[dict], recommendations: list[dict],
               factor_cards: list[dict], regimes: list[dict], explanations: list[dict],
               track_record: dict, warnings: list[str], trace_path: str) -> dict:
    """Assemble RunOutput (schema_version "1.0", disclaimer = DISCLAIMER), validate it with
    tradepulse.contracts.assert_payload and return it."""
    raise NotImplementedError
