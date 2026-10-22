# Contributing

## Team

| member | folder | task spec |
|---|---|---|
| Team lead | `tradepulse/`, `contracts/`, `config/`, `docs/` | `tradepulse/README.md` |
| Member A | `ingest/` | `ingest/TASK.md` |
| Member B | `web/` | `web/TASK.md` |
| Member C | `quant/` | `quant/TASK.md` |
| Member D | `integrations/` (Zetaris, Meterless, NIM) | `integrations/TASK.md` |

The team lead reviews and merges every PR, and owns QA and delivery: README, demo video, slides and
the submission.

## Workflow

1. Pull `main`. Create a branch named `<member letter>/<task>`, for example `a/a2-prices`,
   `b/b4-leaderboard`, `c/c1-indicators` or `d/d2-templates`.
2. Read your folder's `TASK.md`, `ACCEPTANCE.md` and `AGENTS.md`. Give the AI assistant the same
   files.
3. Make the given tests pass. Add tests if you like; never weaken existing ones.
4. Open a PR into `main`. Fill in the PR checklist from your `ACCEPTANCE.md` and paste the command
   output.
5. Fix review comments in the same branch. The lead squash-merges.

## Commits

- English, imperative mood, at most 72 characters in the subject: `Add EDGAR submissions parser`.
- One logical change per commit.
- Never commit `.env`, `data/lake/`, `web/node_modules/`, logs or credentials. If a secret slips
  in, tell the lead immediately; the key gets rotated first.

## Daily sync

There is one short sync per day at a fixed UTC time. Each person reports what was merged, what is
in review and what is blocked. A blocker on a contract goes to the lead the same day.
