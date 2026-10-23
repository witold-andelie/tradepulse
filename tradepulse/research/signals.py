"""Raw panels for the filing-based and relational factors (docs/architecture/factors.md).

These raw panels are passed to research.panels.build_pool_panels(extra=...), which standardises
them and residualises them on the price-volume baseline. Every panel is point-in-time: a value at
row t uses only information available before that row's close.

"Effective row" of something available at UTC time T: the first index row whose date is strictly
after T's UTC calendar date. (A filing accepted on 2026-10-15 becomes usable on the next session.)
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import pandas as pd
from quant.earnings import event_panel as _event_panel
from quant.earnings import quarterly_eps as _quarterly_eps
from quant.earnings import sue as _sue
from quant.evaluation import lead_lag_tstat as _lead_lag_tstat
from quant.indicators import rolling_beta as _rolling_beta
from quant.indicators import simple_returns as _simple_returns
from tradepulse.extract.grounding import demand_language_score as _demand_score

EPS_TAG = "EarningsPerShareDiluted"
EPS_UNIT = "USD/shares"


def effective_row(index: pd.DatetimeIndex, available_at) -> int:
    """Position of the first row of index whose date is strictly after the UTC date of
    available_at (str ISO, Timestamp or datetime; naive values are treated as UTC).
    Returns len(index) when no such row exists."""
    ts = pd.to_datetime(available_at, utc=True)
    day = pd.Timestamp(ts.date())
    tz = getattr(index, "tz", None)
    if tz is not None:
        day = pd.Timestamp(day, tz="UTC").tz_convert(tz)
    return int(index.searchsorted(day, side="right"))


def sue_panel(facts: pd.DataFrame, index: pd.DatetimeIndex, symbols: list[str], hold: int = 60) -> pd.DataFrame:
    """earn_sue raw panel from fundamental_fact rows.

    Per symbol: rows with tag == EPS_TAG and unit == EPS_UNIT -> quant.earnings.quarterly_eps ->
    quant.earnings.sue -> events (symbol, available_date = filed, value = sue) without NaN ->
    quant.earnings.event_panel(events, index, symbols, hold). Symbols without facts stay NaN.
    """
    rows: list[dict] = []
    for sym in symbols:
        sub = facts[(facts["tag"] == EPS_TAG) & (facts["unit"] == EPS_UNIT) & (facts["symbol"] == sym)]
        if sub.empty:
            continue
        eps = _quarterly_eps(sub)
        if eps.empty:
            continue
        with_sue = _sue(eps)
        valid = with_sue.dropna(subset=["sue"])
        for rec in valid.itertuples(index=False):
            rows.append({"symbol": sym, "available_date": rec.filed, "value": rec.sue})
    if rows:
        events = pd.DataFrame(rows)
    else:
        events = pd.DataFrame(columns=["symbol", "available_date", "value"])
    return _event_panel(events, index, symbols, hold)


def event_drift_panel(events: list[dict], index: pd.DatetimeIndex, symbols: list[str],
                      priors: dict[str, float], window: int = 20, decay: float = 10.0) -> pd.DataFrame:
    """evt_drift raw panel from ExtractedEvent dicts.

    For an event with effective row r (see effective_row(available_at)), rows r .. r+window-1 get
    prior[event_type] * direction * exp(-k / decay) with k = row - r + 1 (k = 1 on row r).
    Contributions of several events on the same symbol and row are summed. Events whose type has no
    prior, whose direction is 0, or whose symbol is not in symbols are ignored. Cells with no
    contributing event are NaN.
    """
    n = len(index)
    cols = {s: j for j, s in enumerate(symbols)}
    values = np.zeros((n, len(symbols)), dtype=float)
    hit = np.zeros((n, len(symbols)), dtype=bool)
    for ev in events:
        sym = ev.get("symbol")
        j = cols.get(sym)
        if j is None:
            continue
        direction = ev.get("direction")
        if direction == 0 or direction is None:
            continue
        etype = ev.get("event_type")
        if etype not in priors:
            continue
        prior = priors[etype]
        if prior is None or (isinstance(prior, float) and math.isnan(prior)):
            continue
        try:
            r = effective_row(index, ev.get("available_at"))
        except Exception:
            continue
        if r >= n:
            continue
        end = min(r + window, n)
        if end <= r:
            continue
        k = np.arange(1, end - r + 1, dtype=float)
        contrib = float(prior) * float(direction) * np.exp(-k / decay)
        values[r:end, j] += contrib
        hit[r:end, j] = True
    out = np.where(hit, values, np.nan)
    return pd.DataFrame(out, index=index, columns=symbols)


def demand_panel(events: list[dict], index: pd.DatetimeIndex, symbols: list[str], hold: int = 60) -> pd.DataFrame:
    """earn_demand_language raw panel. Group events by (symbol, doc_sha256); score each document
    with tradepulse.extract.grounding.demand_language_score (skip None); the document is available
    at the earliest available_at of its events. Spread with quant.earnings.event_panel using
    available_date = that UTC date, value = score, hold rows."""
    wanted = set(symbols)
    grouped: dict[tuple[str, str], list[dict]] = {}
    earliest: dict[tuple[str, str], pd.Timestamp] = {}
    for ev in events:
        sym = ev.get("symbol")
        sha = ev.get("doc_sha256")
        if sym is None or sha is None:
            continue
        key = (sym, sha)
        grouped.setdefault(key, []).append(ev)
        try:
            ts = pd.to_datetime(ev.get("available_at"), utc=True)
        except Exception:
            continue
        if key not in earliest or ts < earliest[key]:
            earliest[key] = ts
    rows: list[dict] = []
    for key, docs in grouped.items():
        sym = key[0]
        if sym not in wanted:
            continue
        score = _demand_score(docs)
        if score is None:
            continue
        ts = earliest.get(key)
        if ts is None:
            continue
        naive = ts.tz_convert(None)
        rows.append({"symbol": sym, "available_date": naive, "value": float(score)})
    if rows:
        ev_df = pd.DataFrame(rows)
    else:
        ev_df = pd.DataFrame(columns=["symbol", "available_date", "value"])
    return _event_panel(ev_df, index, symbols, hold)


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
    train_ts = pd.to_datetime(train_end)
    bench = benchmark.reindex(prices.index)
    n = len(prices.index)
    acc: dict[str, list[float]] = {}
    for ev in events:
        direction = ev.get("direction")
        if direction == 0 or direction is None:
            continue
        sym = ev.get("symbol")
        if sym not in prices.columns:
            continue
        try:
            r = effective_row(prices.index, ev.get("available_at"))
        except Exception:
            continue
        if r < 1 or r + 4 >= n:
            continue
        if prices.index[r + 4] > train_ts:
            continue
        p0 = prices[sym].iloc[r - 1]
        p1 = prices[sym].iloc[r + 4]
        b0 = bench.iloc[r - 1]
        b1 = bench.iloc[r + 4]
        if pd.isna(p0) or pd.isna(p1) or pd.isna(b0) or pd.isna(b1):
            continue
        if p0 == 0 or b0 == 0:
            continue
        abnormal = (p1 / p0 - 1) - (b1 / b0 - 1)
        if pd.isna(abnormal) or not np.isfinite(abnormal):
            continue
        acc.setdefault(ev.get("event_type"), []).append(float(abnormal) * float(direction))
    priors: dict[str, float] = {}
    for etype, vals in acc.items():
        if not vals:
            continue
        mean = float(np.mean(vals))
        k = len(vals)
        priors[etype] = k / (k + shrink) * mean
    return priors


def leader_shocks(prices: pd.DataFrame, benchmark: pd.Series, *, window: int = 5, beta_window: int = 60,
                  scale_window: int = 120) -> pd.DataFrame:
    """Normalised 5-day residual shock of every symbol.

    resid = simple return - rolling_beta(prices, benchmark, beta_window) * benchmark simple return;
    shock = rolling sum of resid over `window` rows (min_periods = window);
    z = shock / rolling std(shock, scale_window rows, ddof=1, min_periods = scale_window // 2).
    Uses only rows <= t. Zero std -> NaN.
    """
    rets = _simple_returns(prices)
    beta = _rolling_beta(prices, benchmark, beta_window)
    aligned = benchmark.reindex(prices.index)
    bench_ret = aligned / aligned.shift(1) - 1
    resid = rets - beta.mul(bench_ret, axis=0)
    shock = resid.rolling(window, min_periods=window).sum()
    scale = shock.rolling(scale_window, min_periods=scale_window // 2).std(ddof=1)
    return shock / scale.where(scale.ne(0))


def spillover_panel(prices: pd.DataFrame, benchmark: pd.Series, edges: list[dict], symbols: list[str],
                    index: pd.DatetimeIndex) -> pd.DataFrame:
    """rel_spillover raw panel for `symbols` on `index`.

    prices covers every leader and follower (possibly several pools, on a common calendar).
    Only edges with status == "validated" are used. For follower i at row t:
      s = sum_j w_ij * z_j[t-1] / sum_j abs(w_ij)
    over edges j -> i whose valid_from <= the date of row t and whose leader shock z_j[t-1]
    (leader_shocks, previous row of `index`) is not NaN. No usable edge -> NaN.
    """
    shocks = leader_shocks(prices, benchmark)
    prev = shocks.reindex(index).shift(1)
    incoming: dict[str, list[tuple[str, float, pd.Timestamp]]] = {}
    for edge in edges:
        if edge.get("status") != "validated":
            continue
        dst = edge.get("dst_symbol")
        if dst not in symbols:
            continue
        src = edge.get("src_symbol")
        if src not in prev.columns:
            continue
        try:
            w = float(edge.get("weight"))
        except (TypeError, ValueError):
            continue
        try:
            valid = pd.to_datetime(edge.get("valid_from"))
        except Exception:
            continue
        incoming.setdefault(dst, []).append((src, w, valid))
    out = pd.DataFrame(np.nan, index=index, columns=symbols)
    for sym in symbols:
        lst = incoming.get(sym)
        if not lst:
            continue
        srcs = [s for s, _, _ in lst]
        weights = np.array([w for _, w, _ in lst], dtype=float)
        valids = [v for _, _, v in lst]
        mat = prev[srcs].to_numpy(dtype=float)
        valid_mask = np.column_stack([np.asarray(index >= v) for v in valids])
        usable = valid_mask & ~np.isnan(mat)
        numer = np.where(usable, mat * weights, 0.0).sum(axis=1)
        denom = np.where(usable, np.abs(weights), 0.0).sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            series = np.where(denom > 0, numer / np.where(denom == 0, np.nan, denom), np.nan)
        out[sym] = series
    return out


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
    shocks = leader_shocks(prices, benchmark)
    aligned = benchmark.reindex(prices.index)
    bench_ret = aligned / aligned.shift(1) - 1
    beta = _rolling_beta(prices, benchmark, 60)
    resid = _simple_returns(prices) - beta.mul(bench_ret, axis=0)
    result: list[dict] = []
    for row in seed_edges.itertuples(index=False):
        src = getattr(row, "src_symbol")
        dst = getattr(row, "dst_symbol")
        relation = getattr(row, "relation")
        try:
            weight = float(getattr(row, "weight"))
        except (TypeError, ValueError):
            weight = 0.0
        edge_id = hashlib.sha256(f"{src}|{dst}|{relation}".encode("utf-8")).hexdigest()[:16]
        lead: float | None = None
        status = "rejected"
        if src in prices.columns and dst in prices.columns:
            try:
                leader = shocks[src].loc[train_start:train_end]
                follower = resid[dst].loc[train_start:train_end]
                stats = _lead_lag_tstat(leader, follower, lag=1)
                t_stat = stats.get("t_stat")
            except Exception:
                t_stat = None
            if t_stat is None or not np.isfinite(t_stat):
                lead = None
                if isinstance(t_stat, float) and math.isinf(t_stat):
                    sign = 1.0 if weight > 0 else (-1.0 if weight < 0 else 0.0)
                    val = sign * t_stat
                    if np.isfinite(val) and val >= t_threshold:
                        status = "validated"
                else:
                    status = "rejected"
            else:
                lead = float(t_stat)
                sign = 1.0 if weight > 0 else (-1.0 if weight < 0 else 0.0)
                status = "validated" if sign * lead >= t_threshold else "rejected"
        result.append({
            "edge_id": edge_id,
            "src_symbol": src,
            "dst_symbol": dst,
            "relation": relation,
            "weight": weight,
            "source": "seed",
            "evidence_ref": "config/graph/seed_edges.csv",
            "status": status,
            "lead_lag_t": lead,
            "valid_from": as_of,
        })
    return result
