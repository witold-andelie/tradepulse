# Fast product acceptance: hosted GLM, live Zetaris and Meterless Engines

Current lead decision, 27 October 2026: stop local-model diagnostics and use the supplied
GLM API for normal inference. Existing Nightshift attempts, late completion, original traces
and failed client reports are retained as separate integration evidence. They are not
rewritten into successful product cases. The pending request for more Nightshift reply text
is no longer a prerequisite for this workflow.

## Current priority: US equities first, preserve Crypto

The lead reports the first hosted suite passed parity 12/12 and Crypto: six live GLM calls,
three explained names, real engine snapshot/recall/remember, and 38 computed NO_CALL records.
EU then failed because SAF.PA's skeptic reply did not pass strict JSON parsing; US never ran.
The source directory is runs/hosted-glm-acceptance-1/. Preserve it unchanged. Do not repeat
Crypto. Its NO_CALL stances are computed research outcomes, not a reason to alter gates.

The lead now prioritizes US. Start its existing supported single-pool command immediately;
do not wait for EU reply diagnosis, assembly tooling or another model probe:

```sh
export ZETARIS_API_MODE=proxy
export ZETARIS_BASE_URL=http://localhost:3000
export ENGINES_URL=http://127.0.0.1:8790
python3 -m integrations.live_acceptance \
  --llm-provider glm \
  --env-file ~/getting-started/.env.local \
  --env-file .env.glm.local \
  --pools us_equity \
  --output runs/hosted-glm-us-first-1
```

This retains US filing extraction and its existing bounds. A successful US-only run is
selected_cases_ok with submission_complete=false; that means the selected case passed,
not that US failed. Once it passes, prioritize its API/UI review. The already accepted Crypto
result can also be reviewed now; neither browser workflow needs to wait for EU acceptance.
The API launcher below does not start model generation merely by serving existing results.

To index the accepted Crypto and US evidence without model calls or source rewrites:

```sh
python3 -m integrations.assemble_acceptance \
  --source runs/hosted-glm-acceptance-1 \
  --source runs/hosted-glm-us-first-1 \
  --llm-provider glm \
  --output runs/hosted-glm-accepted-index-1
```

The assembler verifies recorded file hashes, case identity, actual-provider trace requirements
and engine operations using the same case validator. A failed overall source can contribute
only its previously accepted case entries. The EU failed case is not silently reclassified.
The index references original directories and retains their manifest hashes and statuses;
it is not a standalone copy of the evidence. Preserve source model/query receipts, cassettes,
parity files and original traces. Two pools remain partial acceptance. After a later accepted
EU-only run, create a fresh three-source index; only three distinct accepted pools mark complete.

EU raw-reply diagnosis is deferred behind US. Do not guess that it is a Markdown fence or
repair its text before inspecting the existing raw response. Never fill missing schema fields,
discard extra objects, weaken evidence checks or rerun accepted Crypto to work around it.

## Rule basis and scope

The locally saved Official Rules section 8 permits any model, including paid APIs, while
requiring Zetaris and Meterless integration. The Technical Execution Guide says sponsor
technology must have a real role and discourages hours-long runs. Those stored documents
do not require every inference role to use Nightshift. Their older Cursor text is superseded
by the organizer change reported by the lead. Current event-page rules remain authoritative;
the public page did not expose the complete current rules during this check. This guide is
an engineering acceptance profile, not a guarantee of organizer eligibility decisions.

The earlier all-Nightshift acceptance gate was an internal profile, not a rule found in
those stored documents. It remains available unchanged by default. The explicit GLM profile
instead requires live GLM analyst/skeptic replies, actual Zetaris queries and actual engine
snapshot/recall/remember operations. Contracts, data hashes, point-in-time checks, schemas
and honest abstention are preserved. GLM answers are labelled glm, never meterless.

Meterless is already functional in the core through the official H-MEM/World Model sidecar:
the lead observed real snapshot, recall and persistence calls. Snapshots were empty, so
non-empty real World Model ingestion remains unclaimed. Nightshift successfully generated
responses in the app; some client requests failed or timed out and their quality was not
accepted. These facts can be disclosed without blocking hosted inference.

## Private configuration on the Mac

Reuse the existing virtual environment, Zetaris deployment and engine service. Do not make
new sponsor credentials or edit the installed Nightshift app. Local models can remain idle;
they are never called by the GLM profile, even if METERLESS_TOKEN_FILE remains configured.

