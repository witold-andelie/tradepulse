"""Opt-in World Model/H-MEM orchestration against the agreed sidecar HTTP interface.

Injected ports support offline tests. Environment-based HTTP activation is live-only.
No engine output bypasses the existing research gates or claim verifier.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
from copy import deepcopy
from urllib.parse import urlsplit

import pandas as pd

from quant import settlement
from tradepulse.contracts import assert_payload
from tradepulse.ports import EnginesPort

MAX_WORLD_ITEMS = 5000
MAX_FOCUS = 100
MAX_RECORDS = 1000
RECALL_K = 10


class EngineIntegrationError(RuntimeError):
    """A configured engine failed; the run must not claim successful persistence."""


def configured_engines(is_sample: bool) -> EnginesPort | None:
    """Never construct an HTTP client in SAMPLE_MODE, even if engine variables are set."""
    if is_sample:
        return None
    enabled = os.getenv("ENGINES_ENABLED", "false").strip().lower()
    if enabled in {"false", "0", "no", "off"}:
        return None
    if enabled not in {"true", "1", "yes", "on"}:
        raise ValueError("ENGINES_ENABLED must be a boolean")
    url = os.getenv("ENGINES_URL", "").strip()
    parsed = urlsplit(url)
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1", "engines"}
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.scheme not in {"http", "https"} or (parsed.scheme == "http" and not local)):
        raise ValueError("Engines require HTTPS, or HTTP on a local sidecar address")
    from integrations.meterless.engines_client import EnginesClient

    return EnginesClient(url, timeout_s=10.0)


def _bounded(values, limit):
    if not isinstance(values, list) or len(values) > limit:
        raise ValueError("Engine list exceeds the agreed local work limit")
    return values


def _count(payload, key, maximum):
    value = payload.get(key) if isinstance(payload, dict) else None
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError("Invalid engine acknowledgement")
    return value


class EngineBridge:
    def __init__(self, port: EnginesPort, as_of: str, tracer) -> None:
        self.port, self.as_of, self.tracer = port, dt.date.fromisoformat(as_of), tracer

    def _safe(self, operation, work):
        try:
            return work()
        except Exception as exc:
            message = f"Meterless {operation} failed ({type(exc).__name__})"
            self.tracer.event("meterless", "error", status="error", message=message)
            raise EngineIntegrationError(message) from None

    def _invoke(self, operation, *args, **kwargs):
        result = getattr(self.port, operation)(*args, **kwargs)
        self.tracer.event("meterless", "tool_call", message=f"{operation} returned",
                          payload={"operation": operation})
        return result

    def _world_items(self, values, definition):
        items = _bounded(values, MAX_WORLD_ITEMS)
        ids = set()
        for item in items:
            assert_payload(item, definition)
            key = "event_id" if definition == "ExtractedEvent" else "edge_id"
            if item[key] in ids:
                raise ValueError("Duplicate World Model identity")
            ids.add(item[key])
            if definition == "ExtractedEvent":
                available = dt.datetime.fromisoformat(item["available_at"].replace("Z", "+00:00"))
                cutoff = dt.datetime.combine(self.as_of + dt.timedelta(days=1), dt.time(), dt.UTC)
                if available.utcoffset() is None or available >= cutoff:
                    raise ValueError("World Model event is unavailable as of the run")
            elif dt.date.fromisoformat(item["valid_from"]) > self.as_of:
                raise ValueError("World Model edge is unavailable as of the run")
        return deepcopy(items)

    def world_snapshot(self, events, edges):
        """Commit grounded events/validated edges, then use the validated as-of snapshot."""
        def work():
            checked_events = self._world_items(events, "ExtractedEvent")
            checked_edges = self._world_items(edges, "GraphEdge")
            checked_edges = [edge for edge in checked_edges if edge["status"] == "validated"]
            if checked_events:
                receipt = self._invoke("ingest_events", checked_events)
                ingested = _count(receipt, "ingested", len(checked_events))
                duplicates = _count(receipt, "duplicates", len(checked_events))
                if ingested + duplicates != len(checked_events):
                    raise ValueError("Incomplete event acknowledgement")
            if checked_edges:
                _count(self._invoke("upsert_edges", checked_edges), "upserted", len(checked_edges))
            snapshot = self._invoke("snapshot", self.as_of.isoformat())
            if not isinstance(snapshot, dict) or snapshot.get("as_of") != self.as_of.isoformat():
                raise ValueError("Snapshot decision date mismatch")
            found_events = self._world_items(snapshot.get("events"), "ExtractedEvent")
            found_edges = self._world_items(snapshot.get("edges"), "GraphEdge")
            if not {item["event_id"] for item in checked_events} <= {item["event_id"] for item in found_events}:
                raise ValueError("Acknowledged events missing from snapshot")
            if not {item["edge_id"] for item in checked_edges} <= {item["edge_id"] for item in found_edges}:
                raise ValueError("Acknowledged edges missing from snapshot")
            return found_events, [edge for edge in found_edges if edge["status"] == "validated"]
        return self._safe("world_snapshot", work)

    def _record(self, record, symbol=None):
        required = {"id", "symbol", "as_of", "tier", "horizon_days", "content", "provenance"}
        if not isinstance(record, dict) or not required <= record.keys():
            raise ValueError("Incomplete memory record")
        if not isinstance(record["id"], str) or not 1 <= len(record["id"]) <= 128:
            raise ValueError("Invalid memory identity")
        if symbol is not None and record["symbol"] != symbol:
            raise ValueError("Memory symbol mismatch")
        record_date = dt.date.fromisoformat(record["as_of"])
        if record_date.isoformat() != record["as_of"] or record_date > self.as_of:
            raise ValueError("Future memory record")
        horizon = record["horizon_days"]
        if type(horizon) is not int or not 1 <= horizon <= 252:
            raise ValueError("Invalid memory horizon")
        settlement.hit(record["tier"], 0.0)  # Validate the existing research-stance vocabulary.
        return record

    def prior_context(self, items):
        """Use bounded dated record counts as unverified context, never as claim evidence.

        /hmem/conflicts has no as_of argument or declared dated response shape. Do not feed
        that unscoped response to a historical run or invent a response schema for it.
        """
        def work():
            _bounded(items, MAX_RECORDS)
            result = []
            for index, item in enumerate(items):
                if index >= MAX_FOCUS:
                    self.tracer.event("meterless", "info", message="Recall work limit reached",
                                      payload={"focus_items": len(items), "recall_limit": MAX_FOCUS})
                    result.extend(deepcopy(items[index:]))
                    break
                records = _bounded(self._invoke("recall", item["symbol"], self.as_of.isoformat(),
                                                k=RECALL_K), RECALL_K)
                ids = set()
                for record in records:
                    self._record(record, item["symbol"])
                    if record["id"] in ids:
                        raise ValueError("Duplicate memory record")
                    ids.add(record["id"])
                result.append({**deepcopy(item), "memory_context": {
                    "prior_record_count": len(records), "verified_evidence": False,
                }})
            return result
        return self._safe("recall", work)

    def remember(self, output, execution_lag):
        """Write pending research records with stable per-run identities and original values."""
        def work():
            rows = _bounded(output["recommendations"], MAX_RECORDS)
            explanations = {item["explanation_id"]: item
                            for item in _bounded(output["explanations"], MAX_RECORDS)}
            records = []
            for row in rows:
                identity = [output["run_id"], row["pool"], row["symbol"], output["as_of"], row["horizon_days"]]
                explanation = explanations.get(row["explanation_id"], {})
                evidence = sorted({ref["evidence_id"] for claim in explanation.get("claims", [])
                                   if claim["status"] == "verified" for ref in claim["evidence"]})
                record = {"id": hashlib.sha256(json.dumps(identity).encode()).hexdigest(),
                          "symbol": row["symbol"], "as_of": output["as_of"], "tier": row["tier"],
                          "horizon_days": row["horizon_days"],
                          "content": {"pool": row["pool"], "recommendation": deepcopy(row),
                                      "execution_lag_days": execution_lag, "data_mode": output["data_mode"]},
                          "provenance": {"run_id": output["run_id"], "evidence_ids": evidence}}
                records.append(self._record(record))
            if records:
                _count(self._invoke("remember", records), "added", len(records))
            return records
        return self._safe("remember", work)

    def feedback(self, record, prices: pd.Series, benchmark: pd.Series):
        """Settle one explicitly selected pending record using observed, matured prices.

        Returns False without a request when observations are incomplete. The caller owns
        pending selection and idempotency; the current API does not specify those semantics.
        """
        def work():
            self._record(record)
            content = record["content"]
            lag = content.get("execution_lag_days") if isinstance(content, dict) else None
            if type(lag) is not int or not 0 <= lag <= 20:
                raise ValueError("Missing historical execution lag")
            if (not isinstance(prices.index, pd.DatetimeIndex) or prices.index.tz is not None
                    or not prices.index.is_monotonic_increasing or not prices.index.is_unique
                    or not benchmark.index.is_unique):
                raise ValueError("Settlement prices require unique sorted sessions")
            decision = pd.Timestamp(record["as_of"])
            if decision not in prices.index:
                return False
            entry = int(prices.index.get_loc(decision)) + lag
            exit_row = entry + record["horizon_days"]
            if exit_row >= len(prices) or prices.index[exit_row].date() > self.as_of:
                return False
            dates = [prices.index[entry], prices.index[exit_row]]
            values = [prices.loc[day] for day in dates] + [benchmark.get(day) for day in dates]
            if any(pd.isna(value) or not math.isfinite(float(value)) or float(value) <= 0 for value in values):
                return False
            excess = settlement.excess_return(*map(float, values))
            outcome = {"excess_return": excess, "hit": settlement.hit(record["tier"], excess)}
            receipt = self._invoke("settle", record["id"], outcome)
            if _count(receipt, "updated", 1) != 1:
                raise ValueError("Feedback was not acknowledged")
            return True
        return self._safe("feedback", work)
