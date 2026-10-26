# TradePulse

**An explainable ranking agent for US equities, European equities and crypto.**

TradePulse's target universe combines the S&P 500 and Nasdaq-100, EURO STOXX 50 and crypto
assets. Each pool is ranked separately. Factors must establish what they measure, whether they
predict beyond a price-volume baseline, and whether an edge survives modeled costs.

LLMs extract events, draft explanations and challenge claims. Deterministic code calculates
scores, evaluates gates, assigns research stances and verifies the supporting evidence.
Unsupported explanations abstain.

> Research and education only. Tiers are research stances, never orders. TradePulse places no
> trades. Synthetic fixtures and historical evaluation are not live investment performance.

## Hackathon track

**Primary track: Track 2 — The Agent That Can Explain Why.** TradePulse is built around that
problem: it combines market, filing, attention and relationship evidence; separates descriptive
signals from predictive and cost-surviving ones; drafts claims through an analyst/skeptic flow;
and verifies every explanation against query evidence. When the evidence or model answer is
unavailable, it abstains instead of inventing a rationale.

## Current status — 26 October 2026

The quantitative core, pipeline, HTTP API and complete fixture-backed frontend are implemented.
Huyin's original B1–B10 and accessibility commits are preserved in the integration history,
including six business pages, Discover and Simple/Pro presentation.
Ticker Detail also includes a localized research guide and optional browser speech. Its
guide-only language exception is approved; source narratives and financial values are preserved.
See [guide scope and remaining acceptance](web/AGENT_ACCESSIBILITY_DEMO.md).

The real seven-table sample for **2026-10-23** and verified crypto configuration are prepared.
The sample is below 25 MB and includes hashes, source-exception evidence and offline validation.
The strict data audit passes 31 of 32 checks: 35 filings have no permitted exhibit on their
source index pages. The lead accepted these verified source exceptions for release; strict
completeness remains false. See [real-data evidence](ingest/REAL_DATA_EVIDENCE.md).

A full three-pool run completed with networking blocked. Without D's matching model cassette,
its nine explanations abstained; the unchanged research gates yielded no ACTIVE factors and
all 616 records were NO_CALL. These results are preserved rather than replaced with invented
outputs. Hosted Zetaris, Meterless engines and model acceptance remain incomplete.

Outside that sponsor-service work, the required product path is implemented: reproducible
ingestion and a committed real sample, point-in-time factor research, walk-forward ranking,
regime overlays, grounded explanation and abstention, traceable API output, the responsive web
experience, offline startup, containers and CI. The remaining non-sponsor items are acceptance
or documented extensions rather than broken release paths:

- the new Ticker Detail guide still needs a native NVDA/VoiceOver and audible-speech spot check;
- the target US price-to-sales constraint is not yet connected to the pipeline;
- arbitrary out-of-universe ticker lookup and an independent weekend crypto decision clock are
  not implemented;
- iterative model-proposed graph expansion remains future work.

These gaps are not silently simulated. Current runs disclose the missing valuation constraint,
the frontend exposes only loaded symbols, and the limitations document records the clock and
graph scope. None depends on presentation slides, which are intentionally outside this status.

Read [project status and remaining owners](docs/STATUS.md),
[frontend integration](web/INTEGRATION.md), and [honest limitations](docs/honest-limitations.md).

## Preview the implemented frontend

The standalone frontend runs on bundled **SYNTHETIC** contract fixtures without backend services
or credentials. Leave `VITE_API_BASE` unset.

```powershell
cd web
npm ci
npm run dev
```

Open http://localhost:5173. The root opens US equities; Discover is available at `/discover`.
The other routes are Ticker Detail, Factor Lab, Regime, Track Record and Run Trace.
The persistent banner identifies fictional instruments and generated numbers.

On the team's Windows machines, set `npm_config_cache` to a folder on D: before installing.
Use Node 22.12+ within the 22 LTS line or Node 24+; Node 20.19+ is also supported. The existing
libraries were upgraded for security on 25 October; see [dependency policy](web/DEPENDENCIES.md).

## Run the core

```powershell
py -3 -m pip install -e ".[ingest,agent,dev]"
py -3 serve.py
```

The managed launcher listens on `127.0.0.1:8000`. On a fresh SAMPLE_MODE checkout it verifies
the frozen sample and generates a saved run before starting the API; subsequent starts reuse
it. It does not automatically call or record live models. The lower-level `run.py --serve`
command still exposes only the HTTP service. See [running instructions](docs/RUNNING.md).

The real snapshot is under `data/sample/`. Use its decision date:

```powershell
$env:SAMPLE_MODE = "true"
$env:RECORD_LLM = "false"
py -3 run.py --as-of 2026-10-23
```

SAMPLE_MODE uses DuckDB and recorded model answers; it never silently falls back to hosted
services. The matching `llm_cassette.jsonl` and model extraction cache are not delivered yet,
so unavailable model answers lead to abstention. Record them against this exact redacted-text
snapshot, not the earlier excluded artifact described in PR #5.

