# Engines sidecar HTTP API (task D5)

The server, Python client and existing core bridge now implement this contract. Start the local
sidecar with `docker compose -f integrations/engines/compose.yaml up -d --build --wait` from
the repository root. See [current measured acceptance](VALIDATION.md),
[Mac live setup](../MAC_LIVE_SETUP.md) and [sponsor evidence](../../docs/sponsors.md).

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

The Python client optionally uses ENGINES_REMEMBER_BATCH_SIZE (1-5000, default 5000) and
ENGINES_WRITE_TIMEOUT_SECONDS (greater than zero, at most 300, default the client timeout).
These affect only remember requests, not the HTTP contract or reference implementation.
Each sequential batch requires a valid added acknowledgement; identical existing IDs add
zero and conflicting content returns 409. A failure can leave earlier batches persisted.
The client does not retry a write with an unknown outcome. Read-only reconciliation via
scripts/reconcile-run.mjs checks stored provenance and IDs without changing a failed run's
acceptance. See ../HOSTED_ACCEPTANCE.md for the current Mac procedure.

`GET /activity` is an additional authenticated diagnostic route. It returns store counts and
the last 20 H-MEM ledger entries. The service also writes metadata-only `activity.jsonl` records
with real request IDs, operation names and counts. Headers and credentials are never recorded.

Implementation limits and semantics:

- Request bodies are at most 5 MiB; a batch has at most 5,000 items. Canonical World Model
  history is capped at 100,000 entries and H-MEM at 10,000 records. Capacity errors are explicit.
- GraphEdge and ExtractedEvent use the unchanged repository JSON Schema. Invalid batches are
  rejected before writes. Events are immutable by event_id; changed content returns 409.
- Edge snapshots select the latest eligible valid_from for each edge_id. Future versions do
  not hide earlier versions, including when observations arrive out of order.
- Research records retain the original content and provenance in official H-MEM storage.
  Recall selects at most 100 dated records for the exact symbol and writes official read audit
  entries. Future records are not read or touched. The core uses counts only, explicitly as
  unverified context. Semantic-memory relevance and remembered predictive accuracy are not
  claimed.
- The same settlement payload is idempotent; a changed outcome returns 409. This applies to
  completed requests, not crash-atomic transactions across the reference JSON/ledger files.
- Conflict scanning uses the unchanged official detector, isolated to at most 250 records of
  one symbol. Only opposing stances with equal horizons are reported. Dated stances can change
  legitimately; results are review candidates, never automatic trading or conflict resolution.
  The core does not consume undated conflicts in historical decisions.
- Reference persistence is single-process JSON, not a production multi-writer database.

Rules:
- Use the reference implementations unchanged. They are Apache-2.0: vendor them under `vendor/`
  with their LICENSE and a NOTICE that names the source repository and commit.
- Adapting our JSON to the engine APIs happens in our own `src/` code, never by editing `vendor/`.
- `npm run conformance` must run both official conformance suites against the vendored engines
  and exit 0.
- Changing this API requires a PR reviewed by the team lead, because the core calls it.
