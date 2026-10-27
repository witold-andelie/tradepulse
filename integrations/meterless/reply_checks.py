"""Strict output diagnostics; this module never repairs or verifies model claims."""

from __future__ import annotations

import json
from itertools import islice

from jsonschema import Draft202012Validator


def _reject_constant(_value):
    raise ValueError("Non-JSON numeric constant")


def inspect_reply(text: str, schema: dict | None,
                  evidence_ids: set[str] | None = None) -> dict:
    """Return bounded, value-free error metadata. Require one complete JSON object.

    Known IDs are checked exactly, without removing suffixes or rewriting references.
    Schema success establishes structure only, never factual or causal correctness.
    """
    if schema is None:
        return {"schema_valid": True, "errors": []}
    try:
        if len(text) > 131072:
            raise ValueError("Response exceeds the diagnostic size limit")
        parsed = json.loads(text, parse_constant=_reject_constant)
        if not isinstance(parsed, dict):
            raise ValueError("Response must be an object")
    except (ValueError, TypeError):
        return {"schema_valid": False, "errors": [{"path": [], "keyword": "json"}]}
    errors = [{"path": list(error.absolute_path), "keyword": error.validator}
              for error in islice(Draft202012Validator(schema).iter_errors(parsed), 12)]
    result = {"schema_valid": not errors, "errors": errors}
    if evidence_ids is not None and not errors:
        claims = parsed.get("claims", [])
        unknown = {item for claim in claims for item in claim.get("evidence_ids", [])
                   if item not in evidence_ids}
        result.update({"unknown_evidence_ids": len(unknown),
                       "causal_claims": sum(claim.get("kind") in {"event", "relation"}
                                            for claim in claims)})
    return result
