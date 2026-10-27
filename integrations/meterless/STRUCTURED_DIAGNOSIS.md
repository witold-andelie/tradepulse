# Nightshift structured-reply diagnosis

Updated 27 October 2026. Evidence below was supplied by the lead from the Mac, not generated
by offline tests. The original failed run and its artifacts must be preserved.

## Observations

Zetaris parity passed all 12 templates after 6966b0c. Engine health and Crypto snapshot,
recall and remember succeeded. Run 2026-10-23-ba9fb487 nevertheless failed at validate-case,
with all three explanations abstained. Eleven model replies were returned: eight analyst
replies (one schema-valid) and three skeptic replies (two schema-valid). A further analyst
attempt failed with AllProvidersFailed and did not return a reply.

Three supplied raw replies establish distinct failures:

| Response SHA-256 prefix | Output tokens | Observed failure |
| --- | ---: | --- |
| fae6b2d1 | 428 | Unclosed outer object; missing summary and what_to_watch; invented references and causal statements |
| 9222384c | 767 | A complete object followed by an incomplete second object; all three initial claims omit kind |
| c1dc43b4 | 537 | Base schema passes, but all four claims fail verification; unknown evidence ID and unknown causal timing |

The old core parser can recover the first complete object from some incomplete documents.
Live acceptance now requires one complete JSON object and records bounded schema paths and
validator keywords. No core parser, contract, original test or verification gate was changed.
Tests use explicitly synthetic minimal reproductions, not fabricated service logs.

The 767-token reply is close to the configured 768 cap. The 428-token reply is also incomplete,
so a token-cap explanation alone is insufficient. The historical receipts lack finish_reason;
the provider-level cause of the final AllProvidersFailed is unknown. New model_requests.jsonl
receipts record stop reason, response hash, queue/request milliseconds and error type/HTTP
status without exception bodies, prompts or tokens. Existing models.jsonl elapsed_ms includes
queueing, not just inference time.

## Optional output constraint

METERLESS_RESPONSE_FORMAT accepts prompt (default), json_object or webllm_schema.
Only the Nightshift route uses this setting. The latter sends:

    response_format = {"type": "json_object", "schema": json.dumps(requested_schema)}

This is the documented [WebLLM response format](https://github.com/mlc-ai/web-llm/blob/main/src/openai_api_protocols/chat_completion.ts),
not proof that Nightshift's installed bridge forwards it. Structured requests also use
temperature=0 and retain the schema instruction. Unsupported requests fail once, without
silently reverting to an unconstrained request. No reply is repaired, no kind is filled in
and no evidence ID is mapped to a convenient existing ID. Syntax constraints cannot establish
financial or causal truth; the existing verification must still run.

## One-request Mac diagnostic

Use the existing model and private configuration. Do not load another model, restart Zetaris,
increase Docker memory or start the US filing workload. Memory pressure was yellow and swap
grew during the failed run. From the updated TradePulse checkout:

```sh
source .venv/bin/activate
export ZETARIS_API_MODE=proxy
export ZETARIS_BASE_URL=http://localhost:3000
export METERLESS_MAX_TOKENS=768
python3 -m integrations.meterless.structured_probe \
  --env-file ~/getting-started/.env.local \
  --env-file .env.nightshift.local \
  --case-output runs/live-sponsors-crypto-first/crypto/output.json \
  --symbol WLD-USD \
  --response-format webllm_schema \
  --output runs/nightshift-schema-probe-1
```

The symbol is taken from the actual failed run, not a hard-coded output. The command selects
its computed recommendation, reconstructs the pool count/date, queries fresh allow-listed
Zetaris evidence and makes at most one analyst request, with one provider and no retries.
It deliberately omits old H-MEM context to isolate evidence-following from historical context.
No skeptic, engine write, parity sweep, extraction or full pipeline runs.

The new directory contains queries.jsonl, report.json and, if a reply passed the local privacy
check, reply.json with its original text. Old evidence is never overwritten. report.json
always sets feature_acceptance=false. A reply_checks_ok result only means complete JSON,
the unchanged analyst schema, known cited IDs and no causal claim when all evidence is price.
It does not prove grammar enforcement, narrative truth, complete evidence support or case success.

Stop after this request and inspect the report and original reply locally:

- HTTP 400/422: preserve the report; the format may be rejected by the bridge. Do not retry
  the full pipeline. An explicit json_object probe in a fresh directory is a separate choice.
- finish_reason=length: truncation is observed; examine output size before adjusting the bound.
- Valid JSON with invented references/causality: syntax support does not resolve grounding.
- Apparently valid references: review the narrative against the evidence before a full retry.

Current verification rechecks hashes, dates, references and applicable factor/timing gates.
It is not a general natural-language entailment checker. In particular, correct price evidence
IDs alone do not prove every sentence in a price claim. Do not label a reply factually verified
based only on this diagnostic or remap references to make existing gates pass.

Only after diagnosis and review should the lead rerun Crypto acceptance with an explicitly
chosen format, using a new output directory. Full submission acceptance still needs three
real pool cases, reviewed original traces and privacy-checked sample artifacts.
