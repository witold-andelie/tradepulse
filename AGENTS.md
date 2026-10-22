# Repository rules for AI coding agents (Cursor, Claude Code, others)

These rules apply everywhere. A folder's own `AGENTS.md` adds rules for that folder.

1. **Stay in your folder.** Members work in `ingest/`, `web/`, `quant/` or `integrations/` and follow that folder's
   `TASK.md`. `contracts/`, `config/`, `docs/architecture/` and `tradepulse/` change only through
   PRs reviewed by the team lead.
2. **Contracts are law.** Data passed between modules must match `contracts/`. Never add, rename or
   drop a field to make code work; ask instead.
3. **Never weaken a test.** Make code pass the given tests. If a test is wrong, say so.
4. **No hard-coded results and no fabricated logs.** Every number shown or written comes from
   computation on data. Fixtures are labelled `SYNTHETIC` and must stay that way.
5. **Point-in-time.** Nothing may use data dated after the decision date (`as_of`).
6. **Secrets.** Never write keys, tokens, passwords or personal e-mail addresses into code, tests,
   logs, fixtures or docs. Configuration comes from `.env` (gitignored) and
   `config/tradepulse.toml`.
7. **No trading.** Nothing in this repository places, routes or sizes real orders. Tiers are
   research stances.
8. **Bounded work.** Every loop and retry has an explicit limit. Every network call has a timeout.
9. **Python** runs as `py -3` on the team's Windows machines. Tests: `py -3 -m pytest -q`.
10. **English only** for code, comments, docs, UI text and commit messages.
