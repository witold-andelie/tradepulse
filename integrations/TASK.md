# Member D — Sponsor integrations (`integrations/`)

## Current submission direction: 27 October 2026

The lead's latest requirements supersede the dated AWS-only and NIM-only plan below:

1. A working end-to-end project with Zetaris queries and actual Meterless Engines in a
   working feature. Normal inference now uses the lead's hosted GLM API.
2. Actual agent traces and three computed sample inputs/outputs ready for the README.
3. Private credentials, point-in-time filtering, unchanged contracts and honest abstention.

The lead explicitly stops local-model diagnostics and chooses glm-5.3-flash through the
supplied OpenCode Go endpoint. Follow [HOSTED_ACCEPTANCE.md](HOSTED_ACCEPTANCE.md) now:
the pending-pool acceptance command in the lead's current priority order, then API/UI review.
Preserve already accepted cases. Do not add a new smoke/probe loop.
The original Nightshift-only profile remains available separately; it is not a prerequisite
for the hosted profile and GLM responses must never be labelled Nightshift responses.

Implemented: GLM all-role routing, provider-specific audit/acceptance, the live Zetaris
adapter, official engines sidecar and private-env API launcher. The lead reports real 12/12
Zetaris parity and actual Mac engine operations. Nightshift already generated real replies,
including a Qwen completion after the HTTP client timed out; its original evidence is retained.
Those failed product cases are not relabelled successful. Hosted GLM acceptance is now partial,
with the current pool progress recorded below.

Latest hosted result: Crypto now passed (six GLM calls, three explained names, 38 NO_CALL
records) after 12/12 parity. EU stopped on one skeptic JSON failure. US subsequently ran
but failed with empty length-ended responses and invalid JSON. The GLM-5.3 configuration
now requests low reasoning effort; the next US-only attempt uses the explicit JSON/output
settings in HOSTED_ACCEPTANCE.md. Keep the accepted Crypto case and begin
API/UI checks from accepted stored output without waiting for all pools. Follow the current
priority section of HOSTED_ACCEPTANCE.md; do not repeat its historical full-suite command.

Follow [MAC_LIVE_SETUP.md](MAC_LIVE_SETUP.md), [current acceptance](ACCEPTANCE.md),
[engine measurements](engines/VALIDATION.md) and [sponsor evidence](../docs/sponsors.md).
No AWS deployment, NIM model selection or outside-universe EDGAR source is on the minimum
submission critical path. Those remain unverified extensions. The saved event rules permit
arbitrary models/paid APIs and require meaningful Zetaris/Meterless integration; the earlier
all-Nightshift requirement was an internal profile superseded by the lead's latest decision.

## Historical assignment below

The dated assignment below preserves planning context. Follow the current direction above
where they conflict. Local Zetaris is the actual deployment being accepted.

> **DEADLINE: finish everything by Sunday 25 October 2026, 11:59 pm US Eastern (EDT)**
> = Monday 26 October 03:59 UTC. Target: done on Saturday 24 October. The hackathon closes
> 27 October 23:45 UTC; the remaining time is for the lead's QA, demo video and submission.
>
> **Status (2026-10-24):** the pure-code parts are merged and tested:
> - SQL templates
> - the DuckDB adapter and `rows_sha256`
> - `ensure_single_statement` and `coerce_frame`
> - the registration CLI
> - `llm.py`, including the hosted NIM routes
> - `EnginesClient`
>
> **Decision D18: every LLM role runs on hosted NVIDIA NIM.** No model runs on anyone's laptop.
> Meterless carries its load through the **World Model and H-MEM engines (D5)**.
>
> Your work, in priority order:
> 1. **D0, D1, D3**: Zetaris on AWS, registration, `ZetarisClient` and `ZetarisAdapter`, parity,
>    `ACCESS.md`. This is the disqualification risk, so it comes first.
> 2. **D4**: pick the NIM models, run the live smoke test, and **record the LLM cassette** once A's
>    `data/sample/` is merged.
> 3. **D5**: the Meterless engines sidecar, running locally (docker-compose) and on AWS.
> 4. **D6**: the `docs/sponsors.md` draft, with evidence.

The frontend and core already exist. D's service and cassette work is still on the critical
path; `ZetarisClient` and `ZetarisAdapter` remain stubs and no engines server is present.
`docs/sponsors.md` now tracks the honest implementation/evidence status; attach actual live
evidence there rather than replacing the draft with unverified completion claims.
See `docs/STATUS.md` for current artifacts, owners and acceptance results.

