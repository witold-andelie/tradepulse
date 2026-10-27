# Sponsor integration and evidence

Updated 27 October 2026. The lead's current implementation uses hosted GLM for inference,
Zetaris for queries and actual Meterless Engines in the core. Existing Nightshift invocation
and late-completion evidence is preserved separately. Local-model diagnostics are stopped;
the dated AWS-only, NIM-only and all-Nightshift plans no longer block product acceptance.
See [current acceptance](../integrations/ACCEPTANCE.md) and
[hosted workflow](../integrations/HOSTED_ACCEPTANCE.md).

## Hosted inference: GLM

The lead supplies glm-5.3-flash at the OpenCode Go OpenAI-compatible endpoint. An explicit
LLM_PROVIDER=glm selects it for extraction, guard, analyst and skeptic without initializing
Nightshift or silently falling back to another provider. The current implementation records
provider=glm and the requested model, retains raw cassettes, and applies the same strict JSON,
schema and evidence verification. Timeout/concurrency/token budgets remain bounded.

The original all-Nightshift acceptance profile is preserved. The new explicit glm+zetaris+engines
profile requires real model responses plus actual engine snapshot, recall and remember in
the core trace; it does not pass a cloud response off as Nightshift. Live hosted acceptance
has now run on the Mac with the partial result below. The saved event rules permit arbitrary models/paid APIs while
requiring Zetaris and Meterless integration; a successful three-case engineering profile
is not an attestation of every event rule, media item or submitted entry.

First live hosted suite, reported by the lead: parity matched 12/12; Crypto passed with six
GLM calls, three explained names and successful engine snapshot/recall/remember. All 38
recommendations were computed NO_CALL stances. EU then failed at validate-case because the
SAF.PA skeptic reply failed strict JSON parsing and was marked unavailable. US did not run.
The original failed suite manifest remains submission_complete=false. US-only acceptance
and US API/UI review now take priority; no Crypto rerun or local-model experiment is required.
The new evidence-index tool revalidates and references existing accepted files by their
recorded hashes, without issuing model/query/engine calls or changing failed source reports.

The subsequent US-only run matched parity 12/12 and loaded 523 instruments, 279,982 price
rows and 401,487 pageview rows. It failed at validate-case with two abstained explanations
and one explained. Seven of 12 model request receipts ended length with empty/absent visible
content; the five returned stop-ended replies included three JSON failures and two schema
successes. This is not a passed US case. The original reports are retained.

Provider documentation confirms GLM-5.3-Flash forces thinking and defaults to max effort.
The earlier client did not set effort. The corrected client defaults GLM-5.3 requests to low,
supports explicit JSON-object mode and records visible-content length and reported reasoning
usage without retaining reasoning text. The second US attempt confirmed all 19 replies ended
stop with low effort, 8192 tokens and JSON-object mode. Twelve extractor and all six explanation
replies passed schema; one extractor reply did not. All three explanations were explained by
the existing verifier. This does not certify the entire narrative: the BE skeptic introduced
unsupported assertions, and prompts now require concise, evidence-limited conditional critique.

That run still failed at final engine remember before full output was saved. The old client
used ten seconds and did not retain the underlying exception; a later engine log reports 523
records added. A timeout is plausible but unproven, and the old manifest remains failed.
New client options bound sequential write batches separately from reads, retain safe request
receipts and save pending payloads. A read-only tool can reconcile stored record identities.
The acceptance wrapper also restores the core extractor's original bounded feedback retry
instead of intercepting invalid array elements. No generated text or contract is repaired.

The next US-only attempt explicitly rechecks prior parity against the frozen sample and
caches only bulk windows matching original live Zetaris receipts by parameters/count/hash.
Instrument evidence and verifier queries remain live. Cache hits, reused parity and source
file hashes are disclosed separately; this is not a fresh full-parity measurement. These
changes pass offline tests but remain pending live Mac acceptance. Preserve accepted Crypto.

## Zetaris

Load: the live data/evidence query layer. Typed allow-listed templates supply the core and
verifier. The live client/adapter now implement official direct REST and UI-proxy channels,
fresh request IDs, timeouts, bounded result expansion, contract dtype coercion and result
hashing. Configured live errors remain errors; there is no silent DuckDB fallback. The opt-in
receipt-verified bulk cache described above is explicitly labelled and never caches instrument
evidence or verifier queries.

The lead reports local Docker registration and SQL/API verification on the Mac:

| Registered table | Measured rows |
| --- | ---: |
| filing | 9,005 |
| filing_text | 321 |
| fundamental_fact | 250,968 |
| macro_point | 564 |
| pageview | 463,068 |
| price_bar | 342,804 |
| universe_member | 616 |