The human configures ignored .env.glm.local with:

```dotenv
LLM_PROVIDER=glm
GLM_BASE_URL=https://opencode.ai/inference/go/openai/v1
GLM_MODEL=glm-5.3-flash
GLM_API_KEY=YOUR_EXISTING_PRIVATE_KEY
GLM_MAX_CONCURRENCY=1
GLM_MAX_TOKENS=4096
GLM_TIMEOUT_SECONDS=180
```

Use the actual key locally, never in chat, screenshots or committed files. Alternatively,
GLM_API_KEY_FILE can reference an existing plain-text key file; it is not an OpenCode auth.json
parser. If OpenCode Go is already connected, omit GLM_API_KEY and GLM_API_KEY_FILE and set
GLM_OPENCODE_AUTH_FILE=~/.local/share/opencode/auth.json instead. The adapter reads only the
existing opencode-go API entry in memory, without printing or copying the key. A missing Go
entry fails explicitly; it never selects an unrelated provider credential.
Existing process values take precedence over env files. Do not overwrite existing
private configuration without preserving it. API keys need not be printed to verify setup.

The endpoint/model are confirmed in the
[OpenCode Go endpoint table](https://opencode.ai/v2/docs/console/go/#endpoints).
The pasted /chat/completions URL is also accepted and normalized to its provider base path.
The existing Python OpenAI-compatible SDK is reused; no JS SDK or new dependency is needed.
Requests identify the application honestly as tradepulse/1.0 and include one stable session
header per client. OpenCode Go documents coding-agent-oriented usage; use the account within
its applicable service terms, without disguising research traffic or enabling extra paid usage.
If that subscription rejects the workload, the same adapter accepts another authorized
OpenAI-compatible GLM base URL/key. Do not spoof OpenCode client identity to bypass restrictions.

## Initial three-pool command (historical first attempt; do not repeat Crypto)

From the updated checkout and activated environment:

```sh
export ZETARIS_API_MODE=proxy
export ZETARIS_BASE_URL=http://localhost:3000
export ENGINES_URL=http://127.0.0.1:8790
python3 -m integrations.live_acceptance \
  --llm-provider glm \
  --env-file ~/getting-started/.env.local \
  --env-file .env.glm.local \
  --pools crypto eu_equity us_equity \
  --output runs/hosted-glm-acceptance-1
```

No separate Nightshift smoke/probe is needed. The runner verifies the frozen sample and parity
once, then processes Crypto, EU and US in order. It stops on a failed case and preserves its
real output/trace. Successful cases are also saved into the existing RunStore for API viewing.
US filing extraction retains the original 200-document bound and verification; it is not
silently skipped. The command does not claim it will finish within one API-request timeout.

The final manifest must identify acceptance_profile=glm+zetaris+engines and llm_provider=glm.
Three accepted pool cases produce status=ok and submission_complete=true for this engineering
profile. This field does not attest to every event rule or completed submission media.
The computed README, query/model receipts, original cassette and traces disclose their actual
providers. nightshift_calls is zero for these GLM cases. Do not copy Nightshift records into
them to imply a shared successful request. A refusal/abstention remains valid when evidence
does not support an explanation; schema-invalid or unavailable calls do not pass the profile.

## API and UI check for any accepted case

Start the existing API using the same private settings:

```sh
python3 -m integrations.launch \
  --env-file ~/getting-started/.env.local \
  --env-file .env.glm.local \
  --serve
```

The launcher sets live mode and enables the engine sidecar, then delegates to the unchanged
run.py API entry point. Start the existing web app in another terminal, with its API base
pointing to the local backend as documented in web/. Review Leaderboard, Ticker Detail,
Factor Lab and Run Trace against the actual stored run. Check verified/rejected claim badges,
no-call/abstention labels, source hashes, provider/model disclosure and browser console errors.
Do not use synthetic fixtures as proof of GLM-backed results. Keep API keys off browser UI.

The full three-case suite need not complete before reviewing an accepted stored case. If all
checks pass, review the three case artifacts for privacy and link those exact artifacts
in the final README/demo. Do not claim complete offline model replay until separately measured.
Deck/video and final submission remain separate tasks; do not wait for another local-model trial.