You own everything that connects TradePulse to **Zetaris** and **Meterless**:

- the Zetaris deployment, table registration and the query layer
- the hosted LLM chain on NVIDIA NIM (Meterless Runtime is an optional, off-by-default route)
- the Meterless engines (World Model and H-MEM) running as a sidecar

Sponsor integration is a scoring criterion, and a disqualifier when it is missing or decorative. Each
integration must carry real load and leave evidence: logs, conformance output and screenshots.

- Architecture view: the purple sponsor objects in `docs/architecture/opm/svg/SD1_recommending.svg`,
  `SD1.3_extracting_linking.svg`, `SD1.7_explaining.svg` and `SD2_acquiring.svg` (Registering in
  Zetaris).
- Sponsor facts already collected: `docs/architecture/data-sources.md` (Sponsor routing) and
  `docs/architecture/decisions.md` (D7–D9 and open items).
- Sponsor repositories, cloned locally: `D:\AI_Models\hackson\refs\zetaris\repo` and
  `D:\AI_Models\hackson\refs\meterless\repo`. Online:
  https://zetaris.github.io/getting-started/ and https://github.com/Meterless/Meterless.

## What you own

```
integrations/
  zetaris/
    templates/*.sql     allow-listed query templates (the core's only way to query data)
    templates.py        D2  parameter validation and rendering
    adapter.py          D2/D3  QueryAdapter: DuckDBAdapter (sample) + ZetarisAdapter (live), rows_sha256
    client.py           D3  REST client, response parsing, type coercion
    register.py         D1  runs registration SQL, one statement per call
    sql/                D1  registration SQL files (README inside)
    DEPLOY.md           D0  how the instance runs (no secrets)
  meterless/
    llm.py              D4  hosted NIM routes per role, record/replay cassette
    engines_client.py   D5  Python client for the sidecar
  engines/              D5  Node/TypeScript sidecar hosting the official reference engines (API.md)
  tests/                acceptance tests (given; do not weaken them)
docs/sponsors.md        D6  sponsor-technology write-up (draft; the lead finalises it)
```

Do not edit `contracts/`, `tradepulse/`, `ingest/`, `quant/` or `web/`. To change a template's
output columns or the sidecar API, open a PR for the team lead, because the core depends on them.

## Setup

```
py -3 -m pip install -e ".[agent,dev]"
py -3 -m pytest integrations -q        # existing offline tests; live acceptance is separate
copy .env.example .env                 # fill Zetaris / Meterless / NIM values locally, never commit
```

## Global rules

1. **Secrets** (API keys, the Meterless proxy token, AWS credentials) never enter the repository,
   logs, traces, screenshots or error messages. They are read from the environment or from token
   files only. If a secret leaks, rotate it first, then tell the lead.
2. **One SQL statement per Zetaris call.** Every call has a timeout and a fresh `X-Request-ID`.
3. **The LLM never writes SQL.** The only way to query data is a template in
   `zetaris/templates/` with typed parameters.
4. **SAMPLE_MODE never touches the network:** DuckDB over `data/sample`, LLM answers from the
   cassette. A cassette miss is an error.
5. **Same template, same answer.** DuckDB and Zetaris must return the same rows for the same
   template and parameters (`rows_sha256` equal). The verifier depends on this.
6. **Use the official Meterless reference engines unchanged** (vendored with LICENSE and NOTICE).
   Our adaptation code lives in our own files.
7. **Bounded everything:** timeouts on every call (Zetaris 120 s, LLM 180 s, sidecar 30 s), limited
   retries, no infinite loops.
8. **English only.**

## Tasks

### D0 · Shared AWS deployment (required)

You are in the US and the rest of the team is in Europe, so nobody can use your computer. Every
shared service therefore runs on **AWS** and is reached by the team over the internet. A local-only
setup does not count.

