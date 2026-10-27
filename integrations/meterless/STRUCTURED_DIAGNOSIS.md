# Nightshift structured-reply diagnosis

Updated 27 October 2026. Evidence below was supplied by the lead from the Mac, not generated
by offline tests. The original failed run and its artifacts must be preserved.

## Current decision: stop local-model diagnosis and use hosted GLM

The lead supersedes the diagnostic plans below. No additional Nightshift raw text, model
trial, timeout experiment or local inference is needed to enter hosted product acceptance.
Keep the original failed HTTP reports and separate real runtime completion evidence as they
are. Follow [HOSTED_ACCEPTANCE.md](../HOSTED_ACCEPTANCE.md) for GLM inference, live Zetaris
queries and actual Meterless engine operations. Do not label a GLM answer as Nightshift.
The plans below describe the investigation history, not new work to execute.

## Previous plan: offline review of the retained late response (historical)

The lead located the existing Qwen job's late completion. It finished in the runtime after
267,437 ms, versus the client's 180,153 ms timeout, an approximately 87.3-second difference.
The lane is now ready/idle. Do not repeat a model request yet. Inspect the retained original
reply for complete JSON, exact evidence references and supported descriptive statements.
The lead reports an unsupported investor-optimism causal explanation; a correct price
reference alone would not establish that cause. Full raw model text is still needed for
the offline review. Do not repair it or mark it financially verified based on receipt success.

The client now supports METERLESS_TIMEOUT_SECONDS (integer 1-600, default 180) and
METERLESS_QUEUE_TIMEOUT_SECONDS (integer 1-1800, default 180). A future reviewed trial can
explicitly use 360 seconds for the SDK timeout, based on the observed 267-second completion.
Serial multi-name work may also need a longer queue budget (for example 1200 seconds) so
waiting names do not fail before an earlier slow request finishes. These settings do not
authorize a new trial or change any answer-quality gate; new inference awaits raw-reply review.

The SDK timeout configures bounded HTTP operations, not a strict wall-clock deadline for an
entire pipeline. Local queue wait is separate, and SDK automatic retries remain disabled.
Both budgets are included in new request receipts. Defaults preserve the original behavior.
Client timeout still does not certify remote cancellation; confirm runtime idle before any
subsequent call. No late artifact may be inserted into the missing client reply.json.

## Completed runtime investigation request (historical)

The selected Qwen model is now downloaded, the only resident model, and reported ready at
about 2.2 GB. Its single prompt probe timed out after 180,153 ms with APITimeoutError.
No reply was received and no feature acceptance passed. Do not repeat the loading/probe
commands below. The current step is inspection of this existing request, not new inference.

Ranked hypotheses to distinguish:

1. Nightshift is still queueing or generating after the client stopped waiting.
2. WebGPU compilation, prefill or decode is stalled or failed.
3. The backend completed but the proxy did not return the reply to the HTTP client.

queue_ms=0 measures only TradePulse's local semaphore, not Nightshift's internal queue.
An idle/ready lane before a request does not establish that it generated tokens afterward.
Green observed memory pressure does not prove or exclude a runtime stall. A client timeout
does not establish cancellation or a failed JSON answer.

On the Mac, perform the following bounded investigation without new generation:

- Inspect Nightshift's existing Jobs/Lanes/history and local logs for the one tradepulse
  Qwen request. Identify the request by available app/model/time metadata. Use the report
  file timestamp only as an approximate interval if no real request timestamp is available.
  Record actual status: queued, prefill, generating, completed, failed or unknown. Report
  existing first-token/decode/error evidence only when recorded; do not invent timings.
- Read the installed app's actual /v1/chat/completions handler and its webllm call path.
  Check where it queues, when it loads/compiles, whether max_tokens is forwarded, and whether
  client disconnection invokes cancellation. Inspect existing WebGPU errors or progress
  records. Do not assume OpenAI parameter forwarding or invent an undocumented API route.
