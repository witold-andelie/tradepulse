# TradePulse

**An explainable ranking agent for US equities, European equities and crypto.**

TradePulse ranks about 620 instruments every day: the S&P 500 ∪ Nasdaq-100, EURO STOXX 50 and the
top crypto assets. It uses factors that have to pass three gates:

1. **Measure:** what the factor actually measures.
2. **Predict:** whether it adds information beyond price and volume.
3. **Earn:** whether anything is left after costs.

It then explains the strongest and weakest names with claims that a deterministic verifier
re-checks against the data. When the evidence is weak, it says so and abstains.

> Research and education only. Tiers are research stances, not orders. TradePulse places no trades
> and gives no investment advice.

Built for the Open Agent Hackathon 2026, on **Zetaris** (federated data layer), **Meterless**
(local runtime, World Model, H-MEM) and **NVIDIA NIM** (hosted models).

## Status

**Framework stage.** The architecture, the contracts and the module task specs are in place, and
the modules are being implemented. Nothing in this repository is a result yet. The only data
present are the **synthetic fixtures** in `contracts/fixtures/` (fictional instruments, generated
numbers).

## How it works

```
Acquiring (ingest/) ──► Market Data Lake ──► Zetaris / DuckDB
                                                  │
Recommending (tradepulse/):
  guard request → settle past calls → extract events & link graph (LLM proposes, data disposes)
  → research factors (quant/ + gates G1–G5) → assess regime (fragility monitor)
  → rank & tier (IC-weighted, net of cost) → explain (analyst + skeptic + deterministic verifier)
  → report
                                                  │
Browsing (web/) ◄── Recommendation Report · Track Record · Trace Log
```

The full model is written in OPM (Object-Process Methodology) as Graphviz DOT:
[`docs/architecture/`](docs/architecture/README.md).

## Repository map

| path | what | owner |
|---|---|---|
| `docs/architecture/` | OPM diagrams + OPL, factor spec, data sources, decision log | lead |
| `contracts/` | table and API contracts, synthetic fixtures (the only interface between modules) | lead |
| `config/` | parameters (`tradepulse.toml`), universe extras, seed graph edges | lead |
| `tradepulse/` | core: orchestration, gates, ranking, agents, verifier, adapters | lead |
| `ingest/` | data acquisition → `data/lake/`, sample snapshot → `data/sample/` | Member A |
| `web/` | React app | Member B |
| `quant/` | pure quant functions | Member C |
| `integrations/` | Zetaris query layer, Meterless runtime and engines sidecar, NVIDIA NIM chain | Member D |

Every member folder has a `TASK.md` (what to build), an `ACCEPTANCE.md` (definition of done) and an
`AGENTS.md` (rules for AI coding assistants).

## Development

```
py -3 -m pip install -e ".[ingest,dev]"
py -3 -m pytest -q                     # contract tests pass; module tests stay red until implemented
py -3 scripts/render_opm.py            # re-render the OPM diagrams after editing a .dot file
cd web && npm install && npm run dev   # web app on the synthetic fixtures
```

Copy `.env.example` to `.env` for local settings. Never commit `.env`.

## Run with Docker

```sh
docker compose up --build
```

Open http://localhost:8080. `SAMPLE_MODE=true` by default; no credentials are needed.
The core is limited to 3 GB of memory and the web server to 256 MB, so it fits Docker Desktop
with 4 GB or more allocated. Zetaris is not part of the local stack: SAMPLE_MODE reads the
committed snapshot through DuckDB, and live mode connects to the team's hosted Zetaris instance.

## License

Apache-2.0
