"""SD1 · Recommending: one full run (owned by the team lead).

The API and run.py call run_pipeline(request) only. Sponsor integrations are injected through the
ports in tradepulse.ports; by default they come from integrations/ (Member D):
SAMPLE_MODE -> DuckDB over data/sample + replayed LLM answers; live -> Zetaris + Meterless/NIM.
"""

from __future__ import annotations

import datetime as dt
import os
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from quant.indicators import realized_vol
from tradepulse import ranking, report
from tradepulse.agents.explain import Explainer
from tradepulse.config import load_config
from tradepulse.contracts import REPO_ROOT
from tradepulse.extract.grounding import ExtractionCache
from tradepulse.extract.runner import run_extraction
from tradepulse.ports import LLMPort, QueryPort
from tradepulse.regime_inputs import assess
from tradepulse.research.evaluate import composite_ic, research_pool
from tradepulse.research.panels import build_pool_panels
from tradepulse.research.signals import (EPS_TAG, demand_panel, event_drift_panel, event_priors,
                                         spillover_panel, sue_panel, validate_edges)
from tradepulse.trace import Tracer

SAMPLE_ROOT = REPO_ROOT / "data" / "sample"
CASSETTE_PATH = SAMPLE_ROOT / "llm_cassette.jsonl"
REFERENCE_SYMBOLS = ("SPY", "^VIX", "^VIX3M", "^STOXX50E", "BTC-USD")


def sample_mode() -> bool:
    return os.getenv("SAMPLE_MODE", "true").strip().lower() in {"true", "1", "yes", "on"}


def default_ports(is_sample: bool) -> tuple[QueryPort, LLMPort]:
    """Member D's adapters. Imported lazily so the core runs on fakes without them."""
    from integrations.meterless.llm import Cassette, ChainClient, build_routes_from_env
    from integrations.zetaris.adapter import make_adapter

    query = make_adapter(is_sample, SAMPLE_ROOT if is_sample else None)
    if is_sample:
        llm = ChainClient({}, Cassette(CASSETTE_PATH), mode="replay")
    else:
        llm = ChainClient(build_routes_from_env(), Cassette(CASSETTE_PATH), mode="record")
    return query, llm