For the core and integrations, set configuration variables in the process environment.
Ingestion explicitly reads its contact settings from the ignored root `.env`; this does not
load all core/provider settings into the process. Docker Compose reads `.env` explicitly.
The frontend reads `web/.env.local`; set `VITE_API_BASE=http://localhost:8000` there only after
a backend run is available. Configured API failures remain visible instead of loading fixtures.

## Architecture and ownership

```text
ingest -> parquet lake -> templated DuckDB / planned Zetaris live adapter
      -> event extraction + deterministic factor research and gates
      -> walk-forward weights, regime and ranking
      -> LangGraph analyst / skeptic / verifier -> report, API and trace
      -> fixture-backed or API-backed React frontend
```

World Model and H-MEM have an opt-in core bridge against the agreed sidecar API: snapshot inputs,
bounded historical memory context and research-record persistence. Official engine execution,
automatic pending settlement and dated conflicts still need D's delivery/semantics acceptance.
SAMPLE_MODE never auto-connects to engine HTTP services. See [wiring scope](docs/METERLESS_WIRING.md).
All configured LLM roles use hosted NVIDIA NIM by default (D18).
The current request guard itself is deterministic.

| Path | Responsibility | Owner |
|---|---|---|
| [docs/architecture](docs/architecture/README.md) | Target OPM model, factors, sources and decisions | Lead |
| [contracts](contracts/README.md) | Unchanged table/API schemas and synthetic fixtures | Lead |
| `config/` | Parameters, universe extras and seed-edge hypotheses | Lead |
| [tradepulse](tradepulse/README.md) | Core pipeline, research, ranking, explanation and API | Lead |
| [ingest](ingest/TASK.md) | Preserved A implementation; real collection, sample and remaining source/upload acceptance | Lead, taking over A |
| [web](web/TASK.md) | Existing complete frontend, visual/interaction review and acceptance | B / Huyin |
| [quant](quant/TASK.md) | Existing math library, C9 properties, review of existing B7–B9 pages | C / Tanhao |
| [integrations](integrations/TASK.md) | Zetaris, NIM recording and Meterless engines | D |

## Validation

[GitHub Actions CI](docs/CI.md) runs Python/Ruff/offline-sample acceptance on Windows and
frontend tests/contracts/build/audit on Node 22 and 24. It needs no cloud credentials and
publishes measured reports; live sponsor acceptance remains separate.

```powershell
py -3 -m pytest -q
py -3 -m ruff check ingest quant integrations tradepulse run.py scripts --no-cache
cd web
npm test
npm run check:contracts
npm run build
```

The collector's latest checks are **642 Python tests passed, none skipped**. The research-guide
and provenance follow-up has **89 frontend tests passed**, valid contract fixtures and a successful production build. Existing browser suites
passed 17/17 and 18/18 groups. See [status](docs/STATUS.md) for scope and outstanding manual QA.
The full production lake is ignored rather than committed; its seven lake cases require local
collection or the private handoff. At the initial real-sample release, a clean export passed **588 tests with 7 expected
production-lake skips**, including the committed sample test, with no external network attempts.
Keep Python temporary files on D: with `--basetemp`. Re-render changed OPM diagrams using
`py -3 scripts/render_opm.py`.

Independent Ticker Detail checks now include Lighthouse 100 desktop/mobile, 28 axe-core
cases without violations and 18 native zoom cases. See [actual scope and remaining reader
acceptance](web/ACCESSIBILITY_ACCEPTANCE.md). A's [private full-lake handoff](ingest/DELIVERY.md)
is built and locally verified; actual S3 upload still awaits a supplied destination/access.
Three [computed real-data examples](examples/README.md) include inputs, outputs and original
traces, with explicit unavailable-model abstention and zero network attempts.

## Docker

```powershell
docker compose up --build
```

The configuration defines core (3 GB) and web (256 MB); the engines service is still commented
out. The web server is on http://localhost:8080 and proxies `/api` to core. On a fresh sample
startup the core computes and saves a run; web waits for its health check. Named volumes retain
the runs and traces. An API error stays visible instead of switching to fixture data.
Default `SAMPLE_MODE=true` uses the delivered snapshot but does not supply its missing model cassette. Hosted Zetaris is
an external service, not part of this Compose stack.

The actual core/web images were built and started with fresh volumes in an isolated local
Compose project. All nine real-API browser groups passed through nginx, including 320 px
reflow and the deliberate failure case. See [runtime evidence](docs/validation/README.md).
The engines service and hosted sponsor acceptance are still pending.

The [submission preparation pack](docs/submission/README.md) contains a three-minute demo
script, an eight-slide outline and actual product captures. Its cloud-service scenes and
submission declarations remain drafts until their underlying evidence is supplied.

## License

Apache-2.0
