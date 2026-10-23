"""SD1 · Guarding Request: deterministic validation of run requests and screening of untrusted text."""

from __future__ import annotations

import datetime as dt
import re


class GuardRejection(ValueError):
    """A request was rejected. `code` is one of: "schema", "as_of"."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


EXECUTION_INTENT = re.compile(
    r"\b(buy|sell|place|execute|submit|route)\b[^.\n]{0,40}\b(orders?|trades?|positions?)\b"
    r"|\b(go long|go short|short[- ]sell)\b",
    re.IGNORECASE,
)
INSTRUCTION_OVERRIDE = re.compile(
    r"\b(ignore|disregard|forget)\b[^.\n]{0,30}\b(instructions?|prompts?|rules?)\b"
    r"|\byou are now\b|\bsystem prompt\b",
    re.IGNORECASE,
)
SECRET_REQUEST = re.compile(r"\b(api[ _-]?key|password|access token|secret key)\b", re.IGNORECASE)


def guard_request(raw: dict, *, today: dt.date, earliest: dt.date) -> dict:
    """Validate and normalise a RunRequest.

    - raw must satisfy contracts $defs/RunRequest, else GuardRejection("schema", <first errors>).
    - Defaults: horizon_days = config backtest.primary_horizon, top_k = config explain.top_k,
      tickers = [], as_of = None (None means "latest available"; it is kept as None).
    - A given as_of must satisfy earliest <= as_of <= today, else GuardRejection("as_of", ...).
    - pools and tickers are de-duplicated, keeping their first-seen order.
    - Returns a new dict with exactly the keys as_of (ISO string or None), pools, tickers,
      horizon_days, top_k. The input is not modified.
    """
    raise NotImplementedError


def screen_text(text: str) -> list[str]:
    """Rule names that match untrusted free text, in this order when present:
    "instruction_override", "execution_intent", "secret_request". Empty list = clean.
    Used to flag (not block) filing texts before they reach an LLM."""
    raise NotImplementedError