These match [the committed sample manifest](../data/sample/manifest.json). The official
helper also returned crypto 38, eu_equity 55 and us_equity 523 members. Its sanitized JSON is
preserved in [the real response fixture](../integrations/tests/fixtures/zetaris_query_response.json).

Actual registration route: NDP File System, individual root upload, move to /file-store,
then Data Explorer / File Source & API / TRADEPULSE_LAKE / Create Table / File store /
Parquet / NDP File System. Direct /file-store uploads and a batch failed on this deployment.
The source Parquet files were preserved. Separate microsecond-compatible copies resolved
Spark's nanosecond error. The durable [conversion helper](../integrations/zetaris/prepare_parquet.py)
checks safe casts, exact logical equality and read-back.

The lead now reports real 12/12 parity on the Mac, including complete large results, and
actual Crypto core/evidence queries through Zetaris. The combined case remains failed
because of model replies. No AWS/S3 deployment,
public endpoint or outside-universe EDGAR feature is claimed.

Follow-up reported at 6a2f71d: the actual project client/adapter smoke passed. Parity matched
6/12 templates. Three large responses contained only 1,000 rows; three equal-count hash
mismatches were exactly reproduced locally by removing UTC timezone information from the
DuckDB result. Both adapters now enforce identical contract types before hashing. Verified
ordinal paging protects the live adapter against capped responses and ambiguous API totals.
All 12 frozen-snapshot templates matched through a simulated capped/string-valued API.
The lead reports the updated real Mac run passed 12/12 at 6966b0c, preserved in
runs/zetaris-parity-fixed-1.json on the Mac. See
[diagnosis and scope](../integrations/zetaris/PARITY_DIAGNOSIS.md).

