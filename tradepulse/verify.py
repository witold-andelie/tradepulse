"""SD1.7 · Verifying Claims: deterministic checks on LLM-drafted claims.

An analyst draft looks like {"claim_id", "text", "kind", "evidence_ids": [...]}. The verifier
never trusts the draft: it re-runs every cited query, checks timing and arithmetic, and returns a
contract Claim with status "verified" only when every check passes.
"""

from __future__ import annotations

import datetime as dt
import math

from tradepulse.ports import QueryPort

TIMED_KINDS = ("event", "relation")


def check(name: str, passed: bool, detail: str) -> dict:
    """A Claim check dict: {"name", "passed": bool, "detail": str}."""
    return {"name": str(name), "passed": bool(passed), "detail": str(detail)}


def check_rerun_hash(evidence: dict, adapter: QueryPort) -> dict:
    """rerun_hash_match: adapter.run(evidence["query_template"], evidence["params"]).rows_sha256 must
    equal evidence["rows_sha256"]. Any exception from the adapter -> passed False with the
    exception type name (not its message) in detail."""
    try:
        actual = adapter.run(evidence["query_template"], evidence["params"]).rows_sha256
        passed = actual == evidence["rows_sha256"]
    except Exception as exc:
        return check("rerun_hash_match", False, type(exc).__name__)
    return check("rerun_hash_match", passed, "hash matches" if passed else "hash mismatch")


def check_no_future_data(evidence: dict, as_of: dt.date) -> dict:
    """no_future_data: evidence["as_of"] <= as_of, and every parameter named start, end or as_of
    (ISO date strings or dates) is <= as_of."""
    dates = {"evidence.as_of": evidence["as_of"]}
    dates.update({f"params.{name}": value for name, value in evidence["params"].items()
                  if name in ("start", "end", "as_of")})
    problems = []
    for name, value in dates.items():
        try:
            day = dt.date.fromisoformat(value) if isinstance(value, str) else value
            if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
                raise ValueError("expected a date")
            if day > as_of:
                problems.append(f"{name} is after as_of")
        except (TypeError, ValueError):
            problems.append(f"{name} is not a valid date")
    return check("no_future_data", not problems, "; ".join(problems) or "dates are on or before as_of")


def check_cause_before_move(cause_time: dt.datetime | None, move_start: dt.datetime | None) -> dict:
    """cause_before_move: both must be timezone-aware and cause_time < move_start.
    A missing value -> passed False, detail "timing unknown"."""
    if cause_time is None or move_start is None:
        return check("cause_before_move", False, "timing unknown")
    if cause_time.utcoffset() is None or move_start.utcoffset() is None:
        return check("cause_before_move", False, "timing must be timezone-aware")
    passed = cause_time < move_start
    return check("cause_before_move", passed,
                 "cause precedes move" if passed else "cause does not precede move")


def check_contributions_sum(contributions: list[dict], score: float, tol: float = 1e-6) -> dict:
    """contributions_sum: abs(sum of contribution - score) <= tol."""
    total = sum(float(item["contribution"]) for item in contributions)
    score, tol = float(score), float(tol)
    passed = (math.isfinite(total) and math.isfinite(score) and math.isfinite(tol)
              and abs(total - score) <= tol)
    return check("contributions_sum", passed,
                 f"contributions sum to {total}; score is {score}; tolerance is {tol}")


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
    evidence, checks = [], []
    if not draft["evidence_ids"]:
        checks.append(check("schema", False, "empty evidence_ids"))
    for evidence_id in draft["evidence_ids"]:
        if evidence_id not in bundle:
            checks.append(check("schema", False, f"unknown evidence id: {evidence_id}"))
            continue
        item = bundle[evidence_id]
        evidence.append(item)
        checks.extend((check_rerun_hash(item, adapter), check_no_future_data(item, as_of)))
    if draft["kind"] == "factor":
        if contributions is None or score is None:
            checks.append(check("contributions_sum", False, "contributions and score are required"))
        else:
            checks.append(check_contributions_sum(contributions, score))
    if draft["kind"] in TIMED_KINDS:
        checks.append(check_cause_before_move(cause_time, move_start))
    return {"claim_id": str(draft["claim_id"]), "text": str(draft["text"]), "kind": str(draft["kind"]),
            "evidence": evidence, "status": "verified" if all(c["passed"] for c in checks) else "rejected",
            "checks": checks}


def failure_reasons(claim: dict) -> list[str]:
    """f"{name}: {detail}" for every failed check, used to ask the analyst to revise."""
    return [f"{item['name']}: {item['detail']}" for item in claim["checks"] if not item["passed"]]
