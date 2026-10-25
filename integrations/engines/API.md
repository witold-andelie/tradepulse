# Engines sidecar HTTP API (task D5)

This is the target server contract. The Python client and optional core bridge are implemented;
the TypeScript server/vendor engines and genuine service acceptance remain pending. The local
Compose service is commented out. See [core wiring scope](../../docs/METERLESS_WIRING.md),
[project status](../../docs/STATUS.md) and [sponsor evidence](../../docs/sponsors.md).

A small Node (TypeScript) HTTP server that hosts the **official Meterless reference
implementations** of World Model and H-MEM, listening on `127.0.0.1:8790` (`ENGINES_URL`). Inside
Docker it binds `0.0.0.0`. JSON in and out. Errors return `{"error": "<message>"}` with a 4xx/5xx
status.

Authentication: when the server's `ENGINES_TOKEN` environment variable is set (always on the
shared AWS instance), every endpoint except `GET /health` requires
`Authorization: Bearer <token>`; anything else gets 401 `{"error": "unauthorized"}`. With no token
set (local docker-compose, judges), there is no authentication. Compare tokens in constant time.

| method | path | body / query | response |
|---|---|---|---|
| GET | `/health` | — | `{"status": "ok", "engines": {"world_model": "<version>", "hmem": "<version>"}}` |
| POST | `/world-model/events` | `{"events": [ExtractedEvent]}` | `{"ingested": n, "duplicates": m}` (idempotent by `event_id`) |
| POST | `/world-model/edges` | `{"edges": [GraphEdge]}` | `{"upserted": n}` (append-only history, latest version per `edge_id` wins for a snapshot) |
| GET | `/world-model/snapshot` | `?as_of=YYYY-MM-DD` | `{"as_of": "...", "edges": [GraphEdge], "events": [ExtractedEvent]}`: only items with `valid_from` / `available_at` ≤ as_of |
| POST | `/hmem/records` | `{"records": [{"id", "symbol", "as_of", "tier", "horizon_days", "content", "provenance": {"run_id", "evidence_ids"}}]}` | `{"added": n}` |
| POST | `/hmem/query` | `{"symbol", "as_of", "k"}` | `{"records": [...]}`: only records with `as_of` ≤ the query's as_of |
| POST | `/hmem/feedback` | `{"id", "outcome": {"excess_return", "hit"}}` | `{"updated": 1}` (written to the H-MEM trust ledger) |
| GET | `/hmem/conflicts` | `?symbol=` | `{"conflicts": [...]}`: H-MEM conflict detection, e.g. a new call contradicting a recent one |

Persistence: the engines' own stores live in a data directory (`ENGINES_DATA_DIR`, default
`runs/engines/`), so memory survives restarts.

Rules:
- Use the reference implementations unchanged. They are Apache-2.0: vendor them under `vendor/`
  with their LICENSE and a NOTICE that names the source repository and commit.
- Adapting our JSON to the engine APIs happens in our own `src/` code, never by editing `vendor/`.
- `npm run conformance` must run both official conformance suites against the vendored engines
  and exit 0.
- Changing this API requires a PR reviewed by the team lead, because the core calls it.