- Determine whether the exact timed-out request is still running. Preserve evidence first.
  If clearly identified and still active, use an existing supported UI cancel/stop control
  for that request alone. Do not cancel unrelated work or restart Nightshift/Zetaris/Docker.
  If request identity or cancellation support is unclear, report it without guessing.
- If the existing job completed and retained original output, preserve it separately as a
  late-runtime artifact with its actual source ID/status/timestamps and SHA-256 after privacy
  review. Do not create the missing client reply.json or change the failed probe report.
  Late completion is distinct from a successful HTTP request within the existing bound.
- Capture current lane status and memory pressure/swap. Distinguish recorded task outcomes
  from inference based on snapshots. Stop after the evidence review and any targeted cancel.

No new model request, download, model switch, timeout extension, app patch, schema repair or
Crypto run is part of this step. Do not invoke nightshift_smoke, which generates a reply.
The next implementation change must follow evidence locating the stall or response failure.

## Completed Qwen selection and probe instructions (historical)

The read-only inventory is complete. The lead selects
webllm/Qwen2.5-3B-Instruct-q4f16_1-MLC for one controlled trial through the existing Nightshift
app. Unload Llama 3.2 1B from memory first, preserving its downloaded files. Download/load
only the selected Qwen model through Nightshift; keep a single resident model. Do not modify
the app's structured-output capability flags or install a separate inference server.

