# Instructions for AI coding agents working in `integrations/`

You are helping Member D integrate the sponsor technologies (Zetaris, Meterless, NVIDIA NIM).

1. Read `integrations/TASK.md`, `integrations/ACCEPTANCE.md` and `integrations/engines/API.md`
   first.
2. Edit only files under `integrations/` and `docs/sponsors.md`. Never edit `contracts/`,
   `tradepulse/`, `ingest/`, `quant/`, `web/` or the given tests in `integrations/tests/`.
3. Never create, request, print or store credentials. API keys and tokens come from environment
   variables or token files that the human sets up. Error messages never include them.
4. One SQL statement per Zetaris call. Every call has a timeout and a fresh X-Request-ID.
5. Never add a code path that lets an LLM or a user send arbitrary SQL. Queries go only through
   the templates in `zetaris/templates/` and `render()`.
6. SAMPLE_MODE must work offline: DuckDB plus the cassette. Never fall back to the network
   silently.
7. Do not modify the vendored Meterless reference engines. Adapt them in our own code.
8. Bound every loop and retry.
9. Use `py -3` for Python on this machine. Run `py -3 -m pytest integrations -q` after every change.
10. Write code, comments and messages in English.
