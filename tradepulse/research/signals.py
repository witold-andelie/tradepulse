"""Raw panels for the filing-based and relational factors (docs/architecture/factors.md).

These raw panels are passed to research.panels.build_pool_panels(extra=...), which standardises
them and residualises them on the price-volume baseline. Every panel is point-in-time: a value at
row t uses only information available before that row's close.

"Effective row" of something available at UTC time T: the first index row whose date is strictly
after T's UTC calendar date. (A filing accepted on 2026-10-15 becomes usable on the next session.)
"""

from __future__ import annotations

import pandas as pd

EPS_TAG = "EarningsPerShareDiluted"
EPS_UNIT = "USD/shares"


def effective_row(index: pd.DatetimeIndex, available_at) -> int:
    """Position of the first row of index whose date is strictly after the UTC date of
    available_at (str ISO, Timestamp or datetime; naive values are treated as UTC).
    Returns len(index) when no such row exists."""
    raise NotImplementedError


def sue_panel(facts: pd.DataFrame, index: pd.DatetimeIndex, symbols: list[str], hold: int = 60) -> pd.DataFrame:
    """earn_sue raw panel from fundamental_fact rows.

    Per symbol: rows with tag == EPS_TAG and unit == EPS_UNIT -> quant.earnings.quarterly_eps ->
    quant.earnings.sue -> events (symbol, available_date = filed, value = sue) without NaN ->
    quant.earnings.event_panel(events, index, symbols, hold). Symbols without facts stay NaN.
    """
    raise NotImplementedError


def event_drift_panel(events: list[dict], index: pd.DatetimeIndex, symbols: list[str],
                      priors: dict[str, float], window: int = 20, decay: float = 10.0) -> pd.DataFrame:
    """evt_drift raw panel from ExtractedEvent dicts.

    For an event with effective row r (see effective_row(available_at)), rows r .. r+window-1 get
    prior[event_type] * direction * exp(-k / decay) with k = row - r + 1 (k = 1 on row r).
    Contributions of several events on the same symbol and row are summed. Events whose type has no
    prior, whose direction is 0, or whose symbol is not in symbols are ignored. Cells with no
    contributing event are NaN.
    """
    raise NotImplementedError


def demand_panel(events: list[dict], index: pd.DatetimeIndex, symbols: list[str], hold: int = 60) -> pd.DataFrame:
    """earn_demand_language raw panel. Group events by (symbol, doc_sha256); score each document
    with tradepulse.extract.grounding.demand_language_score (skip None); the document is available
    at the earliest available_at of its events. Spread with quant.earnings.event_panel using
    available_date = that UTC date, value = score, hold rows."""
    raise NotImplementedError


def event_priors(events: list[dict], prices: pd.DataFrame, benchmark: pd.Series, train_end: str,
                 shrink: float = 20.0) -> dict[str, float]:
    """Shrunk mean post-event abnormal return per event_type, from the training period only.

    For each event with direction != 0 whose symbol is in prices: r = effective_row(prices.index,
    available_at); it needs r >= 1 and r + 4 < len(prices) and prices.index[r + 4] <= train_end.
    abnormal = (P[r+4] / P[r-1] - 1) - (B[r+4] / B[r-1] - 1) (B = benchmark aligned to prices.index),
    signed by multiplying with direction. prior(type) = n / (n + shrink) * mean(abnormal); types
    with no usable event are absent. Row r-1 is the close on/before the event, so the event-day
    jump before availability is excluded.
    """
    raise NotImplementedError


def leader_shocks(prices: pd.DataFrame, benchmark: pd.Series, *, window: int = 5, beta_window: int = 60,
                  scale_window: int = 120) -> pd.DataFrame:
    """Normalised 5-day residual shock of every symbol.

    resid = simple return - rolling_beta(prices, benchmark, beta_window) * benchmark simple return;
    shock = rolling sum of resid over `window` rows (min_periods = window);
    z = shock / rolling std(shock, scale_window rows, ddof=1, min_periods = scale_window // 2).
    Uses only rows <= t. Zero std -> NaN.
    """
    raise NotImplementedError


def spillover_panel(prices: pd.DataFrame, benchmark: pd.Series, edges: list[dict], symbols: list[str],
                    index: pd.DatetimeIndex) -> pd.DataFrame:
    """rel_spillover raw panel for `symbols` on `index`.

    prices covers every leader and follower (possibly several pools, on a common calendar).
    Only edges with status == "validated" are used. For follower i at row t:
      s = sum_j w_ij * z_j[t-1] / sum_j abs(w_ij)
    over edges j -> i whose valid_from <= the date of row t and whose leader shock z_j[t-1]
    (leader_shocks, previous row of `index`) is not NaN. No usable edge -> NaN.
    """
    raise NotImplementedError


def validate_edges(seed_edges: pd.DataFrame, prices: pd.DataFrame, benchmark: pd.Series, *, train_start: str,
                   train_end: str, as_of: str, t_threshold: float = 2.0) -> list[dict]:
    """Lead-lag validation of seed edges (config/graph/seed_edges.csv columns: src_symbol,
    dst_symbol, relation, weight, evidence_note) on the training window.

    For each edge: leader = leader_shocks(...)[src] restricted to [train_start, train_end];
    follower = the follower's residual return series (simple return - rolling beta * benchmark
    return, beta_window 60), same window; stats = quant.evaluation.lead_lag_tstat(leader, follower,
    lag=1), which pairs leader[t-1] with follower[t].
    status = "validated" when sign(weight) * t_stat >= t_threshold, else "rejected"; a missing
    symbol -> "rejected" with lead_lag_t None.
    Returns contract GraphEdge dicts: edge_id = first 16 hex chars of sha256("src|dst|relation"),
    weight as float, source "seed", evidence_ref "config/graph/seed_edges.csv", lead_lag_t (float or
    None, non-finite -> None), valid_from = as_of.
    """
    raise NotImplementedError
