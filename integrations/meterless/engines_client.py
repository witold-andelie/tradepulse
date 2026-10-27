"""Python client for the Node engines sidecar (task D5). The HTTP API is specified in
integrations/engines/API.md. Every method validates its payloads against contracts where a
contract exists (GraphEdge, ExtractedEvent) before sending."""

from __future__ import annotations

import datetime as dt
import math
import os
import re
from time import perf_counter

import requests

from tradepulse.contracts import validate_payload


class EnginesError(RuntimeError):
    def __init__(self, message: str, *, error_type=None, http_status=None):
        super().__init__(message)
        self.error_type, self.http_status = error_type, http_status


class EnginesClient:
    def __init__(self, base_url: str, timeout_s: float = 30.0, session=None) -> None:
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("Timeout must be finite and positive")
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self._session = session if session is not None else requests.Session()
        self._token = os.environ.get("ENGINES_TOKEN")
        self.observer = None

    def _request(self, method: str, path: str, *, timeout_s=None, **kwargs) -> dict:
        if self._token:
            kwargs["headers"] = {"Authorization": f"Bearer {self._token}"}
        timeout = self.timeout_s if timeout_s is None else timeout_s
        started = perf_counter()
        receipt = {"method": method.upper(), "path": path, "timeout_seconds": timeout,
                   "at": dt.datetime.now(dt.UTC).isoformat()}
        if path == "/hmem/records":
            receipt["batch_records"] = len(kwargs["json"]["records"])
        try:
            try:
                response = getattr(self._session, method)(
                    f"{self.base_url}{path}", timeout=timeout, **kwargs
                )
            except Exception as error:
                raise EnginesError(f"Engines request failed ({type(error).__name__})",
                                   error_type=type(error).__name__) from None
            receipt["http_status"] = response.status_code
            if not 200 <= response.status_code < 300:
                raise EnginesError(f"Engines returned HTTP {response.status_code}",
                                   error_type="HTTPError", http_status=response.status_code)
            try:
                payload = response.json()
            except ValueError:
                raise EnginesError("Engines returned invalid JSON", error_type="InvalidJSON") from None
            if not isinstance(payload, dict):
                raise EnginesError("Engines response must be an object", error_type="InvalidResponse")
            receipt["status"] = "ok"
            return payload
        except EnginesError as error:
            receipt.update(status="error", error_type=error.error_type)
            raise
        finally:
            if self.observer is not None:
                receipt["elapsed_ms"] = int((perf_counter() - started) * 1000)
                self.observer(receipt)

    @staticmethod
    def _date(value: str) -> str:
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("as_of must be an ISO date")
        try:
            return dt.date.fromisoformat(value).isoformat()
        except ValueError:
            raise ValueError("as_of must be an ISO date") from None

    @staticmethod
    def _validate(items: list[dict], definition: str) -> None:
        if not isinstance(items, list):
            raise ValueError(f"{definition} payload must be a list")
        for item in items:
            if validate_payload(item, definition):
                raise ValueError(f"Invalid {definition} payload")

    @staticmethod
    def _list(payload: dict, key: str) -> list[dict]:
        values = payload.get(key)
        if not isinstance(values, list) or any(not isinstance(value, dict) for value in values):
            raise EnginesError(f"Engines response requires a list of objects: {key}")
        return values

    def health(self) -> dict:
        return self._request("get", "/health")

    def ingest_events(self, events: list[dict]) -> dict:
        """POST /world-model/events. Each event satisfies $defs/ExtractedEvent; invalid -> ValueError."""
        self._validate(events, "ExtractedEvent")
        return self._request("post", "/world-model/events", json={"events": events})

    def upsert_edges(self, edges: list[dict]) -> dict:
        """POST /world-model/edges. Each edge satisfies $defs/GraphEdge; invalid -> ValueError."""
        self._validate(edges, "GraphEdge")
        return self._request("post", "/world-model/edges", json={"edges": edges})

    def snapshot(self, as_of: str) -> dict:
        """GET /world-model/snapshot?as_of=YYYY-MM-DD -> {"edges": [...], "events": [...]}."""
        return self._request("get", "/world-model/snapshot", params={"as_of": self._date(as_of)})

    def remember(self, records: list[dict]) -> dict:
        """Bounded optional batches; never automatically repeat a write with unknown outcome."""
        if not isinstance(records, list) or len(records) > 5000 or any(not isinstance(r, dict) for r in records):
            raise ValueError("Memory writes require at most 5000 objects")
        try:
            batch_size = int(os.environ.get("ENGINES_REMEMBER_BATCH_SIZE", "5000"))
            write_timeout = float(os.environ.get("ENGINES_WRITE_TIMEOUT_SECONDS", str(self.timeout_s)))
        except ValueError:
            raise ValueError("Engine write settings must be numeric") from None
        if not 1 <= batch_size <= 5000 or not math.isfinite(write_timeout) or not 0 < write_timeout <= 300:
            raise ValueError("Engine write settings exceed their bounds")
        added = 0
        for start in range(0, len(records), batch_size):
            batch = records[start:start + batch_size]
            receipt = self._request("post", "/hmem/records", timeout_s=write_timeout,
                                    json={"records": batch})
            count = receipt.get("added")
            if type(count) is not int or not 0 <= count <= len(batch):
                raise EnginesError("Invalid H-MEM write acknowledgement", error_type="InvalidResponse")
            added += count
        return {"added": added}

    def recall(self, symbol: str, as_of: str, k: int = 10) -> list[dict]:
        """POST /hmem/query."""
        if type(k) is not int or k <= 0:
            raise ValueError("k must be a positive integer")
        payload = self._request("post", "/hmem/query",
                                json={"symbol": symbol, "as_of": self._date(as_of), "k": k})
        return self._list(payload, "records")

    def settle(self, record_id: str, outcome: dict) -> dict:
        """POST /hmem/feedback."""
        return self._request("post", "/hmem/feedback", json={"id": record_id, "outcome": outcome})

    def conflicts(self, symbol: str) -> list[dict]:
        """GET /hmem/conflicts?symbol=..."""
        return self._list(self._request("get", "/hmem/conflicts", params={"symbol": symbol}),
                          "conflicts")
