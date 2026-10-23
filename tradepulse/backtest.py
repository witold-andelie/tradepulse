"""Walk-forward evaluation: simulate past decisions with only the data available at the time,
then settle them against realised returns. Fills the TrackRecord and supplies an out-of-sample
composite IC and point-in-time weights for today's ranking.

Timeline for a decision on row d (L = execution lag, h = primary horizon):
- weights and IC_comp are fitted on rows whose forward returns are already known at d:
  rows [window_start, d - h - L] (inclusive) of the factor panels and prices;
- the decision uses the panels' row d (each panel row is point-in-time by construction);
- the outcome is the excess return from close d+L to close d+L+h over the pool benchmark.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant import evaluation, indicators, settlement
from tradepulse import contracts
from tradepulse import ranking
from tradepulse import regime as regime_mod
from tradepulse.research import evaluate as research_evaluate

WF_FACTORS_EXCLUDED = ("evt_drift", "rel_spillover")  # their priors/edges are fitted in-sample


def decision_rows(index: pd.DatetimeIndex, window_start: str, *, burn_in: int, step: int) -> list[int]:
    """Row positions of decision dates: start at the first row >= window_start plus burn_in rows,
    then every `step` rows, up to and including the last row."""
    first = int(index.searchsorted(pd.Timestamp(window_start)))
    start = first + int(burn_in)
    n = len(index)
    if start >= n:
        return []
    return list(range(start, n, int(step)))


def fit_rows(d: int, *, horizon: int, lag: int, first: int) -> tuple[int, int] | None:
    """(start, end) inclusive row range used to fit weights for a decision on row d:
    start = first (window-start row), end = d - horizon - lag. None when end - start + 1 < 40."""
    end = int(d) - int(horizon) - int(lag)
    start = int(first)
    if end - start + 1 < 40:
        return None
    return (start, end)


def _regime_state_at(regime_points: pd.Series | None, index: pd.DatetimeIndex, d: int,
                     regime_cfg: dict) -> str:
    """Classify regime points at row d; normal when unknown or missing."""
    try:
        if regime_points is None:
            return "normal"
        date = index[d]
        value = None
        try:
            if date in regime_points.index:
                value = regime_points.loc[date]
                if isinstance(value, pd.Series):
                    value = value.iloc[0] if len(value) else None
            elif len(regime_points) == len(index):
                value = regime_points.iloc[d]
        except Exception:
            value = None
        if value is None or pd.isna(value):
            return "normal"
        return regime_mod.classify(int(value), regime_cfg)
    except Exception:
        return "normal"


def walk_forward(pool: str, panels: dict[str, pd.DataFrame], prices: pd.DataFrame, benchmark: pd.Series,
                 regime_points: pd.Series, cfg: dict, window_start: str, *, refit_every: int = 20,
                 burn_in: int = 120) -> dict:
    """Run the walk-forward for one pool.

    - Factors in WF_FACTORS_EXCLUDED are dropped before anything else.
    - Decisions on decision_rows(prices.index, window_start, burn_in=burn_in,
      step=cfg["backtest"]["primary_horizon"]).
    - Weights are refitted (tradepulse.research.evaluate.research_pool on the fit_rows slice, window =
      the slice's first and last dates) on the first decision and then whenever at least refit_every
      rows passed since the last fit; between refits the latest weights are reused. IC_comp at
      a refit = composite_ic on the same slice (primary horizon, execution lag, min names). Decisions
      without any fit yet are skipped.
    - At a decision: tradepulse.ranking.composite on the panels' row d with the current weights ->
      join sigma_daily (20-row realized vol on prices up to d, per row) -> assign_tiers with the
      current IC_comp, the pool cost and cfg["tiers"] -> apply_regime with
      tradepulse.regime.classify(regime_points at row d) (normal when unknown).
    - Outcome per symbol: settled when row d + L + h exists: excess = quant.settlement.excess_return
      (P[d+L], P[d+L+h], B[d+L], B[d+L+h]); hit = quant.settlement.hit(tier, excess). Otherwise pending.
    - Realised composite rank IC per decision: Spearman between composite score and the symbol
      forward return P[d+L+h]/P[d+L]-1 (quant.evaluation.rank_ic semantics, min_names from cfg).

    Returns {
      "by_tier": [{"pool", "tier", "n", "hit_rate", "mean_excess_bps"] for every tier with n > 0
                  (hit_rate None for NEUTRAL / NO_CALL),
      "calibration_rows": list of (score percentile, 1 if excess > 0 else 0) for settled outcomes,
      "ic_series": [{"date", "pool", "ic"}] per settled decision,
      "settled": int, "pending": int,
      "ic_comp_oos": mean of the realised composite ICs (None if none),
      "latest_weights": weights fitted on the latest possible fit range for the last row of prices
                        (the point-in-time weights to use today), "latest_ic_comp": its IC_comp,
      "decisions": int (number of decision dates evaluated),
      "decision_tiers": {ISO date of row d: {symbol: tier}} for every evaluated decision,
    }. All numbers are plain Python types; never mutates inputs. A decision on row d may only use
    prices and panel rows <= d (outcomes excepted), which tests check by perturbing later prices.
    """
    kept: dict[str, pd.DataFrame] = {k: v for k, v in panels.items() if k not in WF_FACTORS_EXCLUDED}
    backtest_cfg: dict = cfg["backtest"]
    pool_cfg: dict = cfg["pools"][pool]
    primary_horizon = int(backtest_cfg["primary_horizon"])
    lag = int(backtest_cfg["execution_lag_days"])
    min_names = int(cfg["factors"]["min_names_per_date"])
    cost = float(pool_cfg["cost_bps_one_way"])
    rows_per_year = int(pool_cfg["rows_per_year"])
    tiers_cfg: dict = cfg["tiers"]
    regime_cfg: dict = cfg["regime"]

    index = prices.index
    n = len(index)
    first = int(index.searchsorted(pd.Timestamp(window_start)))
    dec_rows = decision_rows(index, window_start, burn_in=burn_in, step=primary_horizon)

    vol = indicators.realized_vol(prices, window=20, periods_per_year=rows_per_year)
    bench_aligned = benchmark.reindex(index)
    price_vals = prices.to_numpy(dtype=float)
    bench_vals = bench_aligned.to_numpy(dtype=float)
    col_pos = {c: i for i, c in enumerate(prices.columns)}

    current_weights: dict[str, float] | None = None
    current_ic: float | None = None
    last_fit_d: int | None = None

    tier_excess: dict[str, list[float]] = {}
    tier_hits: dict[str, list[bool]] = {}
    calibration_rows: list[tuple[float, int]] = []
    ic_series: list[dict] = []
    ic_vals: list[float] = []
    decision_tiers: dict[str, dict[str, str]] = {}
    settled = 0
    pending = 0
    decisions = 0

    for d in dec_rows:
        fr = fit_rows(d, horizon=primary_horizon, lag=lag, first=first)
        if fr is None:
            if current_weights is None:
                continue
        else:
            need_refit = current_weights is None or (last_fit_d is None or (d - last_fit_d) >= int(refit_every))
            if need_refit:
                s, e = fr
                prices_slice = prices.iloc[s:e + 1]
                panels_slice = {k: df.iloc[s:e + 1] for k, df in kept.items()}
                start_iso = index[s].date().isoformat()
                end_iso = index[e].date().isoformat()
                produced = research_evaluate.research_pool(pool, panels_slice, prices_slice, cfg, (start_iso, end_iso))
                current_weights = {str(k): float(v) for k, v in produced["weights"].items()}
                ic_val = research_evaluate.composite_ic(
                    panels_slice, current_weights, prices_slice,
                    primary_horizon=primary_horizon, lag=lag, min_names=min_names)
                current_ic = float(ic_val) if ic_val is not None else None
                last_fit_d = d
        if current_weights is None:
            continue

        z: dict[str, pd.Series] = {f: df.iloc[d] for f, df in kept.items()}
        comp = ranking.composite(z, current_weights)
        comp = comp.copy()
        vol_row = vol.iloc[d]
        comp["sigma_daily"] = vol_row.reindex(comp.index)
        tiered = ranking.assign_tiers(
            comp, ic_comp=current_ic, cost_bps_one_way=cost,
            horizon=primary_horizon, tiers_cfg=tiers_cfg, valuation_pctile=None)
        state = _regime_state_at(regime_points, index, d, regime_cfg)
        ranked = ranking.apply_regime(tiered, state)

        decisions += 1
        date_d = index[d]
        iso = date_d.date().isoformat()
        decision_tiers[iso] = {str(sym): str(ranked.loc[sym, "tier"]) for sym in ranked.index}

        entry = d + lag
        exit_ = d + lag + primary_horizon
        if exit_ >= n:
            pending += int(len(ranked))
            continue
        b_entry = float(bench_vals[entry]) if entry < len(bench_vals) else float("nan")
        b_exit = float(bench_vals[exit_]) if exit_ < len(bench_vals) else float("nan")
        bench_ok = bool(np.isfinite(b_entry) and np.isfinite(b_exit) and b_entry != 0.0)
        if not bench_ok:
            pending += int(len(ranked))
            continue

        symbols = list(ranked.index)
        entry_px = np.array(
            [price_vals[entry, col_pos[s]] if s in col_pos else np.nan for s in symbols], dtype=float)
        exit_px = np.array(
            [price_vals[exit_, col_pos[s]] if s in col_pos else np.nan for s in symbols], dtype=float)
        scores = ranked["score"].to_numpy(dtype=float)
        coverages = comp["coverage"].reindex(ranked.index).to_numpy(dtype=float)
        percentiles = ranked["percentile"].to_numpy(dtype=float)

        for i, sym in enumerate(symbols):
            tier = str(ranked.loc[sym, "tier"])
            px_in = float(entry_px[i])
            px_out = float(exit_px[i])
            if not (np.isfinite(px_in) and np.isfinite(px_out) and px_in != 0.0):
                pending += 1
                continue
            excess = settlement.excess_return(px_in, px_out, b_entry, b_exit)
            if not np.isfinite(excess):
                pending += 1
                continue
            settled += 1
            tier_excess.setdefault(tier, []).append(float(excess))
            hit_val = settlement.hit(tier, float(excess))
            if hit_val is not None:
                tier_hits.setdefault(tier, []).append(bool(hit_val))
            pct = float(percentiles[i])
            calibration_rows.append((pct, int(1 if float(excess) > 0 else 0)))

        # Realised composite IC for this settled decision.
        score_masked = np.where(np.isfinite(coverages) & (coverages > 0), scores, np.nan)
        fwd_arr = np.array(
            [((exit_px[i] / entry_px[i] - 1.0) if (np.isfinite(entry_px[i]) and np.isfinite(exit_px[i])
              and entry_px[i] != 0.0) else np.nan) for i in range(len(symbols))], dtype=float)
        try:
            factor_df = pd.DataFrame([score_masked], index=[date_d], columns=symbols)
            target_df = pd.DataFrame([fwd_arr], index=[date_d], columns=symbols)
            ic_one = evaluation.rank_ic(factor_df, target_df, min_names).iloc[0]
        except Exception:
            ic_one = float("nan")
        if ic_one is None or (isinstance(ic_one, float) and pd.isna(ic_one)) or pd.isna(ic_one):
            ic_series.append({"date": iso, "pool": str(pool), "ic": None})
        else:
            ic_float = float(ic_one)
            if np.isfinite(ic_float):
                ic_series.append({"date": iso, "pool": str(pool), "ic": ic_float})
                ic_vals.append(ic_float)
            else:
                ic_series.append({"date": iso, "pool": str(pool), "ic": None})

    by_tier: list[dict] = []
    for tier in sorted(tier_excess):
        excesses = tier_excess[tier]
        count = int(len(excesses))
        if count <= 0:
            continue
        mean_bps = float(float(np.mean(np.asarray(excesses, dtype=float))) * 1e4)
        if tier in ("NEUTRAL", "NO_CALL"):
            hit_rate = None
        else:
            hits = tier_hits.get(tier, [])
            hit_rate = float(sum(1 for h in hits if h) / count) if count else None
        by_tier.append({"pool": str(pool), "tier": str(tier), "n": count,
                        "hit_rate": hit_rate, "mean_excess_bps": mean_bps})

    if ic_vals:
        ic_comp_oos: float | None = float(float(np.mean(np.asarray(ic_vals, dtype=float))))
    else:
        ic_comp_oos = None

    last_d = n - 1
    latest_weights: dict[str, float]
    latest_ic_comp: float | None
    fr_latest = fit_rows(last_d, horizon=primary_horizon, lag=lag, first=first)
    if fr_latest is not None:
        s, e = fr_latest
        prices_slice = prices.iloc[s:e + 1]
        panels_slice = {k: df.iloc[s:e + 1] for k, df in kept.items()}
        start_iso = index[s].date().isoformat()
        end_iso = index[e].date().isoformat()
        produced = research_evaluate.research_pool(pool, panels_slice, prices_slice, cfg, (start_iso, end_iso))
        latest_weights = {str(k): float(v) for k, v in produced["weights"].items()}
        ic_val = research_evaluate.composite_ic(
            panels_slice, latest_weights, prices_slice,
            primary_horizon=primary_horizon, lag=lag, min_names=min_names)
        latest_ic_comp = float(ic_val) if ic_val is not None else None
    else:
        latest_weights = dict(current_weights) if current_weights is not None else {}
        latest_ic_comp = float(current_ic) if current_ic is not None else None

    return {
        "by_tier": by_tier,
        "calibration_rows": calibration_rows,
        "ic_series": ic_series,
        "settled": int(settled),
        "pending": int(pending),
        "ic_comp_oos": ic_comp_oos,
        "latest_weights": latest_weights,
        "latest_ic_comp": latest_ic_comp,
        "decisions": int(decisions),
        "decision_tiers": decision_tiers,
    }


def track_record(results: list[dict], window: dict, n_buckets: int = 5) -> dict:
    """Merge per-pool walk_forward results into a contract TrackRecord:
    mode "walk_forward", window, settled_count / pending_count (sums), by_tier (concatenated),
    calibration = quant.settlement.calibration_table over all calibration_rows (predicted = mean
    score percentile, observed = share outperforming the benchmark; empty buckets -> n 0 and None
    means), composite_ic_series (concatenated, ic None when NaN). Validates with
    tradepulse.contracts.assert_payload(..., "TrackRecord")."""
    settled_count = int(sum(int(r.get("settled", 0)) for r in results))
    pending_count = int(sum(int(r.get("pending", 0)) for r in results))
    by_tier: list[dict] = []
    for r in results:
        for row in r.get("by_tier", []):
            hit = row.get("hit_rate")
            mean_bps = row.get("mean_excess_bps")
            by_tier.append({
                "pool": str(row["pool"]),
                "tier": str(row["tier"]),
                "n": int(row["n"]),
                "hit_rate": None if hit is None or pd.isna(hit) else float(hit),
                "mean_excess_bps": None if mean_bps is None or pd.isna(mean_bps) else float(mean_bps),
            })

    all_rows: list[tuple[float, int]] = []
    for r in results:
        all_rows.extend(list(r.get("calibration_rows", [])))
    if all_rows:
        probs = pd.Series([float(p) for p, _ in all_rows])
        outcomes = pd.Series([int(o) for _, o in all_rows])
    else:
        probs = pd.Series(dtype=float)
        outcomes = pd.Series(dtype=float)
    cal_df = settlement.calibration_table(probs, outcomes, int(n_buckets))
    calibration: list[dict] = []
    for _, row in cal_df.iterrows():
        calibration.append({
            "bucket_low": float(row["bucket_low"]),
            "bucket_high": float(row["bucket_high"]),
            "n": int(row["n"]),
            "predicted": None if pd.isna(row["predicted"]) else float(row["predicted"]),
            "observed": None if pd.isna(row["observed"]) else float(row["observed"]),
        })

    composite_ic_series: list[dict] = []
    for r in results:
        for entry in r.get("ic_series", []):
            raw = entry.get("ic")
            if raw is None or pd.isna(raw):
                ic_val = None
            else:
                try:
                    ic_float = float(raw)
                    ic_val = None if not np.isfinite(ic_float) else ic_float
                except Exception:
                    ic_val = None
            composite_ic_series.append({
                "date": str(entry["date"]),
                "pool": str(entry["pool"]),
                "ic": ic_val,
            })

    payload = {
        "mode": "walk_forward",
        "window": {"start": str(window["start"]), "end": str(window["end"])},
        "settled_count": settled_count,
        "pending_count": pending_count,
        "by_tier": by_tier,
        "calibration": calibration,
        "composite_ic_series": composite_ic_series,
    }
    contracts.assert_payload(payload, "TrackRecord")
    return payload
