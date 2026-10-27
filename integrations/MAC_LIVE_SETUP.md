# Finish live sponsor acceptance on the Mac

The lead reports all seven sample tables registered, real 12/12 Zetaris parity after
6966b0c, and working Mac engine health/snapshot/recall/remember operations. The first Crypto
case failed on model replies and remains unaccepted. Start with
[the one-request Nightshift diagnostic](meterless/STRUCTURED_DIAGNOSIS.md); do not repeat
the entire pipeline or US extraction while diagnosing that failure.

Run these commands in macOS Terminal from the TradePulse checkout. This workflow uses the local
Docker deployment; the historical AWS-only Member D plan is not a completed deployment claim.
Never paste API keys, passwords or the Nightshift token into chat, screenshots or committed files.

## 1. Install this checkout's dependencies

Use the sponsor-integration branch supplied by the lead until it is merged to main. Preserve
any local changes before switching branches.

```sh
cd ~/tradepulse
git fetch origin
git switch lead/sponsor-integration-wip-20261027
git pull --ff-only
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[agent,dev]'
```

Python 3.11 or later, Docker Desktop and Node 22.12 or later are required. The engine container
is multi-architecture through the official Node image; the lead now reports a successful
engine start and health check on the actual Mac.

## 2. Reuse the working Zetaris configuration

TradePulse reads integration variables from the process environment. The preflight and live
acceptance commands also accept an explicit `--env-file`; they do not execute shell text.
The existing ignored `~/getting-started/.env.local` can supply the already-configured key and
organization ID. There is no need to copy or display its contents.

```sh
export ZETARIS_API_MODE=proxy
export ZETARIS_BASE_URL=http://localhost:3000
python3 -m integrations.preflight --service zetaris --env-file ~/getting-started/.env.local
```

Expected: SELECT 1 succeeds, followed by one measured universe template receipt per pool.
Do not set ZETARIS_ENGINE_ID unless the official helper requires it; the successful helper
request can use the deployment's default engine. Direct REST is also supported separately
with ZETARIS_API_MODE=direct and ZETARIS_REST_URL, not by silently switching endpoints.

To run parity with the same private environment file:

```sh
python3 -m integrations.zetaris.parity --env-file ~/getting-started/.env.local --report runs/zetaris-parity-fixed.json
```

Every template must return the same logical row hash as DuckDB over the unchanged sample.
On a mismatch, keep the output and fix the integration. Do not weaken the parity assertion.
Choose a new report filename if one already exists. The report contains runtime versions,
configured limits, template counts/hashes, request-size metadata and verified page ordinals;
it never contains credentials or raw query data. Each completed template is printed immediately.
Large results now use verified ordinal paging and can take longer than the earlier truncated
response. See [the diagnosed failure patterns](zetaris/PARITY_DIAGNOSIS.md).

## 3. Start the actual Meterless engines

```sh
docker compose -f integrations/engines/compose.yaml up -d --build --wait
export ENGINES_URL=http://127.0.0.1:8790
python3 -m integrations.preflight --service engines
```

The port is bound only to the Mac's loopback address. The named volume stores official engine
state and audit history across restarts. It is separate from the Zetaris Docker deployment.
No public AWS port or new cloud resources are required by these commands.

## 4. Open Nightshift and enable its API/hotspot