Official contracts:
[direct REST helper](https://github.com/zetaris/getting-started/blob/main/scripts/zetaris_sql.py),
[UI-proxy helper](https://github.com/zetaris/getting-started/blob/main/scripts/query_zetaris.py).

## Meterless Engines

Load: World Model stores grounded events and validated relations; H-MEM persists research
recommendations and provenance. The existing core bridge reads dated memory counts as
unverified prompt context and writes every recommendation. A configured engine failure fails
the integration. The computed Track Record is not relabelled as H-MEM settled performance.

Implemented: the TypeScript sidecar wraps unchanged official references at upstream commit
1742dec56a66e58eef9dda2d2b865823758ca8cd. Docker, loopback-only Compose, original-schema
validation, bounded requests, dated reads, persistence, token auth and audit logs are provided.
See [the HTTP API](../integrations/engines/API.md).

Measured locally, with scope in [VALIDATION.md](../integrations/engines/VALIDATION.md):

- 23 vendored files matched the official commit's Git hashes.
- Official conformance passed: H-MEM 13/13 and World Model 8/8.
- Eight service tests and TypeScript checks passed. Registry audit found zero vulnerabilities.
- Three frozen-snapshot core runs used the actual container over HTTP. The first test took
  40.69 seconds and wrote 616 records. Restart preserved these and 619 H-MEM ledger entries.
  Models abstained because this test used an intentionally empty replay cassette.

Mac follow-up reported by the lead: actual engine health passed. Crypto run
2026-10-23-ba9fb487 recorded successful snapshot, three recall calls and remember.
All 24 seed edges were rejected, so this still does not establish non-empty real World Model
ingestion. H-MEM service operations succeeded even though model/case acceptance failed.

The real-data test's World Model snapshot was empty. Synthetic service tests exercise
non-empty event/graph behavior, not real model-extracted event success. The core uses dated
counts, not semantic relevance or remembered accuracy. Feedback uses the official ledger;
automatic pending selection and historical conflict consumption remain outside the active
core path. JSON reference persistence is single-process storage, not a multi-writer database.

## Nightshift: retained integration evidence, optional inference

Historical load: the AI provider for extraction, analyst and skeptic requests. In auto mode a configured Nightshift
token makes Meterless the first route for every role. The live acceptance runner restricts
routes to Nightshift for that original profile; cloud fallback or replay cannot satisfy those checks. Calls use the real
token file, meterless-app/meterless-scope headers and a 180-second request timeout.

Implemented: URL normalization, all-role routing, thread-safe record/replay, sanitized smoke
checks, wrong-token/live network tests and a three-case acceptance runner. Responses retain
provider/model metadata and hashes. The core already traces model calls and verification.

New lead-reported evidence: Nightshift M1-M4 Edition 2026.10.25 (download page version 0.92.7)
is installed on the M1 Mac. An actual Bearer-token API call at http://127.0.0.1:8088/v1
returned HTTP 200 and "Hello." from webllm/Llama-3.2-1B-Instruct-q4f16_1-MLC. TradePulse's
smoke check also returned status=ok and provider=meterless using that model ID. Configuration
is in the ignored .env.nightshift.local and refers to an existing token file; no token was
included in the report. Zetaris still returned 616 universe members. Memory pressure was
green, with about 7.74 GB of existing swap usage. These observations were reported from the
Mac and have not been independently repeated on the Windows development machine.

This establishes a real text-provider connection. The later Crypto run returned 11 replies:
three passed schema validation and eight did not. Of eight analyst replies, only one passed
the schema, and all four of its claims failed evidence verification. A further analyst
attempt failed with AllProvidersFailed. All three explanations abstained; validate-case
failed, so no successful live case is claimed. Grounded filing extraction and combined
sponsor-connected cases remain incomplete. The client checks
the configured model against the actual runtime catalog, including concrete webllm IDs.
Nightshift calls default to one concurrent request and a 768-token output cap, with the
requested response schema included in the prompt. Live acceptance separately validates the
JSON schema; a plain "Hello." cannot pass as an analyst or skeptic result.

The supplied raw replies demonstrate incomplete JSON, omitted required claim kinds, invented
evidence references and unsupported causal statements. Raising the token limit alone is
not an established fix. A bounded, opt-in structured-output request and a one-request
[diagnostic](../integrations/meterless/STRUCTURED_DIAGNOSIS.md) are implemented; actual
Nightshift schema forwarding and factual reply quality remain unverified. New receipts
record stop reasons and sanitized error types/statuses, without raw credentials.

The lead's first webllm_schema probe at 143386e queried 61 live price rows and then received
HTTP 400 / BadRequestError in 328 ms, without a model reply. It remains failed with
feature_acceptance=false. The specific rejected field was unknown. The next diagnostic was
one explicit json_object control, with only the nested schema removed; it was not an automatic
fallback or Crypto acceptance. Fixed-vocabulary error hints avoid publishing raw error bodies.

Subsequent lead-reported probes: json_object also returned HTTP 400, naming response_format
in the error hints. Plain prompt mode produced invalid JSON after 60,677 ms, stopping normally
after 37 output tokens. Its claims value was a string, with required fields missing and an
extra closing brace. No reference verification ran. These are failed diagnostics, not model
acceptance. The next step is a read-only inventory of actual Nightshift models and current Mac
resources before selecting another configuration; do not keep repeating the same request.

The lead subsequently completed that inventory: Llama 1B was the only resident model, while
Qwen2.5 3B q4f16 appeared as an available download. Inspection of the installed Nightshift
code found structured formats disabled for webllm providers before inference. The next trial
selects Qwen2.5-3B-Instruct-q4f16_1-MLC in prompt mode, replacing rather than adding to the
resident model, followed by one unchanged analyst probe. This selection is not a successful
download, memory measurement or model acceptance by itself.

The lead then reports Qwen loaded as the sole resident model at about 2.2 GB. Its one
plain-prompt probe timed out after 180,153 ms without a reply. Observed memory pressure was
green during the request; this neither establishes nor rules out a runtime problem. The
next step is inspection of the existing request/job, WebGPU and proxy evidence, including
whether it continued after the HTTP client timed out. No successful Qwen/analyst case is claimed.

That existing job was subsequently found completed in Nightshift after 267,437 ms, with
684 input and 170 output tokens. Its receipt is marked unsigned. The lead preserved the
original export separately and confirmed the lane idle; the timed-out client report remains
failed. Inspection found max_tokens forwarding and a non-streaming WebLLM call, with no
worker cancellation propagation in the inspected path. No internal per-stage timings were
retained. Runtime completion does not establish an accepted explanation: the lead reports
an unsupported investor-optimism attribution. Raw-reply grounding review is pending.
Bounded request/queue timeout overrides now support measured slow local inference without
changing the default 180-second values, retries, schemas or verification requirements.

The diagnostic history above is retained, but no further Nightshift experiment is a current
product-acceptance prerequisite. Complete offline model replay and independent skeptic-family
routing remain unverified. NIM remains an optional route in auto mode. The original Nightshift
profile allows only Nightshift; the hosted GLM profile allows only GLM. Provider labels are honest.

Contract: [official hotspot guide](https://github.com/Meterless/Meterless/blob/main/docs/products/nightshift/hotspot.md).

## Traces and three sample cases

The existing [three computed examples](../examples/README.md) contain inputs, outputs and
original traces. They process real public data offline with unavailable-model abstention.

Run the integrations.live_acceptance module on the configured Mac to produce a new delivery
under ignored runs/. It checks sample identities and Zetaris parity, uses the selected live AI provider and the
engines, and packages inputs, outputs, original traces, query/model receipts, a cassette,
manifest and a computed README table. Service/model failure cannot produce status=ok.
Review artifacts before publication. Keep the existing examples until the live command has
completed and a reviewed replacement is ready.
