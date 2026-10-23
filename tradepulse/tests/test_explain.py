import json
from types import SimpleNamespace

import pandas as pd

from tradepulse.agents.explain import ABSTAIN_SUMMARY, Explainer, gather_evidence
from tradepulse.contracts import validate_payload
from tradepulse.trace import Tracer

AS_OF = "2026-10-21"
SHA = {"price_symbol_window": "1" * 64, "filings_symbol_window": "2" * 64}


def _item(symbol="NVDA", pool="us_equity"):
    return {"pool": pool, "symbol": symbol, "name": f"{symbol} Corp", "tier": "OVERWEIGHT", "score": 0.8,
            "rank": 3, "n": 520, "as_of": AS_OF,
            "contributions": [{"factor": "pv_mom_12_1", "z": 1.0, "weight": 0.5, "contribution": 0.5},
                              {"factor": "rel_spillover", "z": 1.0, "weight": 0.3, "contribution": 0.3}]}


class FakeQuery:
    backend = "duckdb"

    def run(self, template, params):
        if template == "price_symbol_window":
            df = pd.DataFrame({"date": pd.bdate_range("2026-08-24", periods=42),
                               "adj_close": [100 + i for i in range(42)]})
        else:
            df = pd.DataFrame({"accession_number": ["0000000000-26-000123"], "form": ["8-K"], "items": ["2.02,9.01"],
                               "acceptance_datetime": [pd.Timestamp("2026-10-15 20:05", tz="UTC")]})
        return SimpleNamespace(df=df, rows_sha256=SHA[template])


class ScriptedLLM:
    """Pops scripted analyst replies in order; the skeptic always answers the same."""

    def __init__(self, analyst_replies):
        self.analyst = list(analyst_replies)
        self.calls = []

    def complete(self, role, messages, response_schema=None):
        self.calls.append(role)
        if role == "analyst":
            text = self.analyst.pop(0) if self.analyst else "not json"
        else:
            text = json.dumps({"counter_case": ["Sector-wide AI flows may explain part of the move."],
                               "ruled_out": ["No index rebalance in the window."]})
        return SimpleNamespace(text=text, provider="fake", model=f"fake-{role}", tokens_in=10, tokens_out=5,
                               cassette_key="k" * 64, replayed=False)


GOOD = json.dumps({"summary": "Trend and supplier momentum drive the ranking.",
                   "claims": [{"text": "Twelve-month momentum contributes most.", "kind": "factor",
                               "evidence_ids": ["ev-nvda-price-symbol-window"]}],
                   "what_to_watch": ["Next earnings release"], "ruled_out": []})
BAD = json.dumps({"summary": "x", "claims": [{"text": "Invented.", "kind": "price", "evidence_ids": ["ev-ghost"]}],
                  "what_to_watch": []})
EVENT = json.dumps({"summary": "The earnings release preceded the gap.",
                    "claims": [{"text": "The 8-K earnings release came before the move.", "kind": "event",
                                "evidence_ids": ["ev-nvda-filings-symbol-window"], "move_date": "2026-10-16",
                                "cause_evidence_id": "ev-nvda-filings-symbol-window",
                                "cause_accession": "0000000000-26-000123"}],
                    "what_to_watch": []})


def test_gather_evidence():
    bundle, notes, text = gather_evidence(_item(), FakeQuery())
    assert sorted(bundle) == ["ev-nvda-filings-symbol-window", "ev-nvda-price-symbol-window"]
    for ev in bundle.values():
        assert validate_payload(ev, "EvidenceRef") == []
    assert bundle["ev-nvda-price-symbol-window"]["source_table"] == "price_bar"
    assert "0000000000-26-000123" in notes["ev-nvda-filings-symbol-window"]["accessions"]
    assert "[ev-nvda-price-symbol-window]" in text
    crypto, _, _ = gather_evidence(_item("BTC-USD", "crypto"), FakeQuery())
    assert list(crypto) == ["ev-btc-usd-price-symbol-window"]


def test_retry_then_verified(tmp_path):
    tracer = Tracer("run-explain-01", "SYNTHETIC", log_dir=tmp_path, echo=False)
    llm = ScriptedLLM([BAD, GOOD])
    out = Explainer(FakeQuery(), llm, max_retries=2, tracer=tracer).run([_item()])
    exp = out["NVDA"]["explanation"]
    assert validate_payload(exp, "Explanation") == []
    assert exp["verdict"] == "explained" and exp["retries"] == 1
    assert exp["claims"][0]["status"] == "verified"
    assert exp["counter_case"] and exp["models"] == {"analyst": "fake-analyst", "skeptic": "fake-skeptic"}
    assert out["NVDA"]["what_to_watch"] == ["Next earnings release"]
    assert llm.calls == ["analyst", "skeptic", "analyst"]  # the skeptic runs once
    kinds = [e["kind"] for e in tracer.events()]
    assert "retry" in kinds and "verify" in kinds and kinds.count("llm_call") == 3


def test_abstains_after_bounded_retries():
    llm = ScriptedLLM([BAD, BAD, BAD, GOOD])
    exp = Explainer(FakeQuery(), llm, max_retries=2).run([_item()])["NVDA"]["explanation"]
    assert exp["verdict"] == "abstained" and exp["summary"] == ABSTAIN_SUMMARY
    assert exp["retries"] == 2
    assert llm.calls.count("analyst") == 3  # first draft + 2 retries, never more
    assert validate_payload(exp, "Explanation") == []


def test_event_claim_uses_filing_timestamp():
    exp = Explainer(FakeQuery(), ScriptedLLM([EVENT])).run([_item()])["NVDA"]["explanation"]
    assert exp["verdict"] == "explained"
    checks = {c["name"]: c["passed"] for c in exp["claims"][0]["checks"]}
    assert checks["cause_before_move"] is True


def test_event_claim_after_move_is_rejected():
    late = EVENT.replace("2026-10-16", "2026-10-14")  # the move predates the filing
    exp = Explainer(FakeQuery(), ScriptedLLM([late, late, late]), max_retries=2).run([_item()])["NVDA"]["explanation"]
    assert exp["verdict"] == "abstained"


def test_parallel_fan_out():
    items = [_item("NVDA"), _item("AMD"), _item("BTC-USD", "crypto")]
    replies = {"NVDA": GOOD}

    class PerSymbolLLM(ScriptedLLM):
        def complete(self, role, messages, response_schema=None):
            if role == "analyst":
                content = messages[-1]["content"]
                sym = next(s for s in ("NVDA", "AMD", "BTC-USD") if f'"symbol": "{s}"' in content)
                slug = sym.lower()
                text = replies.get(sym, GOOD.replace("ev-nvda-", f"ev-{slug}-"))
                return SimpleNamespace(text=text, provider="fake", model="fake-analyst", tokens_in=1,
                                       tokens_out=1, cassette_key="k" * 64, replayed=False)
            return super().complete(role, messages, response_schema)

    out = Explainer(FakeQuery(), PerSymbolLLM([]), max_concurrency=3).run(items)
    assert set(out) == {"NVDA", "AMD", "BTC-USD"}
    assert all(r["explanation"]["verdict"] == "explained" for r in out.values())
    assert Explainer(FakeQuery(), ScriptedLLM([])).run([]) == {}
