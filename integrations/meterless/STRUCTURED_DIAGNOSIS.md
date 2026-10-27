# Nightshift structured-reply diagnosis

Updated 27 October 2026. Evidence below was supplied by the lead from the Mac, not generated
by offline tests. The original failed run and its artifacts must be preserved.

## Current next step: read-only model and resource inventory

Both formatted probes were rejected. The plain-prompt probe then returned invalid JSON
with finish_reason=stop after only 37 output tokens. Stop repeating the current full-schema
request on the current 1B model. A higher token cap is not an evidence-based fix for this
observed early stop. Historical probe commands below remain evidence of the diagnosis,
not instructions to repeat them.

On the Mac, inspect only:

1. GET /v1/models once using the existing ignored configuration and token file, with a
   30-second timeout and no retries. Report only status and actual model IDs, never the token,
   request headers or complete raw body. Do not run nightshift_smoke: it makes a generation call.
2. The installed Nightshift app's model selector/catalog. Distinguish loaded/installed models,
   available downloads and routing aliases. A catalog entry does not prove the model is installed
   or runnable on this Mac. Do not start a download or load a second model.
3. Current macOS memory_pressure (without load-generating flags), sysctl vm.swapusage and
   docker stats --no-stream. Report these as current readings; the older swap total does not
   establish current paging activity.
4. If readily available, the installed bridge's validation code or existing error logs for
   response_format. Read locally and summarize the specific restriction after privacy review.
   Do not modify the app or generate another failed request merely to recreate its body.

Do not restart services, change Docker resources, weaken schemas/verifiers, repair generated
claims or run another probe/pipeline. Use the actual inventory and memory measurements to
choose the next model/provider configuration. Current evidence establishes failure of the
tested model/prompt combination, not universal failure of all 1B models or every JSON format.

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

## Reported first schema probe and next control

The lead reports one webllm_schema probe at 143386e: live price_symbol_window returned
61 rows for WLD-USD, 2026-08-24 through 2026-10-23, with rows_sha256
b12675b09cc3869cbc4dbc658e1155abb1f245ad4c02d919cef56764d5333208.
The subsequent provider request returned HTTP 400 / BadRequestError in 328 ms. No model
reply or finish_reason was returned. The original artifact remains
runs/nightshift-schema-probe-1/report.json on the Mac. The rejection's specific cause
is not established; the first report omitted the error body.

Ranked hypotheses: the nested response_format.schema is rejected; the entire response_format
is rejected; or another field such as temperature causes request validation to fail.
The next control changes only the nested schema field. It keeps the model, prompts,
temperature, output bound and serial request setting the same. A regression verifies that
these two modes produce otherwise identical SDK request arguments.

New HTTP diagnostics include error_signals, extracted from the SDK-parsed body with a fixed
vocabulary. They report known codes, parameter names and message categories, never arbitrary
messages, echoed inputs, credentials or response headers. Empty hints are inconclusive;
message-category matches alone do not prove a root cause.

After updating the branch, execute exactly one control request and stop:

```sh
python3 -m integrations.meterless.structured_probe \
  --env-file ~/getting-started/.env.local \
  --env-file .env.nightshift.local \
  --case-output runs/live-sponsors-crypto-first/crypto/output.json \
  --symbol WLD-USD \
  --response-format json_object \
  --output runs/nightshift-json-object-probe-1
```

Use the same activated environment and exports as the first probe. Preserve all earlier
evidence. Do not automatically retry prompt mode, remove temperature, raise the token cap,
change models or run Crypto acceptance. Report the new report.json and, if generated and
privacy-checked, original reply.json. If it succeeds where the schema mode failed, that
implicates the nested schema handling; it does not prove all schema constraints are unsupported.

## Reported control and plain-prompt outcomes

The lead reports json_object returned HTTP 400 / BadRequestError in 154 ms. Its fixed-vocabulary
error hints contain invalid_request_error and the parameter response_format. No reply was
returned. This narrows investigation toward that parameter but does not establish the exact
restriction; no raw rejection message was provided.

The later prompt-mode request returned a reply in 60,677 ms with finish_reason=stop,
655 input tokens and 37 output tokens. The response SHA-256 is
7a6e937fabca7b1bdb7c79851a07eb03db1942b85e31cc771d9239ad0bc18544.
It contains an extra closing brace, claims as a string rather than an array, and no summary
or what_to_watch. It is not a successful analyst answer. No reference or causal validation
was performed because strict JSON parsing failed. The original artifacts remain in
runs/nightshift-json-object-probe-1/ and runs/nightshift-prompt-probe-1/ on the Mac.
Both have feature_acceptance=false. No Crypto rerun, model change or service adjustment
was reported. Do not repair the reply or treat a schema-shaped reconstruction as model output.
