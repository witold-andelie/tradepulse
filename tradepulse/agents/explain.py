"""SD1.7 · Explaining: one LangGraph run explains every focus name in parallel.

Per name: gather evidence (allow-listed templates) -> analyst drafts claims -> skeptic challenges
(first round) -> deterministic verification -> retry with failure reasons (bounded) -> compose.
LLMs only write text and choose evidence ids; every claim is re-checked by tradepulse.verify.
"""

from __future__ import annotations

import datetime as dt
import operator
import re
import threading
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from tradepulse.agents import prompts
from tradepulse.ports import LLMPort, QueryPort
from tradepulse.verify import failure_reasons, verify_claim

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "integrations" / "zetaris" / "templates"
PRICE_LOOKBACK_DAYS = 60
FILING_LOOKBACK_DAYS = 45
MAX_CLAIMS = 5
# Approximate regular-session open in UTC per pool; used to place a move_date on the clock.
SESSION_OPEN_UTC = {"us_equity": (13, 30), "eu_equity": (7, 0), "crypto": (0, 0)}
ABSTAIN_SUMMARY = "Insufficient verified evidence; no explanation is offered."


class ExplainState(TypedDict, total=False):
    item: dict
    bundle: dict
    notes: dict
    evidence_text: str
    draft: dict
    feedback: list
    claims: list
    counter_case: list
    ruled_out: list
    retries: int
    models: dict
    explanation: dict
    what_to_watch: list


class RunState(TypedDict):
    items: list
    explanations: Annotated[list, operator.add]


def template_table(template: str) -> str:
    text = (TEMPLATE_DIR / f"{template}.sql").read_text(encoding="utf-8")
    match = re.search(r"\{\{table:(\w+)\}\}", text)
    if match is None:
        raise ValueError(f"template {template} names no table")
    return match.group(1)


def _price_summary(df) -> str:
    if df is None or len(df) == 0:
        return "no rows"
    close = df["adj_close"].astype(float).to_numpy()
    window_ret = close[-1] / close[0] - 1
    ret_5d = close[-1] / close[-6] - 1 if len(close) > 5 else float("nan")
    peak = max(close)
    return (f"{len(df)} daily bars {str(df['date'].iloc[0])[:10]}..{str(df['date'].iloc[-1])[:10]}; "
            f"last adj close {close[-1]:.4g}; window return {window_ret:+.2%}; 5-day return {ret_5d:+.2%}; "
            f"distance to window high {close[-1] / peak - 1:+.2%}")


def _filings_summary(df) -> tuple[str, dict]:
    if df is None or len(df) == 0:
        return "no filings in window", {}
    lines, accessions = [], {}
    for row in df.tail(8).itertuples(index=False):
        accepted = row.acceptance_datetime
        accessions[str(row.accession_number)] = accepted
        items = row.items if isinstance(row.items, str) else "-"
        lines.append(f"{row.accession_number} {row.form} items={items} accepted={accepted}")
    return "; ".join(lines), accessions


def gather_evidence(item: dict, query: QueryPort) -> tuple[dict, dict, str]:
    """Run the allow-listed evidence queries for one name.

    Returns (bundle: evidence_id -> EvidenceRef, notes: evidence_id -> {"accessions": {...}},
    evidence_text for the prompts). A query that fails is reported as unavailable, never invented.
    """
    as_of = dt.date.fromisoformat(item["as_of"])
    symbol = item["symbol"]
    requests = [("price_symbol_window", {"symbol": symbol,
                                         "start": (as_of - dt.timedelta(days=PRICE_LOOKBACK_DAYS)).isoformat(),
                                         "end": as_of.isoformat()})]
    if item["pool"] == "us_equity":
        requests.append(("filings_symbol_window", {"symbol": symbol,
                                                   "start": (as_of - dt.timedelta(days=FILING_LOOKBACK_DAYS)).isoformat(),
                                                   "end": as_of.isoformat()}))
    bundle, notes, lines = {}, {}, []
    slug = re.sub(r"[^a-z0-9]+", "-", symbol.lower()).strip("-")
    for template, params in requests:
        evidence_id = f"ev-{slug}-{template.replace('_', '-')}"
        try:
            result = query.run(template, params)
        except Exception as exc:  # the evidence is simply unavailable
            lines.append(f"[{evidence_id}] unavailable ({type(exc).__name__})")
            continue
        bundle[evidence_id] = {
            "evidence_id": evidence_id, "query_template": template, "params": params,
            "rows_sha256": result.rows_sha256, "source_table": template_table(template),
            "as_of": as_of.isoformat(), "url": None,
        }
        if template == "filings_symbol_window":
            text, accessions = _filings_summary(result.df)
            notes[evidence_id] = {"accessions": accessions}
        else:
            text = _price_summary(result.df)
            notes[evidence_id] = {}
        lines.append(f"[{evidence_id}] {template} {params}: {text}")
    return bundle, notes, "\n".join(lines)