def _wide(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    frame = df.assign(date=pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize())
    return frame.pivot_table(index="date", columns="symbol", values=column, aggfunc="last").sort_index()


def _latest_session(query: QueryPort, as_of: dt.date) -> dt.date:
    res = query.run("price_symbol_window", {"symbol": "SPY", "start": (as_of - dt.timedelta(days=14)).isoformat(),
                                            "end": as_of.isoformat()})
    if res.df.empty:
        raise RuntimeError("no reference prices before as_of")
    return pd.to_datetime(res.df["date"]).max().date()


def _load_reference(query: QueryPort, start: str, end: str) -> tuple[pd.DataFrame, pd.Series | None]:
    ref = query.run("price_pool_window", {"pool": "reference", "start": start, "end": end}).df
    reference = _wide(ref, "adj_close")
    macro = query.run("macro_window", {"series": "BAMLH0A0HYM2", "start": start, "end": end}).df
    hy = None
    if not macro.empty:
        hy = macro.assign(date=pd.to_datetime(macro["date"]).dt.tz_localize(None)).set_index("date")["value"].astype(float)
    return reference, hy


def _load_pool(pool: str, query: QueryPort, start: str, as_of: str, tracer: Tracer, warnings: list[str]) -> dict:
    with tracer.span(f"load:{pool}"):
        universe = query.run("universe_pool", {"pool": pool}).df.set_index("symbol")
        bars = query.run("price_pool_window", {"pool": pool, "start": start, "end": as_of}).df
        views_df = query.run("pageviews_pool_window", {"pool": pool, "start": start, "end": as_of}).df
    prices = _wide(bars, "adj_close").reindex(columns=sorted(universe.index))
    prices = prices.dropna(axis=1, how="all")
    volume = _wide(bars, "volume").reindex_like(prices)
    views = _wide(views_df, "views").reindex_like(prices) if not views_df.empty else None
    if views is None:
        warnings.append(f"{pool}: no pageview data; att_pageviews not evaluated")
    return {"pool": pool, "universe": universe, "prices": prices, "volume": volume, "views": views}


def _empty(index: pd.DatetimeIndex, symbols: list[str]) -> pd.DataFrame:
    return pd.DataFrame(np.nan, index=index, columns=symbols)


def _signal_panels(cfg: dict, query: QueryPort, llm: LLMPort, loaded: list[dict], reference: pd.DataFrame,
                   window_start: str, as_of: str, cache_path: Path, tracer: Tracer,
                   warnings: list[str]) -> dict[str, dict[str, pd.DataFrame]]:
    """Raw extra panels per pool: filing-based factors (US only) and relational spillover (all pools).
    Pools without a source still get all-NaN panels, so their cards honestly read INSUFFICIENT_DATA."""
    combined = pd.concat([d["prices"] for d in loaded] + [reference], axis=1)
    combined = combined.loc[:, ~combined.columns.duplicated()].sort_index().ffill(limit=3)
    extras: dict[str, dict[str, pd.DataFrame]] = {}
    spy = reference["SPY"].reindex(combined.index).ffill(limit=3) if "SPY" in reference else None
    if spy is None:
        warnings.append("SPY reference prices missing; relational and event factors are empty.")

    edges: list[dict] = []
    if spy is not None:
        with tracer.span("graph", "validating seed edges"):
            seeds = pd.read_csv(REPO_ROOT / "config" / "graph" / "seed_edges.csv")
            edges = validate_edges(seeds, combined, spy, train_start=window_start, train_end=as_of, as_of=as_of)
            validated = sum(e["status"] == "validated" for e in edges)
            tracer.event("graph", "info", message=f"{validated}/{len(edges)} seed edges validated",
                         payload={"edges": [{"src": e["src_symbol"], "dst": e["dst_symbol"], "status": e["status"],
                                             "t": e["lead_lag_t"]} for e in edges]})
        warnings.append("Graph edges are validated on the same window they are used in (in-sample).")

    events: list[dict] = []
    if spy is not None and any(d["pool"] == "us_equity" for d in loaded):
        with tracer.span("extract", "filing texts"):
            try:
                docs = query.run("filing_texts_window", {"start": window_start, "end": as_of}).df
                result = run_extraction(docs, llm, ExtractionCache(cache_path),
                                        max_docs=cfg["extract"]["max_docs_per_run"], tracer=tracer)
                events = result["events"]
                tracer.event("extract", "info", message=f"{len(events)} grounded events",
                             payload={k: result[k] for k in ("processed", "cached", "skipped", "rejected_problems")})
            except Exception as exc:  # missing table or extractor unavailable: the factors stay empty
                warnings.append(f"Event extraction unavailable ({type(exc).__name__}); event factors are empty.")

    for d in loaded:
        pool, prices = d["pool"], d["prices"]
        symbols, index = list(prices.columns), prices.index
        extra = {name: _empty(index, symbols) for name in ("rel_spillover", "earn_sue", "evt_drift",
                                                           "earn_demand_language")}
        if spy is not None:
            extra["rel_spillover"] = spillover_panel(combined, spy, edges, symbols, index)
        if pool == "us_equity" and spy is not None:
            try:
                facts = query.run("facts_tag_window", {"tag": EPS_TAG, "end": as_of}).df
                extra["earn_sue"] = sue_panel(facts, index, symbols)
            except Exception as exc:
                warnings.append(f"Fundamental facts unavailable ({type(exc).__name__}); earn_sue is empty.")
            if events:
                priors = event_priors(events, prices, spy.reindex(index), train_end=as_of)
                extra["evt_drift"] = event_drift_panel(events, index, symbols, priors)
                extra["earn_demand_language"] = demand_panel(events, index, symbols)
                warnings.append("Event priors are estimated on the research window (in-sample).")
        extras[pool] = extra
    return extras


def _rank_pool(data: dict, extra: dict[str, pd.DataFrame], cfg: dict, window_start: str, as_of: str,
               reference: pd.DataFrame, hy: pd.Series | None, tracer: Tracer, warnings: list[str]) -> dict:
    pool, universe, prices = data["pool"], data["universe"], data["prices"]
    pool_cfg = cfg["pools"][pool]
    groups = universe["sector"] if pool_cfg["sector_neutral"] else None

    with tracer.span(f"research:{pool}"):
        panels = build_pool_panels(prices, data["volume"], data["views"], groups, pool_cfg, cfg["factors"],
                                   extra=extra)
        research = research_pool(pool, panels, prices, cfg, (window_start, as_of))
        window_prices = prices.loc[window_start:as_of]
        ic_comp = composite_ic({f: p.loc[window_start:as_of] for f, p in panels.items()}, research["weights"],
                               window_prices, primary_horizon=cfg["backtest"]["primary_horizon"],
                               lag=cfg["backtest"]["execution_lag_days"],
                               min_names=cfg["factors"]["min_names_per_date"])
        active = sum(c["status"] == "ACTIVE" for c in research["cards"])
        tracer.event(f"research:{pool}", "info", message=f"{active}/{len(research['cards'])} factors active",
                     payload={"composite_ic_in_sample": ic_comp, "weights": research["weights"]})
        warnings.append(f"{pool}: composite IC is in-sample over the research window, not walk-forward")

    with tracer.span(f"regime:{pool}"):
        regime = assess(pool, as_of, prices, reference, hy, cfg["regime"], pool_cfg, window_start)

    with tracer.span(f"rank:{pool}"):
        last = prices.index[-1]
        z_today = {f: p.loc[last] for f, p in panels.items()}
        book = ranking.composite(z_today, research["weights"])
        sigma = (realized_vol(prices, 20, pool_cfg["rows_per_year"]).loc[last] / np.sqrt(pool_cfg["rows_per_year"]))
        book = book.join(sigma.rename("sigma_daily"))
        tiers = ranking.assign_tiers(book, ic_comp=ic_comp, cost_bps_one_way=pool_cfg["cost_bps_one_way"],
                                     horizon=cfg["backtest"]["primary_horizon"], tiers_cfg=cfg["tiers"])
        tiers = ranking.apply_regime(tiers, regime["state"])
        ret_1d = prices.pct_change(fill_method=None).iloc[-1]
    return {"pool": pool, "universe": universe, "prices": prices, "book": tiers, "ret_1d": ret_1d,
            "research": research, "ic_comp": ic_comp, "regime": regime, "as_of_close": str(last.date())}


def run_pipeline(request: dict, *, query: QueryPort | None = None, llm: LLMPort | None = None,
                 log_dir: Path | None = None, now: dt.datetime | None = None) -> dict:
    """Execute one run for a guarded RunRequest and return a contract-valid RunOutput."""
    cfg = load_config()
    is_sample = sample_mode()
    if query is None or llm is None:
        default_query, default_llm = default_ports(is_sample)
        query, llm = query or default_query, llm or default_llm
    now = now or dt.datetime.now(dt.timezone.utc)
    requested = dt.date.fromisoformat(request["as_of"]) if request.get("as_of") else now.date()
    as_of_date = _latest_session(query, requested)
    as_of = as_of_date.isoformat()
    window_start = (as_of_date - dt.timedelta(days=cfg["backtest"]["window_days"])).isoformat()
    start = (as_of_date - dt.timedelta(days=cfg["backtest"]["window_days"] + cfg["backtest"]["warmup_days"])).isoformat()

    run_id = report.new_run_id(as_of, uuid.uuid4().hex[:8])
    data_mode = "REPLAY" if is_sample else "REAL"
    tracer = Tracer(run_id, data_mode, log_dir=log_dir or REPO_ROOT / "logs")
    tracer.event("run", "info", message=f"run {run_id} as_of {as_of}", payload={"request": request})
    warnings: list[str] = ["The valuation constraint is not applied in this run."]

    reference, hy = _load_reference(query, start, as_of)
    loaded = [_load_pool(p, query, start, as_of, tracer, warnings) for p in request["pools"]]
    cache_path = (SAMPLE_ROOT if is_sample else REPO_ROOT / "data" / "cache") / "extraction_cache.jsonl"
    extras = _signal_panels(cfg, query, llm, loaded, reference, window_start, as_of, cache_path, tracer, warnings)
    pools = [_rank_pool(d, extras[d["pool"]], cfg, window_start, as_of, reference, hy, tracer, warnings)
             for d in loaded]

    items = []
    for p in pools:
        focus = ranking.select_focus(p["book"], top_k=request["top_k"], movers_k=cfg["explain"]["movers_k"],
                                     ret_1d=p["ret_1d"], requested=request["tickers"])
        for symbol in focus:
            row = p["book"].loc[symbol]
            items.append({"pool": p["pool"], "symbol": symbol, "name": str(p["universe"].at[symbol, "name"]),
                          "tier": str(row["tier"]), "score": float(row["score"]), "rank": int(row["rank"]),
                          "n": len(p["book"]), "as_of": as_of, "contributions": row["contributions"]})
    with tracer.span("explain", f"{len(items)} focus names"):
        explained = Explainer(query, llm, max_retries=cfg["explain"]["max_verify_retries"], tracer=tracer).run(items)

    with tracer.span("report"):
        recommendations, summaries = [], []
        for p in pools:
            meta = p["universe"][["name", "sector"]]
            last_close = p["prices"].iloc[-1]
            by_symbol = {s: v for s, v in explained.items() if s in p["book"].index}
            recommendations += report.recommendation_rows(p["pool"], p["book"], meta, last_close, p["ret_1d"],
                                                          request["horizon_days"], None, by_symbol)
            summaries.append(report.pool_summary(p["pool"], cfg["pools"][p["pool"]], len(p["universe"]), p["book"],
                                                 p["ic_comp"], p["regime"]["state"], p["as_of_close"]))
        output = report.run_output(
            run_id=run_id, created_at=now.isoformat().replace("+00:00", "Z"), as_of=as_of, data_mode=data_mode,
            sample_mode=is_sample, horizon=request["horizon_days"], request=request, pools=summaries,
            recommendations=recommendations, factor_cards=[c for p in pools for c in p["research"]["cards"]],
            regimes=[p["regime"] for p in pools], explanations=[v["explanation"] for v in explained.values()],
            track_record=report.empty_track_record({"start": window_start, "end": as_of}),
            warnings=warnings, trace_path=str(tracer.path.relative_to(REPO_ROOT)) if tracer.path.is_relative_to(REPO_ROOT)
            else str(tracer.path))
    tracer.event("run", "info", message="run complete",
                 payload={"recommendations": len(recommendations), "explanations": len(explained)})
    return output
