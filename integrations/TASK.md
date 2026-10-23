# Member D — Sponsor integrations (`integrations/`)

You own everything that connects TradePulse to **Zetaris** and **Meterless**:

- the Zetaris deployment, table registration and the query layer
- the LLM provider chain through Meterless Runtime and NVIDIA NIM
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
    llm.py              D4  provider chain Meterless Runtime -> NIM, record/replay cassette
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
py -3 -m pytest integrations -q        # red until implemented
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
- **Zetaris:** install it on AWS following the Zetaris AWS guide. The free tier gives $200 in credits;
  a Mini cluster costs about $80 a week.
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
- Record one real query response with secrets removed into
  `integrations/tests/fixtures/zetaris_query_response.json` and add a test for `parse_response`.
- **Parity test:** add `integrations/tests/test_parity.py`, marked `@pytest.mark.network`. It runs
  every template with fixed parameters on both back ends and asserts equal `rows_sha256`. Paste the
  output.
- **On-demand ticker lookup:** a template or REST-table query that reads EDGAR `companyconcept` for
  a CIK outside the universe, through the REST table registered in D1. `CACHE TABLE` first; the
  first call can take about 50 s.

### D4 · LLM provider chain (`meterless/llm.py`)

- Implement `read_token`, `runtime_status`, `cassette_key`, `Cassette`, `ChainClient` and
  `build_routes_from_env`.
- **Meterless Runtime runs on the lead's laptop in Europe**, not on AWS. Nightshift's Windows
  edition needs a local NVIDIA GPU; the lead has an RTX 4060 with 8 GB. Your part:
  - make `llm.py` work against it
  - write `integrations/meterless/SETUP.md`: install steps, where the proxy token file lives, and
    how to pick **one** 7–8B non-thinking model that stays resident, because an 8 GB GPU cannot
    hold two
  - write the live smoke test (`network` marker): `runtime_status` is `online`, and one extractor
    request goes through Meterless. The lead runs it and sends you the output.
  - Ask the lead whether participants get a Nightshift licence.
- NIM is hosted, so test it yourself with both the analyst and the skeptic model. They must be
  **different model families**; propose them to the lead.
- `py -3 -m integrations.meterless.llm --record` records the cassette for the three sample inputs
  that the lead provides. The cassette file is committed; it holds no secrets.

### D5 · Engines sidecar (`engines/`, `meterless/engines_client.py`)

- Vendor the reference implementations of **World Model** and **H-MEM** from the Meterless repo
  into `engines/vendor/`, with LICENSE and a NOTICE naming the source commit.
- Implement the HTTP API in `engines/API.md` in TypeScript (`engines/src/server.ts`). Keep it
  small: Node's built-in `http` module, or one tiny framework. Store data under `ENGINES_DATA_DIR`.
- `npm run conformance` runs both official conformance suites and must exit 0. Paste the output;
  this is strong sponsor evidence.
- `npm test` runs a smoke test that ingests 2 edges and 1 event, then checks that the snapshot
  filters by `as_of` and that H-MEM conflict detection fires on two contradicting records.
- Implement `EnginesClient` (Python) to make the given tests pass.
- Add a `Dockerfile` for the sidecar. It must run in two places:
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
