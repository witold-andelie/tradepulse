"""Python client for the Node engines sidecar (task D5). The HTTP API is specified in
integrations/engines/API.md. Every method validates its payloads against contracts where a
contract exists (GraphEdge, ExtractedEvent) before sending."""

from __future__ import annotations

import datetime as dt
import math
import os
import re

import requests

from tradepulse.contracts import validate_payload


class EnginesError(RuntimeError):
    pass


class EnginesClient:
    def __init__(self, base_url: str, timeout_s: float = 30.0, session=None) -> None:
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("Timeout must be finite and positive")
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self._session = session if session is not None else requests.Session()
        self._token = os.environ.get("ENGINES_TOKEN")

    def _request(self, method: str, path: str, **kwargs) -> dict:
        if self._token:
            kwargs["headers"] = {"Authorization": f"Bearer {self._token}"}
        try:
            response = getattr(self._session, method)(
                f"{self.base_url}{path}", timeout=self.timeout_s, **kwargs
            )
        except Exception as error:
            raise EnginesError(f"Engines request failed ({type(error).__name__})") from None
        if not 200 <= response.status_code < 300:
            raise EnginesError(f"Engines returned HTTP {response.status_code}")
        try:
            payload = response.json()
        except ValueError:
            raise EnginesError("Engines returned invalid JSON") from None
        if not isinstance(payload, dict):
            raise EnginesError("Engines response must be an object")
        return payload

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
        """POST /hmem/records (recommendations to remember)."""
        return self._request("post", "/hmem/records", json={"records": records})

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