Rationale: the [official Qwen model card](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/raw/main/README.md)
describes instruction-following and JSON-generation improvements. The
[upstream WebLLM catalog](https://github.com/mlc-ai/web-llm/blob/main/src/config.ts) lists
vram_required_MB=2504.76 for this exact quantization with a 4096 context override. This is
an upstream planning estimate, not a measurement of total Nightshift process memory or a
guarantee of capacity or answer quality on this Mac. The installed runtime remains 4K.

Capture current memory pressure and swap before loading, after ready, and after the probe.
Stop if there is sustained red memory pressure, allocation failure, a model crash or a
timeout; do not automatically load another model or retry. Leave Zetaris, its data and Docker
resource settings intact. Wait for the Qwen lane to report ready; do not trigger a separate
chat or smoke generation. If the GUI does not expose the required unload/download/load
controls, report that blocker rather than patching the application.

In the existing activated TradePulse environment, override only the selected model:

```sh
export METERLESS_MODEL=webllm/Qwen2.5-3B-Instruct-q4f16_1-MLC
export METERLESS_RESPONSE_FORMAT=prompt
export METERLESS_MAX_CONCURRENCY=1
export METERLESS_MAX_TOKENS=768
export ZETARIS_API_MODE=proxy
export ZETARIS_BASE_URL=http://localhost:3000
python3 -m integrations.meterless.structured_probe \
  --env-file ~/getting-started/.env.local \
  --env-file .env.nightshift.local \
  --case-output runs/live-sponsors-crypto-first/crypto/output.json \
  --symbol WLD-USD \
  --response-format prompt \
  --output runs/nightshift-qwen3b-prompt-probe-1
```

Existing process values take precedence over private env files. Do not print or replace token
contents. This keeps the same analyst task, evidence window, schema, prompt, output budget,
serial route, no retries and 180-second request timeout as the last plain-prompt test; the
selected model changes. Do not raise context length or rewrite the output to make it pass.

Stop after this one analyst request. Report the loaded model ID, actual resident memory,
resource snapshots, report.json and privacy-reviewed original reply.json if generated.
Even reply_checks_ok is not Crypto acceptance: examine numeric statements against the fresh
evidence and reject unsupported causal explanations. No automatic Crypto/US run is authorized
by this diagnostic. If the trial fails, preserve the result instead of cycling through models.

## Completed inventory request (historical)

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

## Lead-reported inventory and installed bridge restriction

GET /v1/models returned HTTP 200 without generation. The lead distinguished meterless routing
aliases from concrete webllm model IDs. Only Llama 3.2 1B q4f16 was downloaded and resident,
idle/ready at a UI-reported 922 MB and 4K context. Qwen2.5-3B-Instruct-q4f16_1-MLC is listed
but its files were missing. Other advertised downloads include Llama 3.2 3B, Qwen2.5 1.5B,
Qwen2.5 Coder 3B, Gemma 2 2B, Phi 3.5 Mini and SmolLM2 1.7B; none was loaded in that check.

Resource snapshot: macOS memory_pressure reported 16 GiB and 46% system-wide free percentage.
Swap usage was 9,977 MB of 11,264 MB. Container usage was engines 103.8 MiB, UI 279.6 MiB,
API 1.15 GiB, driver 2.489 GiB and Postgres 120.1 MiB. This is a snapshot, not a paging-rate
measurement or proof that the next model will fit.

The lead inspected structured-output.js and web-config.js under
/Applications/Nightshift M1-M4.app/Contents/Resources/web/. In that installed code, webllm
models have no structured-output capability override; the provider defaults json_object and
json_schema to unsupported and rejects such requests before inference. This is a concrete
installed-code restriction consistent with the two HTTP 400 reports. The raw historic rejection
bodies were not retained, so the exact branch taken by those historic requests is unproven.
Keep METERLESS_RESPONSE_FORMAT=prompt for this build. Do not patch capability metadata to
claim support that the app does not expose. No new model inference occurred during inventory.

## Lead-reported Qwen trial outcome

After updating to include 6c257bf, the lead unloaded Llama 1B from memory while retaining its
download and downloaded/loaded webllm/Qwen2.5-3B-Instruct-q4f16_1-MLC. Qwen was the sole
resident model, lane ready, with about 2.2 GB reported residency. Exactly one plain-prompt
probe was sent. It returned APITimeoutError after 180,153 ms, wrapped as AllProvidersFailed.
There was no reply.json or finish_reason, so JSON and grounding quality remain unmeasured.
The original failed report remains in runs/nightshift-qwen3b-prompt-probe-1/ on the Mac.

| Snapshot | Reported system free percentage | Swap used MB |
| --- | ---: | ---: |
| Before loading | 48% | 9,905 |
| Qwen ready | 42% | 11,052 |
| After request | 36% | 10,868 |

Memory pressure was briefly yellow during download and observed green after loading/during
the request, without sustained red pressure. These readings do not prove an out-of-memory
failure or establish that memory caused the timeout. No retry or Crypto run was reported.

## Lead-reported late completion and proxy findings

The lead located job_mvqgctxb02, session 4, turn 16, receipt rcpt_req_7tp6i4kq, marked unsigned
in the UI. The runtime receipt records success, 684 input tokens, 170 output tokens and
267,437 ms. The exported session timestamp is 2026-10-27T14:23:20.934Z. The separately
preserved runtime-response.md has file SHA-256
2afea4ffb8a7da07be986a7f3632ad8913e416811b65b06bd805217dbb3f089b;
it is an exported-file hash, not a hash of an HTTP response received by TradePulse.
Artifacts remain in runs/nightshift-qwen3b-late-runtime-1/ on the Mac. The original timed-out
probe and missing client reply are unchanged. No cancellation was needed: the lane was idle.

The lead inspected proxy.js, webllm-plane.js and webllm-worker.mjs in the installed app.
max_tokens is passed through to WebLLM; the receipt itself does not record its actual value.
The worker waits for queued model loading, then calls WebLLM with stream:false and waits for
the complete result. The proxy creates an abort signal on disconnect, but this inspected
worker path does not forward it or implement matching inference cancellation. Late completion
is consistent with that finding; whether this exact disconnect event reached the proxy was
not recorded. Do not patch the installed application as part of TradePulse's integration.

There are no retained per-stage first-token/compile/prefill/decode timings for this request.
Existing logs show WebGPU availability at startup but no associated GPU error or progress.
Thus the 267-second duration cannot be assigned to a particular internal phase. The unsigned
receipt's success status does not establish schema validity, grounding or case acceptance.

The lead reports the response described about 19.74% appreciation and attributed it to
investor optimism without causal evidence. That narrative is unverified and must not be
published as a research conclusion. The current resource snapshot reported 41% system free
and swap used 10,660 MB of 12,288 MB; the four Zetaris containers remained running.
