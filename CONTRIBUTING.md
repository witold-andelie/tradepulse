# Contributing

Read [current project status](docs/STATUS.md), your folder's TASK, ACCEPTANCE and AGENTS files.
Task catalogues describe the required behavior; the status sections identify what remains.
Huyin's detailed current review assignment is in
[web/HUYIN_NEXT_STEPS.md](web/HUYIN_NEXT_STEPS.md).

## Team and current work

| Member | Scope | Remaining work |
|---|---|---|
| Lead | Core, contracts, configuration, architecture, QA and delivery | Data/service integration, honest limitations, examples, slides, video and submission |
| A | `ingest/`, approved universe/sample paths | Real collection and coverage, timezone check, snapshot and S3 upload |
| B / Huyin | `web/` | Review the integrated existing UI, resolve concrete findings and supply available visual evidence |
| C / Tanhao | `quant/` and existing B7–B9 page implementations | C9 properties; review and extend Regime, Track Record and Run Trace |
| D | `integrations/` and sponsor evidence | Zetaris deployment/client/parity, NIM model checks and cassette, engines sidecar |

Huyin's B1–B10 and accessibility work is the frontend baseline. Do not rebuild the shared base
or the existing six pages. The lead handles integration issues; B and C coordinate changes to
shared UI components and extend the same implementation.

## Workflow

1. Update `main`, then create a task branch such as `a/live-data`, `b/ui-review`,
   `c/b8-evaluation-review` or `d/d3-zetaris`. Do not resume old branches against the obsolete
   pre-integration frontend without first reconciling them with current main.
2. Read the current instructions and review existing code before implementing.
3. Run the relevant tests. Preserve given tests and assertions; add regression coverage for
   material behavior changes. Ask the lead about contract changes.
4. Open a PR against main, with the applicable acceptance checklist and genuine evidence.
   Existing implementations are credited; incomplete acceptance is listed separately.
5. Address review findings in the same branch. The lead chooses the merge strategy.
   Preserve original contributor ancestry when importing existing work, as in frontend
   integration `aaf3b5f`; do not replace it with a fresh implementation or erase its history.

The lead owns final QA and delivery. A lead-authorized integration can be published directly;
this does not change the normal review requirement for member contributions.

## Commits and evidence

- English, imperative subject, at most 72 characters. Keep each change coherent.
- Preserve original authors. Use a non-personal GitHub noreply identity when configuring a
  commit identity; never place a personal address in source, docs, fixtures or logs.
- Never commit `.env`, `data/lake/`, caches, logs, credentials or generated browser captures.
  The small validated `data/sample/` snapshot is intended to be committed when ready.
- Report only commands that actually ran and results derived from their output.
  A synthetic fixture demonstration is not a recorded market result.
- Keep downloaded references, temporary files and npm/Python caches on D: on this team's machines.

## Validation and blockers

Python uses `py -3`. Run the relevant Python folder suite and ruff. For frontend changes run
`npm test`, `npm run check:contracts` and `npm run build`, plus the applicable browser checks.

Lighthouse, axe and native screen-reader requirements remain acceptance tasks. A focused
Chromium check is useful evidence but does not certify WCAG conformance.

Report contract blockers and missing artifacts promptly. A green unit suite with skipped
lake/sample tests does not complete A's data delivery or D's live-service acceptance.
