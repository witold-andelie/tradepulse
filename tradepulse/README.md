# Core (`tradepulse/`) — team lead

Implemented so far:

| module | purpose |
|---|---|
| `config.py` | Loads `config/tradepulse.toml`. |
| `contracts.py` | Validates tables (`validate_table`) and API payloads (`validate_payload`) against `contracts/`. |

Planned modules, mapped to OPM processes (`docs/architecture/opm/`):

| module | OPM process | notes |
|---|---|---|
| `trace.py` | every process → Trace Log | JSONL `logs/trace-<run_id>.jsonl` plus stdout. Each event matches `$defs/TraceEvent`. |
| *(Member D)* `integrations/zetaris/` | instrument "Zetaris / DuckDB" | `make_adapter(sample_mode)`, then `.run(template, params)`, which returns a `QueryResult` with `rows_sha256`. The core only calls this. |
| *(Member D)* `integrations/meterless/llm.py` | instruments "Meterless Runtime", "NVIDIA NIM" | `ChainClient.complete(role, messages, schema)` with the roles extractor, guard, analyst and skeptic, plus a record/replay cassette. |
| *(Member D)* `integrations/meterless/engines_client.py` + `integrations/engines/` | "World Model", "H-MEM" | `EnginesClient` over the Node sidecar that hosts the official reference engines. |
| `guard.py` | SD1 · Guarding Request | Schema check, order-execution intent rejected, prompt-injection screen on free text. |
| `extract/` | SD1.3 | Extractor prompt and schema (`$defs/ExtractedEvent`), the deterministic grounding check, a sha256 cache. |
| `graph/` | SD1.3 | Seed edges, LLM edge proposals with at most 3 rounds, lead-lag validation (`quant.evaluation.lead_lag_tstat`), commit to the World Model. |
| `research/` | SD1.4 | Builds the factor panels with `quant/`, gates G1–G5, weights and factor cards (`$defs/FactorCard`). |
| `regime.py` | SD1.5 | Indicators from `quant.regime_indicators`, the state, the lift. |
| `ranking.py` | SD1.5 | Composite, Grinold alpha, net edge, tiers, regime overlay, focus list. |
| `agents/` | SD1.7 | LangGraph: typed state, `Send` fan-out per focus name, analyst, skeptic, verifier and a bounded retry loop (≤ 2). |
| `verify.py` | SD1.7 · Verifying Claims | Re-runs the query and compares hashes, checks cause before move, checks that contributions sum to the score, checks no data after `as_of`. |
| `settle.py` | SD1.2 | Settles matured recommendations in H-MEM and builds the track record (`$defs/TrackRecord`). |
| `report.py` | SD1 · Reporting | Assembles `RunOutput` and validates it with `contracts.assert_payload` before returning. |
| `api.py`, `../run.py` | entry points | FastAPI (`POST /run`, `GET /runs/latest`, `GET /runs/{id}`, `GET /runs/{id}/trace`, `GET /health`) on `0.0.0.0`; `py -3 run.py --as-of ... --pools ...`. |

Delivery items owned by the lead:

- Dockerfile and docker-compose (core, engines sidecar, static web)
- `.env.example`
- 3 or more sample input/output pairs
- `docs/honest-limitations.md`
- the demo script
