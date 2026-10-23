"""SD1.7 · Verifying Claims: deterministic checks on LLM-drafted claims.

An analyst draft looks like {"claim_id", "text", "kind", "evidence_ids": [...]}. The verifier
never trusts the draft: it re-runs every cited query, checks timing and arithmetic, and returns a
contract Claim with status "verified" only when every check passes.
"""

from __future__ import annotations

import datetime as dt

from tradepulse.ports import QueryPort

TIMED_KINDS = ("event", "relation")


def check(name: str, passed: bool, detail: str) -> dict:
    """A Claim check dict: {"name", "passed": bool, "detail": str}."""
    raise NotImplementedError


def check_rerun_hash(evidence: dict, adapter: QueryPort) -> dict:
    """rerun_hash_match: adapter.run(evidence["query_template"], evidence["params"]).rows_sha256 must
    equal evidence["rows_sha256"]. Any exception from the adapter -> passed False with the
    exception type name (not its message) in detail."""
    raise NotImplementedError


def check_no_future_data(evidence: dict, as_of: dt.date) -> dict:
    """no_future_data: evidence["as_of"] <= as_of, and every parameter named start, end or as_of
    (ISO date strings or dates) is <= as_of."""
    raise NotImplementedError


def check_cause_before_move(cause_time: dt.datetime | None, move_start: dt.datetime | None) -> dict:
    """cause_before_move: both must be timezone-aware and cause_time < move_start.
    A missing value -> passed False, detail "timing unknown"."""
    raise NotImplementedError


def check_contributions_sum(contributions: list[dict], score: float, tol: float = 1e-6) -> dict:
    """contributions_sum: abs(sum of contribution - score) <= tol."""
    raise NotImplementedError


def verify_claim(draft: dict, bundle: dict[str, dict], *, adapter: QueryPort, as_of: dt.date,
                 score: float | None = None, contributions: list[dict] | None = None,
                 cause_time: dt.datetime | None = None, move_start: dt.datetime | None = None) -> dict:
    """Turn a draft into a contract Claim.

    - Evidence: each id in draft["evidence_ids"] must exist in bundle (id -> EvidenceRef). An
      unknown id or an empty list adds a failed "schema" check (detail names the problem), and the
      claim cannot be verified.
    - For each known evidence item: check_rerun_hash and check_no_future_data.
    - kind "factor": check_contributions_sum(contributions, score) (both required; a missing one
      fails the check).
    - kind in TIMED_KINDS: check_cause_before_move(cause_time, move_start).
    - status = "verified" if every check passed, else "rejected".
    - Output keys: claim_id, text, kind, evidence (list of EvidenceRef from the bundle, in draft
      order, unknown ids skipped), status, checks. The result satisfies $defs/Claim.
    """
    raise NotImplementedError


def failure_reasons(claim: dict) -> list[str]:
    """f"{name}: {detail}" for every failed check, used to ask the analyst to revise."""
    raise NotImplementedError