Nightshift must be installed and running on hardware supported by the chosen edition. The
browser-only edition does not provide the local AI hotspot. Follow the official
[hotspot guide](https://github.com/Meterless/Meterless/blob/main/docs/products/nightshift/hotspot.md)
for the actual app edition. A Zetaris Docker installation is not a Nightshift installation.

Nightshift writes a private `proxy-token` file under its state directory. Set the path to the
file using the app's actual location; do not guess a state-directory path and do not print the
token. The example below prompts only for that file path:

```sh
read -r 'METERLESS_TOKEN_FILE?Path to Nightshift proxy-token file: '
export METERLESS_TOKEN_FILE
export METERLESS_BASE_URL=http://127.0.0.1:8088/v1
export METERLESS_MODEL=meterless/auto
export METERLESS_APP=tradepulse
python3 -m integrations.preflight --service nightshift
```

Use the actual endpoint and model ID shown in the installed app. The lead's M1 edition has
successfully used webllm/Llama-3.2-1B-Instruct-q4f16_1-MLC; it must not be rejected simply
because the ID lacks a meterless/ prefix. The selected ID must appear in the runtime's
actual model catalog. The request must return a text response. The smoke output
includes provider, model, response length and SHA-256, never the bearer token. A response from
NIM cannot satisfy this smoke check. When available, run the wrong-token network acceptance:

```sh
python3 -m pytest integrations/tests/test_live_meterless.py -q -m network
```

The lead has already reported a successful smoke call using the ignored .env.nightshift.local.
To reuse that file, without printing its contents:

```sh
python3 -m integrations.preflight --service nightshift --env-file .env.nightshift.local
```

The default runtime queue is serial across roles. METERLESS_MAX_CONCURRENCY can be 1-4;
keep it at 1 on this M1. METERLESS_MAX_TOKENS defaults to 768 (allowed range 1-4096).
The SDK request and local queue-wait timeouts each default to 180 seconds. For measured slow
local inference, METERLESS_TIMEOUT_SECONDS accepts 1-600 and METERLESS_QUEUE_TIMEOUT_SECONDS
accepts 1-1800, both integer seconds. They are independent: a serial multi-name call can
wait behind another complete inference. SDK automatic retries remain disabled. These are
HTTP-operation/queue bounds, not a whole-pipeline deadline or remote cancellation guarantee.
The lead's Qwen request completed in Nightshift after about 267 seconds, beyond the default
client timeout. Its original late reply still needs offline grounding review; do not rerun
it merely because a longer wait is now configurable. These limits do not certify that a
small model follows research instructions; live acceptance checks its actual JSON reply.
METERLESS_RESPONSE_FORMAT defaults to prompt. The optional webllm_schema mode sends WebLLM's
schema-string response_format, without automatic fallback. The installed Nightshift bridge
must be tested before relying on it. See the diagnostic above.

## 5. Start with a Crypto-only live case

First check Zetaris parity and start the engine service above. Then:

```sh
export ZETARIS_API_MODE=proxy
export ZETARIS_BASE_URL=http://localhost:3000
export ENGINES_URL=http://127.0.0.1:8790
export METERLESS_MAX_CONCURRENCY=1
export METERLESS_MAX_TOKENS=768
python3 -m integrations.live_acceptance \
  --env-file ~/getting-started/.env.local \
  --env-file .env.nightshift.local \
  --pools crypto \
  --output runs/live-sponsors-crypto-first
```

Crypto does not trigger the US filing extractor. A successful selected run reports
status=selected_cases_ok and submission_complete=false. It is useful live-feature evidence,
not completion of all three cases. Watch current memory pressure and swap growth during
the test; an old swap-usage total alone is not a measurement of current paging activity.
Do not run the full filing workload while diagnosing a slow or invalid small-model reply.

## 6. Generate all three live examples and traces

Once all three service checks pass:

```sh
python3 -m integrations.live_acceptance \
  --env-file ~/getting-started/.env.local \
  --env-file .env.nightshift.local \
  --output runs/live-sponsors-first
```

Choose a new output directory for each attempt. The command checks the frozen sample hashes,
all-template Zetaris parity and engine health before running crypto, EU and US requests.
It uses Nightshift only, with no cloud fallback or prerecorded answer. US extraction can be
long-running: the normal pipeline allows up to 200 filing documents, plus bounded extraction
and verification retries. The model SDK timeout defaults to 180 seconds and has the bounded
local override above. There is no
promise that the entire run finishes within one request timeout.

Each pool directory contains input.json, output.json, the original trace and a console log.
The root contains parity.json, queries.jsonl, models.jsonl, the live cassette, manifest.json
and a computed README table. Full status=ok with submission_complete=true requires all three
pools, schema-valid live analyst and skeptic answers and actual engine snapshot, recall
and write operations. Missing models or services fail acceptance. Failure artifacts retain
the original trace and contract-valid output where available, without claiming success.
An evidence-checked abstention can still be an honest output; no tier or claimed result is
changed to make the demo look better.

The original `examples/` remain the previously computed offline examples until a reviewed
live delivery replaces them. `runs/` is ignored. Review model text and run evidence for
privacy before publishing. Offline replay is a separate follow-up: refresh the cassette for
the exact sample-mode prompts and prove a network-blocked replay before claiming it works.
