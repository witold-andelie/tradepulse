"""SD1 Guarding Request: deterministic validation and screening of untrusted text."""

from __future__ import annotations

import datetime as dt
import re

from tradepulse.config import load_config
from tradepulse.contracts import validate_payload


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
    errors = validate_payload(raw, "RunRequest")
    if errors:
        raise GuardRejection("schema", "; ".join(errors[:20]))
    as_of = raw.get("as_of")
    if as_of is not None:
        decision_date = dt.date.fromisoformat(as_of)
        if not earliest <= decision_date <= today:
            raise GuardRejection("as_of", f"as_of must be between {earliest} and {today}")
        as_of = decision_date.isoformat()
    cfg = load_config()
    return {
        "as_of": as_of,
        "pools": list(dict.fromkeys(raw["pools"])),
        "tickers": list(dict.fromkeys(raw.get("tickers", []))),
        "horizon_days": raw.get("horizon_days", cfg["backtest"]["primary_horizon"]),
        "top_k": raw.get("top_k", cfg["explain"]["top_k"]),
    }


def screen_text(text: str) -> list[str]:
    """Rule names that match untrusted free text, in this order when present:
    "instruction_override", "execution_intent", "secret_request". Empty list = clean.
    Used to flag (not block) filing texts before they reach an LLM."""
    rules = (
        ("instruction_override", INSTRUCTION_OVERRIDE),
        ("execution_intent", EXECUTION_INTENT),
        ("secret_request", SECRET_REQUEST),
    )
    return [name for name, pattern in rules if pattern.search(text)]