- **Region:** use an EU region, `eu-central-1` (Frankfurt) or `eu-west-1` (Ireland), because four of
  five members are in Europe. If the Zetaris AWS install does not support EU regions, use
  `us-east-1` and say so in `DEPLOY.md`.
  - **Recorded fallback, 25 October:** D reports that the EU regions and N. Virginia were
    unavailable and is proceeding with **US East (Ohio), `us-east-2`**. The lead accepts Ohio
    as the deployment-region fallback. Record the actual region and observed restriction in
    `DEPLOY.md`; the cause of the failed attempts has not been independently verified.
    Compatibility, cost checks and successful HTTPS smoke tests from Europe still apply.
    This records a region choice, not a completed deployment.
- **Zetaris:** install it on AWS following the Zetaris AWS guide. Verify current account credits
  and deployment pricing before provisioning; earlier planning estimates are not a quote.
  - Stop the instance when nobody is working.
  - Set a budget alert.
- **Lake storage:** create a **private S3 bucket** for the parquet lake and register the tables with
  `s3a://` paths; this is the route the Zetaris recipes have proven.
  - Give Member A an IAM user that can only write to `s3://<bucket>/lake/`.
  - Give the core a read-only IAM role or user.
- **Team endpoints:** expose the Zetaris REST API and the engines sidecar (D5) over **HTTPS only**:
  - Put a reverse proxy in front with automatic TLS, e.g. Caddy on the instance, or an ALB with an
    ACM certificate.
  - Restrict access to the team's IP addresses, and also require a token: the Zetaris API key for
    Zetaris, `ENGINES_TOKEN` for the sidecar.
  - Never expose a plain-HTTP port or the Zetaris GUI publicly. Reach the GUI only through an SSH
    tunnel or AWS SSM port forwarding.
- Run the Zetaris preflight and verify scripts and paste their output.
- Create API tokens in the GUI yourself; never ask an AI agent to create one.

**Deliverable: `integrations/ACCESS.md`**, the interface the rest of the team plugs into. It contains
no secrets. It lists:

- the HTTPS base URLs: `ZETARIS_REST_URL`, `ENGINES_URL`
- how each teammate receives their token and org id through a private channel
- how to add a new IP to the allow-list
- a 3-line smoke test each teammate can run from Europe:
  - `GET /health` on the sidecar
  - `SELECT 1` through `ZetarisClient`
  - one template through `ZetarisAdapter`

This closes the open item "How Zetaris reads lake files" in `decisions.md`.

### D1 · Registration (`zetaris/sql/`, `register.py`)

- Write the SQL described in `zetaris/sql/README.md`.
- Implement `split_statements`, `substitute` and `run_files`. Add a CLI:
  `py -3 -m integrations.zetaris.register integrations/zetaris/sql/*.sql`, reading `${LAKE_PATH}`
  and `${ZETARIS_USER_AGENT}` from the environment.
- Running it twice must be harmless: "already exists" counts as success.
- Evidence: the CLI output and a screenshot of the tables in the Zetaris GUI (with the token
  hidden).

### D2 · Templates and DuckDB adapter (`templates.py`, `adapter.py`)

- Implement `list_templates`, `declared_params`, `render`, `rows_sha256` and `DuckDBAdapter`.
- Keep template SQL in the subset both Spark SQL and DuckDB accept:
  - `DATE 'YYYY-MM-DD'` literals
  - `IN (...)` lists
  - `BETWEEN`
  - no engine-specific functions
- Adding a template is welcome when the core needs it. Add it in a PR with a test.

### D3 · Zetaris client and adapter (`client.py`, `adapter.py`)

- Implement `ensure_single_statement`, `coerce_frame`, `ZetarisClient` (`from_env`, `execute`,
  `parse_response`), `ZetarisAdapter` and `make_adapter`.
  The statement/dtype helpers and sample factory already exist; complete the live stubs,
  including bounded pagination, without replacing tested offline behavior.
- Record one real query response with secrets removed into
  `integrations/tests/fixtures/zetaris_query_response.json` and add a test for `parse_response`.
- **Parity test:** add `integrations/tests/test_parity.py`, marked `@pytest.mark.network`. It runs
  every template with fixed parameters on both back ends and asserts equal `rows_sha256`. Paste the
  output.
- **On-demand ticker lookup:** a template or REST-table query that reads EDGAR `companyconcept` for
  a CIK outside the universe, through the REST table registered in D1. `CACHE TABLE` first; the
  first call can take about 50 s.

### D4 · Hosted LLMs on NVIDIA NIM (`meterless/llm.py`)

The chain code is merged. `build_routes_from_env` maps every role to NIM:

