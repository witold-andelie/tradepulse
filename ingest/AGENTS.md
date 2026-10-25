# Instructions for AI coding agents working in `ingest/`

You are helping Member A implement the data-ingestion module of TradePulse.

The acquisition code and real 2026-10-23 sample are implemented. Read `docs/STATUS.md` and
`ingest/REAL_DATA_EVIDENCE.md`; preserve the published hashes, source exceptions and contributor
history. Follow-up work is owned by the lead, not a new assignment for Member A.

1. Read `ingest/TASK.md` and `ingest/ACCEPTANCE.md` before writing code. Read the contract file in
   `contracts/tables/` for any table you touch.
2. Edit only files under `ingest/`, `config/universe/` and `data/sample/`. Never edit `contracts/`,
   `tradepulse/`, `quant/`, `web/` or any test under `ingest/tests/`. If a test seems wrong, stop
   and say so instead of changing it.
3. Keep the function names, arguments and return columns exactly as the stubs define them.
4. Unit tests must run offline. Put network calls in `fetch_*` functions. Keep parsing in pure
   functions that take text or JSON.
5. All HTTP goes through `ingest.net.build_session()` and a `RateLimiter`. SEC: ≤ 8 requests/s with
   a User-Agent that contains an e-mail address read from the environment.
6. Never forward-fill prices, never invent values, never write rows dated after `as_of`.
7. Never hard-code or print secrets. Configuration comes from `config/tradepulse.toml` and `.env`.
8. Use `py -3` to run Python on this machine. Run `py -3 -m pytest ingest -q` after every change.
9. Write code, comments and messages in English.
