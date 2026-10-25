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
| `engines.py` | Opt-in, bounded World Model snapshots, dated H-MEM counts, pending-record mapping and caller-driven feedback. |
| `report.py`, `store.py`, `trace.py` | Contract-valid reports, saved runs and JSONL traces. |
| `api.py`, `../run.py` | HTTP and command-line entry points. |

The query layer and hosted LLM client are in `integrations/`. The UI consumes the unchanged
RunOutput and TraceEvent contracts.

## Entry points

`py -3 run.py --serve` starts FastAPI on `0.0.0.0:8000`.
Endpoints: `POST /run`, `GET /runs/latest`, `GET /runs/{run_id}`,
`GET /runs/{run_id}/trace`, and `GET /health`.

A health response does not establish that hosted services work. The validated real snapshot
is delivered under `data/sample/`; `py -3 serve.py` verifies it and computes a saved run on
fresh startup. Its matching cassette is still absent, so current model answers abstain.
A configured live run still requires D's Zetaris client/adapter delivery.

Direct Python commands read process environment variables, not the root `.env` automatically.
The frontend can be previewed separately on synthetic fixtures while these dependencies are
completed. Docker Compose reads `.env` and supplies an API-mode web build.

## Current differences from the target OPM model

- Graph handling validates seed edges in the research window. With an explicitly enabled
  live engine, the core commits grounded events/validated edges and uses a checked as-of
  World Model snapshot. This wiring is tested on injected synthetic ports; official engine
  execution and iterative LLM edge proposals remain unverified/unimplemented respectively.
- Opt-in H-MEM wiring recalls bounded dated record counts and writes original recommendations
  with stable run identities/provenance. Caller-driven feedback mapping is prepared. Automatic
  pending selection/idempotency and dated conflict semantics are not specified by the current
  sidecar API and remain separate acceptance. TrackRecord stays the walk-forward simulation.
- The request guard is deterministic. D18 configures hosted NIM for any LLM roles; this does
  not mean the current guard calls a model.
- Ranking uses walk-forward weights and out-of-sample composite IC. Factor cards display
  in-sample diagnostics. Event drift and relational spillover are excluded from walk-forward
  because their priors/edges are fitted in-sample.
- The US valuation constraint is not applied by the current pipeline.
- A requested ticker outside the loaded pool is not yet implemented as an on-demand lookup.

## Lead's remaining delivery work

1. Upload A's locally verified complete lake when D supplies the private destination/access.
2. Validate the prepared [core bridge](../docs/METERLESS_WIRING.md) against D's actual official
   engines and agree pending/conflict semantics before automatic settlement.
3. Record actual NIM answers and repeat offline model replay. The current data-only pipeline
   and default-engine network isolation already pass.
4. Recheck the real frontend after model/service delivery; complete native guide acceptance.
5. Finalize slides/video/sponsor evidence. Three real input/output/trace pairs and demo content
   are already delivered.
   Keep [limitations](../docs/honest-limitations.md) and [sponsor evidence](../docs/sponsors.md)
   accurate as services and artifacts become available.

The Docker configuration exists for core/web; the engines service is not yet enabled.
Credential-free [CI](../docs/CI.md) checks Windows Python and Node 22/24 frontend acceptance.
