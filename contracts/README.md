# Contracts

Contracts are the **only** interface between modules. A module may rely on what a contract says and
nothing else. Changing a contract requires a PR reviewed by the team lead, because every other
module depends on it.

The frontend integration does not change table or API schemas or regenerate fixtures.
See [current implementation status](../docs/STATUS.md). UI entry points in
`web/src/api/client.js` validate responses before rendering; legacy transport functions are
retained for existing callers. `*Page` adapters are internal UI interfaces, not new API fields.

| folder | what | checked by |
|---|---|---|
| `tables/*.json` | One file per parquet table in `data/lake/`: columns, dtypes, nullability, enums, primary key, row checks | `tradepulse.contracts.validate_table(df, name, as_of=None)` |
| `api/tradepulse.schema.json` | JSON Schema (2020-12) for the HTTP API and the trace format. The root is `RunOutput`; other payloads are under `$defs` | Python: `tradepulse.contracts.validate_payload(obj, "<Def>")` · JS: `npm run check:contracts` in `web/` |
| `fixtures/` | **SYNTHETIC** example payloads produced by `make_fixtures.py` | `tradepulse/tests/test_contracts.py` |

## Table dtypes

| dtype | pandas representation |
|---|---|
| `string` | `object` or `string` dtype holding `str` values |
| `float` | any numeric dtype except bool |
| `int` | integer dtype (`int64` or nullable `Int64`) |
| `bool` | bool dtype |
| `date` | timezone-naive `datetime64` at midnight, or `datetime.date` objects |
| `datetime` | timezone-aware `datetime64[..., UTC]` |

## API definitions (`$defs`)

`RunRequest`, `RunOutput`, `PoolSummary`, `Recommendation`, `Contribution`, `FactorCard`,
`GateResult`, `RegimeState`, `RegimeIndicator`, `Explanation`, `Claim`, `EvidenceRef`,
`TrackRecord`, `TraceEvent`, `ExtractedEvent`, `GraphEdge`.

## HTTP endpoints (served by the core, consumed by `web/`)

| method | path | request | response |
|---|---|---|---|
| `POST` | `/run` | `RunRequest` | `RunOutput` |
| `GET` | `/runs/latest` | — | `RunOutput` |
| `GET` | `/runs/{run_id}` | — | `RunOutput` |
| `GET` | `/runs/{run_id}/trace` | — | array of `TraceEvent` |
| `GET` | `/health` | — | `{"status": "ok", "sample_mode": bool}` |

## Fixtures are not results

Every instrument in `fixtures/` is fictional (`SYN001`, `SYE01.XX`, `SYC01-USD`) and
`data_mode` is `SYNTHETIC`. The web app must show a visible **SYNTHETIC FIXTURE** banner whenever
it renders them. Regenerate the fixtures with:

```
py -3 contracts/fixtures/make_fixtures.py
```

Do not regenerate or rewrite fixtures to hide source discrepancies. The current by-tier sample
counts sum to 1,808 while `settled_count` is 1,200; the frontend preserves and discloses both.
Trace timestamps and reported durations are also displayed as distinct measurements. These
generated records are not evidence that real sample data or sponsor services have run.
