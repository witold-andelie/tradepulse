# Core (`tradepulse/`) — team lead

The deterministic research pipeline and LangGraph explanation graph are implemented.
See [current project status](../docs/STATUS.md) for delivery blockers and
[limitations](../docs/honest-limitations.md) before describing results.

## Implemented modules

| Module | Role |
|---|---|
| `config.py`, `contracts.py` | Load TOML settings and validate tables/API payloads. |
| `guard.py` | Deterministic request schema/date checks and rule-based source-text screening. |
| `extract/runner.py`, `extract/grounding.py` | Bounded event extraction, quote/time grounding and hash cache. |
| `research/signals.py` | Filing signals, event priors, seed-edge validation and spillover panels. |
| `research/panels.py`, `evaluate.py`, `gates.py` | Factor panels, evaluation, G1–G5, diagnostic cards and weights. |
| `regime.py`, `regime_inputs.py` | Fragility indicators, states and lift diagnostics. |
| `ranking.py` | Composite score, expected alpha, cost-aware research tiers and focus names. |
| `backtest.py` | Walk-forward decisions, matured simulated outcomes and TrackRecord assembly. |
| `agents/explain.py`, `agents/prompts.py` | LangGraph fan-out, analyst, skeptic, bounded revision and abstention. |
| `verify.py` | Re-run evidence queries, compare row hashes, check dates and attribution sums. |
| `pipeline.py`, `ports.py` | Orchestration and injected query/LLM/engine interfaces. |
| `report.py`, `store.py`, `trace.py` | Contract-valid reports, saved runs and JSONL traces. |
| `api.py`, `../run.py` | HTTP and command-line entry points. |

The query layer and hosted LLM client are in `integrations/`. The UI consumes the unchanged
RunOutput and TraceEvent contracts.

## Entry points

`py -3 run.py --serve` starts FastAPI on `0.0.0.0:8000`.
Endpoints: `POST /run`, `GET /runs/latest`, `GET /runs/{run_id}`,
`GET /runs/{run_id}/trace`, and `GET /health`.

A health response does not establish that a complete run can execute. Default SAMPLE_MODE
requires a validated snapshot and matching cassette under `data/sample/`; they are still
absent. A configured live run currently reaches unimplemented Zetaris client/adapter methods.

Direct Python commands read process environment variables, not the root `.env` automatically.
The frontend can be previewed separately on synthetic fixtures while these dependencies are
completed. Docker Compose reads `.env` and supplies an API-mode web build.

## Current differences from the target OPM model

- Graph handling validates seed edges in the research window. Iterative LLM edge proposals,
  World Model persistence and engine snapshots are not wired into the pipeline.
- H-MEM recommendation persistence, settlement and conflict detection are pending. Current
  TrackRecord values come from the deterministic walk-forward simulation, not persisted calls.
- The request guard is deterministic. D18 configures hosted NIM for any LLM roles; this does
  not mean the current guard calls a model.
- Ranking uses walk-forward weights and out-of-sample composite IC. Factor cards display
  in-sample diagnostics. Event drift and relational spillover are excluded from walk-forward
  because their priors/edges are fitted in-sample.
- The US valuation constraint is not applied by the current pipeline.
- A requested ticker outside the loaded pool is not yet implemented as an on-demand lookup.

## Lead's remaining delivery work

1. Review A's real lake/sample and D's service/cassette evidence.
2. Wire World Model and H-MEM after D's engines sidecar passes its tests.
3. Run the real offline SAMPLE_MODE acceptance with networking disabled and inspect traces.
4. Review the integrated frontend's real API behavior and remaining accessibility evidence.
5. Produce at least three real sample input/output pairs, the demo script, slides and video.
   Keep [limitations](../docs/honest-limitations.md) and [sponsor evidence](../docs/sponsors.md)
   accurate as services and artifacts become available.

The Docker configuration exists for core/web; the engines service is not yet enabled.
