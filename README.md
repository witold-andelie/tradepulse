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

## Current status — 24 October 2026

The quantitative core, pipeline, HTTP API and complete fixture-backed frontend are implemented.
Huyin's original B1–B10 and accessibility commits are preserved in the integration history,
including six business pages, Discover and Simple/Pro presentation.

The real-data delivery is still pending: this checkout has no lake/sample snapshot or recorded
LLM cassette. Zetaris live access and the Meterless engines sidecar are not complete. A green
offline suite does not establish that the hosted services or a credential-free SAMPLE_MODE run
have passed acceptance.

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

## Run the core

```powershell
py -3 -m pip install -e ".[ingest,agent,dev]"
py -3 run.py --serve
```

The API listens on `0.0.0.0:8000`. The health endpoint can work before a run exists;
`GET /runs/latest` returns 404 until an output has been generated and saved.

A full sample run requires A's validated snapshot under `data/sample/` and D's matching
`llm_cassette.jsonl` and `extraction_cache.jsonl`. These artifacts are not yet in this checkout.
Use the snapshot's decision date when invoking `run.py --as-of`. SAMPLE_MODE uses DuckDB and
recorded model answers; it never silently falls back to hosted services.

For direct Python execution, set configuration variables in the process environment.
Python does not automatically load the root `.env`. Docker Compose reads `.env` explicitly.
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

World Model and H-MEM are planned load-bearing integrations; the current pipeline does not yet
call the engines client. All configured LLM roles use hosted NVIDIA NIM by default (D18).
The current request guard itself is deterministic.

| Path | Responsibility | Owner |
|---|---|---|
| [docs/architecture](docs/architecture/README.md) | Target OPM model, factors, sources and decisions | Lead |
| [contracts](contracts/README.md) | Unchanged table/API schemas and synthetic fixtures | Lead |
| `config/` | Parameters, universe extras and seed-edge hypotheses | Lead |
| [tradepulse](tradepulse/README.md) | Core pipeline, research, ranking, explanation and API | Lead |
| [ingest](ingest/TASK.md) | Live collection, data quality, sample snapshot and S3 upload | A |
| [web](web/TASK.md) | Existing complete frontend, visual/interaction review and acceptance | B / Huyin |
| [quant](quant/TASK.md) | Existing math library, C9 properties, review of existing B7–B9 pages | C / Tanhao |
| [integrations](integrations/TASK.md) | Zetaris, NIM recording and Meterless engines | D |

## Validation

```powershell
py -3 -m pytest -q
py -3 -m ruff check ingest quant integrations tradepulse run.py scripts --no-cache
cd web
npm test
npm run check:contracts
npm run build
```

The latest recorded checks are 282 Python tests passed with 8 data-dependent skips, 56 frontend
tests passed, valid contract fixtures and a successful production build. Existing browser suites
passed 17/17 and 18/18 groups. See [status](docs/STATUS.md) for scope and outstanding manual QA.
Keep Python temporary files on D: with `--basetemp`. Re-render changed OPM diagrams using
`py -3 scripts/render_opm.py`.

## Docker

```powershell
docker compose up --build
```

The configuration defines core (3 GB) and web (256 MB); the engines service is still commented
out. The web server is on http://localhost:8080 and proxies `/api` to core. It uses API mode,
so it requires a saved backend run; it does not present the standalone fixture demo on failure.
Default `SAMPLE_MODE=true` does not supply the missing snapshot or cassette. Hosted Zetaris is
an external service, not part of this Compose stack.

Docker configuration exists but was not built or exercised in the frontend integration review.

## License

Apache-2.0