def _move_start(pool: str, move_date: Any, as_of: dt.date) -> dt.datetime | None:
    try:
        day = dt.date.fromisoformat(str(move_date))
    except ValueError:
        return None
    if day > as_of:
        return None
    hour, minute = SESSION_OPEN_UTC[pool]
    return dt.datetime(day.year, day.month, day.day, hour, minute, tzinfo=dt.timezone.utc)


def _cause_time(raw: dict, notes: dict) -> dt.datetime | None:
    accepted = notes.get(raw.get("cause_evidence_id", ""), {}).get("accessions", {}).get(raw.get("cause_accession", ""))
    if accepted is None:
        return None
    ts = accepted if isinstance(accepted, dt.datetime) else dt.datetime.fromisoformat(str(accepted))
    return ts if ts.tzinfo is not None else None


class Explainer:
    """Builds and runs the explanation graph. tracer is optional (tradepulse.trace.Tracer)."""

    def __init__(self, query: QueryPort, llm: LLMPort, *, max_retries: int = 2, tracer=None,
                 max_concurrency: int = 4) -> None:
        self.query, self.llm, self.max_retries = query, llm, max_retries
        self.tracer, self.max_concurrency = tracer, max_concurrency
        self._lock = threading.Lock()
        self.graph = self._build()

    # ------------------------------------------------------------------ tracing
    def _trace(self, item: dict, kind: str, message: str, **extra) -> None:
        if self.tracer is None:
            return
        with self._lock:
            self.tracer.event(f"explain:{item['symbol']}", kind, message=message, **extra)

    def _ask(self, item: dict, role: str, messages: list[dict], schema: dict) -> tuple[dict | None, str]:
        response = self.llm.complete(role, messages, schema)
        self._trace(item, "llm_call", f"{role} answered", model=response.model,
                    tokens_in=response.tokens_in, tokens_out=response.tokens_out,
                    payload={"provider": response.provider, "replayed": response.replayed,
                             "cassette_key": response.cassette_key})
        return prompts.parse_json(response.text), response.model

    # ------------------------------------------------------------------ nodes
    def _gather(self, state: ExplainState) -> dict:
        item = state["item"]
        bundle, notes, text = gather_evidence(item, self.query)
        self._trace(item, "tool_call", f"{len(bundle)} evidence queries", payload={"evidence_ids": sorted(bundle)})
        return {"bundle": bundle, "notes": notes, "evidence_text": text, "retries": 0, "feedback": [],
                "counter_case": [], "ruled_out": [], "models": {"analyst": "none", "skeptic": "none"}}

    def _draft(self, state: ExplainState) -> dict:
        item = state["item"]
        messages = prompts.analyst_messages(item, state["evidence_text"], state.get("feedback", []))
        draft, model = self._ask(item, "analyst", messages, prompts.ANALYST_SCHEMA)
        if draft is None:
            draft = {"summary": "", "claims": [], "what_to_watch": []}
            self._trace(item, "info", "analyst reply was not valid JSON", status="error")
        return {"draft": draft, "models": {**state["models"], "analyst": model}}

    def _challenge(self, state: ExplainState) -> dict:
        item = state["item"]
        messages = prompts.skeptic_messages(item, state["evidence_text"], state["draft"])
        reply, model = self._ask(item, "skeptic", messages, prompts.SKEPTIC_SCHEMA)
        reply = reply or {}
        return {"counter_case": [str(x) for x in reply.get("counter_case", [])][:5],
                "ruled_out": [str(x) for x in reply.get("ruled_out", [])][:5],
                "models": {**state["models"], "skeptic": model}}

    def _verify(self, state: ExplainState) -> dict:
        item, notes = state["item"], state["notes"]
        as_of = dt.date.fromisoformat(item["as_of"])
        claims = []
        for i, raw in enumerate(state["draft"].get("claims", [])[:MAX_CLAIMS]):
            kind = raw.get("kind") if raw.get("kind") in ("factor", "event", "relation", "price", "fundamental") else "price"
            draft = {"claim_id": f"{item['symbol']}-r{state['retries']}-c{i + 1}", "text": str(raw.get("text", ""))[:600],
                     "kind": kind, "evidence_ids": [str(e) for e in raw.get("evidence_ids", [])]}
            claims.append(verify_claim(
                draft, state["bundle"], adapter=self.query, as_of=as_of, score=item["score"],
                contributions=item["contributions"], cause_time=_cause_time(raw, notes),
                move_start=_move_start(item["pool"], raw.get("move_date"), as_of)))
        verified = sum(c["status"] == "verified" for c in claims)
        self._trace(item, "verify", f"{verified}/{len(claims)} claims verified",
                    payload={"rejected": [c["claim_id"] for c in claims if c["status"] != "verified"]})
        feedback = [f"{c['text'][:80]} -> {r}" for c in claims for r in failure_reasons(c)]
        if not claims:
            feedback = ["You made no claims with evidence ids; cite the evidence ids shown."]
        return {"claims": claims, "feedback": feedback}

    def _route_after_verify(self, state: ExplainState) -> str:
        needs_retry = not state["claims"] or any(c["status"] != "verified" for c in state["claims"])
        if needs_retry and state["retries"] < self.max_retries:
            return "retry"
        return "compose"

    def _retry(self, state: ExplainState) -> dict:
        self._trace(state["item"], "retry", f"revising claims, retry {state['retries'] + 1} of {self.max_retries}",
                    payload={"feedback": state["feedback"][:10]})
        return {"retries": state["retries"] + 1}

    def _compose(self, state: ExplainState) -> dict:
        item, claims = state["item"], state.get("claims", [])
        verified = [c for c in claims if c["status"] == "verified"]
        draft = state.get("draft", {})
        explained = bool(verified)
        ruled_out = [str(x) for x in draft.get("ruled_out", [])] + state.get("ruled_out", [])
        explanation = {
            "explanation_id": f"exp-{item['pool']}-{re.sub(r'[^a-z0-9]+', '-', item['symbol'].lower())}",
            "pool": item["pool"], "symbol": item["symbol"],
            "verdict": "explained" if explained else "abstained",
            "summary": (str(draft.get("summary", ""))[:1200] or "See verified claims.") if explained else ABSTAIN_SUMMARY,
            "claims": claims,
            "counter_case": state.get("counter_case", [])[:5],
            "ruled_out": ruled_out[:5],
            "models": state["models"],
            "retries": state["retries"],
        }
        self._trace(item, "info", f"explanation {explanation['verdict']}")
        return {"explanation": explanation,
                "what_to_watch": [str(x) for x in draft.get("what_to_watch", [])][:5]}

    # ------------------------------------------------------------------ graph
    def _build(self):
        sub = StateGraph(ExplainState)
        sub.add_node("gather", self._gather)
        sub.add_node("draft", self._draft)
        sub.add_node("challenge", self._challenge)
        sub.add_node("verify", self._verify)
        sub.add_node("retry", self._retry)
        sub.add_node("compose", self._compose)
        sub.add_edge(START, "gather")
        sub.add_edge("gather", "draft")
        sub.add_conditional_edges("draft", lambda s: "challenge" if s["retries"] == 0 else "verify",
                                  {"challenge": "challenge", "verify": "verify"})
        sub.add_edge("challenge", "verify")
        sub.add_conditional_edges("verify", self._route_after_verify, {"retry": "retry", "compose": "compose"})
        sub.add_edge("retry", "draft")
        sub.add_edge("compose", END)
        one = sub.compile()

        def explain_one(state: dict) -> dict:
            result = one.invoke({"item": state["item"]})
            explanation = dict(result["explanation"])
            return {"explanations": [{"explanation": explanation,
                                      "what_to_watch": result.get("what_to_watch", [])}]}

        def fan_out(state: RunState):
            return [Send("explain_one", {"item": item}) for item in state["items"]]

        outer = StateGraph(RunState)
        outer.add_node("explain_one", explain_one)
        outer.add_conditional_edges(START, fan_out, ["explain_one"])
        outer.add_edge("explain_one", END)
        return outer.compile()

    def run(self, items: list[dict]) -> dict[str, dict]:
        """Explain every item; returns symbol -> {"explanation": Explanation, "what_to_watch": [...]}."""
        if not items:
            return {}
        result = self.graph.invoke({"items": items, "explanations": []},
                                   config={"max_concurrency": self.max_concurrency})
        return {r["explanation"]["symbol"]: r for r in result["explanations"]}