| role | model setting |
|---|---|
| `extractor`, `guard` | `NIM_EXTRACTOR_MODEL` (falls back to `NIM_ANALYST_MODEL`) |
| `analyst` | `NIM_ANALYST_MODEL` |
| `skeptic` | `NIM_SKEPTIC_MODEL` |

Steps:

1. Get a key at build.nvidia.com and keep it only in your local `.env`.
2. Choose three hosted chat models from the NIM catalogue and send the choice to the lead
   **before** recording. The skeptic must be from a **different model family** than the analyst.
   - extractor and guard: a mid-size, fast instruct model that follows "reply with JSON only"
     reliably
   - analyst: a strong reasoning-capable instruct model
   - skeptic: a strong model from a different family
   - Prefer models whose replies contain no visible `<think>` blocks. If a model emits them, add a
     small `strip_thinking()` step in `llm.py` with a unit test.
3. Write `integrations/tests/test_live_llm.py` (`@pytest.mark.network`):
   - one extractor call on a short sample filing returns parseable JSON whose quote passes
     `grounding_problems`
   - one analyst call returns parseable JSON
   - one skeptic call returns parseable JSON
   Paste the output in the PR.
4. **Record the cassette** (judges replay it offline), as soon as A's `data/sample/` is on `main`:

   ```
   SAMPLE_MODE=true RECORD_LLM=true  py -3 run.py --as-of <sample as_of> --pools us_equity eu_equity crypto
   SAMPLE_MODE=true RECORD_LLM=false py -3 run.py --as-of <same date>   --pools us_equity eu_equity crypto
   ```

   - The second command must run with the network disabled, and its warnings must not mention
     "model answer was unavailable".
   - Use the same `--as-of` both times; different prompts would miss the cassette.
   - Commit `data/sample/llm_cassette.jsonl` and `data/sample/extraction_cache.jsonl` (model text
     only, no secrets) in a PR.
5. The Meterless Runtime route (Nightshift) stays in the code as an **optional, off-by-default**
   path. Do not spend time on it.

### D5 · Engines sidecar (`engines/`, `meterless/engines_client.py`)

**This is where Meterless carries its load** (decision D18): the World Model holds the validated
relation graph and events with `as_of` snapshots, and H-MEM stores every recommendation and settles
it later, with conflict detection. Treat it as a core deliverable, not an extra.

- Vendor the reference implementations of **World Model** and **H-MEM** from the Meterless repo
  into `engines/vendor/`, with LICENSE and a NOTICE naming the source commit.
- Implement the HTTP API in `engines/API.md` in TypeScript (`engines/src/server.ts`). Keep it
  small: Node's built-in `http` module, or one tiny framework. Store data under `ENGINES_DATA_DIR`.
- `npm run conformance` runs both official conformance suites and must exit 0. Paste the output;
  this is strong sponsor evidence.
- `npm test` runs a smoke test that ingests 2 edges and 1 event, then checks that the snapshot
  filters by `as_of` and that H-MEM conflict detection fires on two contradicting records.
- Implement `EnginesClient` (Python) to make the given tests pass.
- Add a `Dockerfile` for the sidecar (small memory footprint: the local Docker budget is 5.6 GB in
  total). It must run in two places:
  - **locally**, through docker-compose. Judges and SAMPLE_MODE use this, and no token is needed on
    `127.0.0.1`.
  - **on AWS** behind the HTTPS proxy from D0, as the team's shared instance. There,
    `ENGINES_TOKEN` is required: requests without `Authorization: Bearer <token>` get 401.
- `EnginesClient` sends `Authorization: Bearer <ENGINES_TOKEN>` when that environment variable is
  set.

### D6 · Sponsor write-up (`docs/sponsors.md`, draft)

For each sponsor, write:

- what it does in TradePulse
- which OPM process uses it
- why it carries load: what breaks without it
- the evidence: command output, conformance results, screenshots, trace excerpts

Write only what really happened. The lead edits and submits it.

### Stretch · D7 Scout Intent

Meterless Scout Intent ships as a spec plus an eval harness, without a reference implementation.

- Prototype the request guard (reject order-execution intent and prompt injection) against the spec.
- Run its eval harness and report the metrics honestly.

## Definition of done

See `ACCEPTANCE.md`. Open one PR per task. Branch names are `d/<task>`, for example
`d/d2-templates`.
