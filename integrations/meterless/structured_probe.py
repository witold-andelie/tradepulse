"""One real analyst request using an existing REAL recommendation and fresh Zetaris evidence.

This diagnostic does not run the pipeline, extraction, engines or retries. Success checks
JSON and references only; it is not feature acceptance or proof of factual correctness.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from tradepulse.agents.explain import gather_evidence
from tradepulse.agents.prompts import ANALYST_SCHEMA, analyst_messages
from tradepulse.contracts import REPO_ROOT, assert_payload

from integrations.environment import load_private_env
from integrations.live_acceptance import AuditedQueries, write_json
from integrations.zetaris.adapter import ZetarisAdapter
from integrations.zetaris.client import ZetarisClient

from .llm import ChainClient, build_routes_from_env, read_token
from .reply_checks import inspect_reply


def select_item(path: Path, symbol: str) -> dict:
    if path.stat().st_size > 10485760:
        raise ValueError("Case output exceeds the probe size limit")
    output = json.loads(path.read_text(encoding="utf-8"))
    assert_payload(output, "RunOutput")
    if output["sample_mode"] or output["data_mode"] != "REAL":
        raise ValueError("Probe requires an existing REAL output, never a synthetic example")
    matches = [item for item in output["recommendations"] if item["symbol"] == symbol]
    if len(matches) != 1:
        raise ValueError("Choose one unambiguous symbol from the existing output")
    item = matches[0]
    # Reconstruct the same computed context as the pipeline's explanation input.
    return {**item, "as_of": output["as_of"],
            "n": sum(row["pool"] == item["pool"] for row in output["recommendations"])}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, action="append", default=[])
    parser.add_argument("--case-output", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--response-format", choices=("prompt", "json_object", "webllm_schema"),
                        required=True)
    parser.add_argument("--output", type=Path, required=True, help="new directory under runs/")
    args = parser.parse_args(argv)
    destination = args.output.resolve()
    if not destination.is_relative_to(REPO_ROOT / "runs") or destination.exists():
        raise ValueError("Choose a new probe directory under runs/; old evidence is preserved")
    item = select_item(args.case_output.expanduser(), args.symbol)
    for path in args.env_file:
        load_private_env(path.expanduser())
    token = read_token(os.environ["METERLESS_TOKEN_FILE"])
    secrets = [token, os.environ.get("ZETARIS_API_KEY", ""),
               os.environ.get("ZETARIS_PASSWORD", ""), os.environ.get("ENGINES_TOKEN", "")]
    os.environ["METERLESS_MAX_CONCURRENCY"] = "1"
    os.environ["METERLESS_RESPONSE_FORMAT"] = args.response_format
    diagnostics = []
    routes = {role: [route for route in values if route[0] == "meterless"]
              for role, values in build_routes_from_env(diagnostics=diagnostics.append).items()}
    if len(routes.get("analyst", [])) != 1:
        raise ValueError("Probe requires exactly one Nightshift route")
    destination.mkdir(parents=True)
    report = {"status": "failed", "feature_acceptance": False, "symbol": item["symbol"],
              "as_of": item["as_of"], "response_format": args.response_format,
              "request_limit": 1, "diagnostics": diagnostics}
    try:
        query = AuditedQueries(ZetarisAdapter(ZetarisClient.from_env()), destination / "queries.jsonl")
        bundle, _, evidence_text = gather_evidence(item, query)
        if not bundle:
            raise ValueError("No live evidence is available")
        messages = analyst_messages(item, evidence_text, [])
        response = ChainClient(routes, None, mode="live").complete("analyst", messages, ANALYST_SCHEMA)
        write_json(destination / "reply.json", {"text": response.text,
                   "provider": response.provider, "model": response.model,
                   "cassette_key": response.cassette_key, "tokens_in": response.tokens_in,
                   "tokens_out": response.tokens_out}, secrets)
        checked = inspect_reply(response.text, ANALYST_SCHEMA, set(bundle))
        only_price = all(entry["query_template"] == "price_symbol_window" for entry in bundle.values())
        ready = (checked["schema_valid"] and checked.get("unknown_evidence_ids") == 0
                 and not (only_price and checked.get("causal_claims")))
        report.update(checked, status="reply_checks_ok" if ready else "failed",
                      only_price_evidence=only_price,
                      note="JSON and references only; factual and causal correctness are not certified.")
    except Exception as error:
        report["failure_type"] = type(error).__name__
    write_json(destination / "report.json", report, secrets)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "reply_checks_ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
