"""SD1 · Recommending: one full run. Owned by the team lead.

The API and run.py call run_pipeline(request) and nothing else from here.
"""

from __future__ import annotations


def run_pipeline(request: dict) -> dict:
    """Execute one run for a guarded RunRequest and return a contract-valid RunOutput."""
    raise NotImplementedError("pipeline is implemented by the team lead")
