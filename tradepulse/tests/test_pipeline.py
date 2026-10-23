"""End-to-end: run_pipeline on a synthetic lake through fake ports (no network, no sponsors)."""

import hashlib
from pathlib import Path
import json
import re
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from tradepulse.contracts import validate_payload
from tradepulse.pipeline import run_pipeline

AS_OF = pd.Timestamp("2026-10-21")
DOC_TEXT = "Q3 results. Demand continues to exceed supply. We raised full-year guidance."


def _lake():
    rng = np.random.default_rng(7)
    dates = pd.bdate_range(end=AS_OF, periods=600)
    pools = {"us_equity": [f"U{i:02d}" for i in range(30)], "crypto": [f"C{i:02d}-USD" for i in range(22)],
             "reference": ["SPY", "^VIX", "^VIX3M", "BTC-USD"]}
    bars, views, members = [], [], []
    for pool, syms in pools.items():
        for j, sym in enumerate(syms):
            rets = rng.normal(0.0004, 0.015, len(dates))
            px = 100 * np.cumprod(1 + rets)
            if sym == "^VIX3M":
                px = px * 1.2
            bars.append(pd.DataFrame({"pool": pool, "symbol": sym, "date": dates, "adj_close": px,
                                      "volume": rng.lognormal(12, 0.3, len(dates))}))
            if pool != "reference":
                members.append({"pool": pool, "symbol": sym, "name": f"Synthetic {sym}",
                                "sector": ["Tech", "Energy", "Health"][j % 3] if pool == "us_equity" else "layer-1"})
                views.append(pd.DataFrame({"pool": pool, "symbol": sym, "date": dates,
                                           "views": rng.poisson(500, len(dates)).astype(float)}))
    macro = pd.DataFrame({"series_id": "BAMLH0A0HYM2", "date": dates, "value": 3 + rng.normal(0, 0.02, len(dates)).cumsum() * 0.01})
    return pd.concat(bars), pd.concat(views), pd.DataFrame(members), macro


class LakeQuery:
    backend = "duckdb"

    def __init__(self):
        self.bars, self.views, self.members, self.macro = _lake()
        self.calls = []

    @staticmethod
    def _between(df, start, end):
        return df[(df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))]

    def run(self, template, params):
        self.calls.append(template)
        if template == "universe_pool":
            df = self.members[self.members["pool"] == params["pool"]]
        elif template == "price_pool_window":
            df = self._between(self.bars[self.bars["pool"] == params["pool"]], params["start"], params["end"])
        elif template == "price_symbol_window":
            df = self._between(self.bars[self.bars["symbol"] == params["symbol"]], params["start"], params["end"])
        elif template == "pageviews_pool_window":
            df = self._between(self.views[self.views["pool"] == params["pool"]], params["start"], params["end"])
        elif template == "macro_window":
            df = self._between(self.macro, params["start"], params["end"])
        elif template == "filings_symbol_window":
            df = pd.DataFrame(columns=["accession_number", "form", "items", "acceptance_datetime"])
        elif template == "filing_texts_window":
            df = pd.DataFrame([{"accession_number": "0000000001-26-000001", "cik": "0000000001", "symbol": "U01",
                                "document_name": "ex991.htm", "document_type": "EX-99.1", "url": "https://www.sec.gov/x",
                                "sha256": hashlib.sha256(DOC_TEXT.encode()).hexdigest(), "text": DOC_TEXT,
                                "char_count": len(DOC_TEXT), "available_at": pd.Timestamp("2026-09-15 20:05", tz="UTC"),
                                "fetched_at": pd.Timestamp("2026-10-01", tz="UTC")}])
        elif template == "facts_tag_window":
            df = pd.DataFrame(columns=["symbol", "tag", "unit", "value", "period_start", "period_end", "filed"])
        else:
            raise KeyError(template)
        df = df.reset_index(drop=True)
        digest = hashlib.sha256(df.to_json(date_format="iso").encode()).hexdigest()
        return SimpleNamespace(df=df, rows_sha256=digest)


