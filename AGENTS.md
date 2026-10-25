# Repository rules for AI coding assistants (any tool)

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
10. **English only** for code, comments, docs, UI text and commit messages. The lead approved
    localized labels only inside the Ticker Detail research guide on 2026-10-25. That scoped UI
    exception preserves source narratives, financial values and enums; it does not authorize
    localization of the rest of the application. See `web/AGENT_ACCESSIBILITY_DEMO.md`.

## Current implementation baseline

- Read `docs/STATUS.md` for current owners, implemented work and remaining acceptance.
  Historical notes are not a new instruction to rebuild completed modules.
- Huyin's complete frontend and accessibility work is preserved in merge `aaf3b5f`.
  Member B reviews that implementation; Member C extends its existing B7–B9 pages.
- Keep original contributor history and given test assertions. The integration preserves
  both original frontend test suites and unchanged API/table schemas.
- The standalone fixture frontend runs now. Full SAMPLE_MODE, hosted sponsor services and
  native accessibility acceptance remain incomplete; never describe them as verified.