class ScriptedLLM:
    def __init__(self):
        self.roles = []

    def complete(self, role, messages, response_schema=None):
        self.roles.append(role)
        if role == "extractor":
            text = json.dumps({"events": [{"event_type": "guidance_raise", "direction": 1, "novelty": "new",
                                           "quote": "We raised full-year guidance",
                                           "demand_signals": [{"type": "demand_exceeds_supply", "polarity": 1,
                                                               "quote": "Demand continues to exceed supply"}]}]})
            return SimpleNamespace(text=text, provider="fake", model="fake-extractor", tokens_in=1, tokens_out=1,
                                   cassette_key="0" * 64, replayed=True)
        if role == "analyst":
            sym = re.search(r'"symbol": "([^"]+)"', messages[-1]["content"]).group(1)
            slug = re.sub(r"[^a-z0-9]+", "-", sym.lower()).strip("-")
            text = json.dumps({"summary": f"{sym}: price-volume factors drive the score.",
                               "claims": [{"text": "The composite comes from the listed factor contributions.",
                                           "kind": "factor", "evidence_ids": [f"ev-{slug}-price-symbol-window"]}],
                               "what_to_watch": ["Moves in linked names"]})
        else:
            text = json.dumps({"counter_case": ["Momentum can reverse quickly."], "ruled_out": []})
        return SimpleNamespace(text=text, provider="fake", model=f"fake-{role}", tokens_in=1, tokens_out=1,
                               cassette_key="0" * 64, replayed=True)


@pytest.fixture(scope="module")
def output(tmp_path_factory):
    request = {"as_of": "2026-10-21", "pools": ["us_equity", "crypto"], "tickers": ["U05"], "horizon_days": 5,
               "top_k": 2}
    llm = ScriptedLLM()
    import tradepulse.pipeline as pipeline_module
    cache_dir = tmp_path_factory.mktemp("cache")
    original = pipeline_module.SAMPLE_ROOT
    pipeline_module.SAMPLE_ROOT = cache_dir  # keep the extraction cache out of data/sample
    try:
        out = run_pipeline(request, query=LakeQuery(), llm=llm, log_dir=tmp_path_factory.mktemp("logs"))
    finally:
        pipeline_module.SAMPLE_ROOT = original
    return out, llm


def test_output_is_contract_valid(output):
    out, _ = output
    assert validate_payload(out, "RunOutput") == []
    assert out["as_of"] == "2026-10-21" and out["data_mode"] == "REPLAY"
    assert [p["pool"] for p in out["pools"]] == ["us_equity", "crypto"]


def test_every_member_is_ranked_once(output):
    out, _ = output
    us = [r for r in out["recommendations"] if r["pool"] == "us_equity"]
    assert len(us) == 30 and sorted(r["rank"] for r in us) == list(range(1, 31))
    for r in out["recommendations"]:
        assert abs(sum(c["contribution"] for c in r["contributions"]) - r["score"]) < 1e-6


def test_cards_regimes_and_explanations(output):
    out, llm = output
    assert len(out["factor_cards"]) == 22  # 6 price-volume + attention + 4 signal factors, per pool
    crypto = {c["factor"]: c for c in out["factor_cards"] if c["pool"] == "crypto"}
    assert crypto["earn_sue"]["status"] == "INSUFFICIENT_DATA"  # no filings for crypto: said, not hidden
    assert {r["pool"] for r in out["regimes"]} == {"us_equity", "crypto"}
    assert out["explanations"], "focus names must be explained"
    assert all(e["verdict"] == "explained" for e in out["explanations"])
    assert "U05" in {e["symbol"] for e in out["explanations"]}  # requested ticker
    assert llm.roles.count("skeptic") == len(out["explanations"])


def test_trace_written(output):
    out, _ = output
    from pathlib import Path
    lines = Path(out["trace_path"]).read_text(encoding="utf-8").splitlines()
    nodes = {json.loads(line)["node"] for line in lines}
    assert {"research:us_equity", "regime:crypto", "explain", "report"} <= nodes


def test_extraction_feeds_event_factors(output):
    out, llm = output
    assert "extractor" in llm.roles
    us = {c["factor"]: c for c in out["factor_cards"] if c["pool"] == "us_equity"}
    assert {"evt_drift", "earn_demand_language", "rel_spillover", "earn_sue"} <= set(us)
    assert not any("Event extraction unavailable" in w for w in out["warnings"])
    lines = Path(out["trace_path"]).read_text(encoding="utf-8").splitlines()
    assert any(json.loads(line)["message"] == "1 grounded events" for line in lines)
