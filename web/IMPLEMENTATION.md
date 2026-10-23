# Member B implementation and acceptance map

Baseline: remote main a5c685dfad7f4e710e2edc6d48dcc15c5428879f; B1 PR #1 open and unmerged at inspection. Git fetch failed because the configured proxy was unreachable. GitHub connector retrieved the exact B1 blobs and commit metadata; blob, tree and commit SHA checks reproduced c8e1d7da9bf18fd78ee297896e9a60b61cf857ea locally. Development branch: b/b2-b10-frontend. No remote mutations.

| Task | Implementation checklist | Verification |
| --- | --- | --- |
| B1 | Preserve exact helpers and existing tests | Original 15 Vitest cases |
| B2 | Client endpoints, 15-minute bound, strict schema validation, fixture mode, hook, retry | Client tests: modes, nulls, empty, malformed, HTTP/network errors, timeout, request and trace validation |
| B3 | Pool tabs, persistent navigation, run metadata, all specified routes, loading/error/not found, banner/footer | Browser direct loads, internal navigation, failure retry |
| B4 | Pool summary, all columns, numeric/null sorting, combined filters, 50-row pagination, sector treemap click, top/bottom links | Browser counts, interactions, keyboard and chart checks |
| B5 | Metrics, contributions, claims/checks/evidence, counter-case, models/retries, invalidation/watch, unknown symbol | Browser explained and abstained examples and unknown route |
| B6 | Pool selector, complete cards, five gates, decay charts, same-day IC, long-short, research window and explanatory intro | Browser all pools and insufficient-data states |
| B7 | All pool panels, indicators, banded history and lift with n | Browser states, charts, source values |
| B8 | Walk-forward label, provenance, counts/window, tier table, calibration diagonal/bubble n, IC per pool | Browser charts and source reconciliation warnings |
| B9 | Paired node timeline, event filters, retry/error highlighting, totals | Browser filters, events and timestamps |
| B10 | Consistent accessible visual system, responsive containers/navigation, lazy modular charts | Screenshots all routes at 1440/768/390; keyboard; production chunk checks |

## Milestones

- A: Exact B1 baseline restored. Client implemented with schema validation at the boundary; configured API failure remains visible instead of silently substituting fixtures. No endpoint is presumed available.
- B: Shell and all leaderboard interactions implemented. Chromium confirmed loaded pool counts (520 / 60 / 40), 50-row pagination, combined filters, numeric sorting, treemap click filtering, keyboard row navigation and shortlist links. A formatter callback arity defect found by browser testing was repaired.
- C: Instrument details render contract-backed metrics, signed contributions, full claim checks/evidence, analyst/skeptic metadata and source caveats. Explained and abstained examples and unknown instruments were exercised in Chromium.
- D: Factor cards, all gates, IC decay and source measurements; regime indicators/history/lift; track-record calibration/tier table/IC history; and trace timeline/event filters/totals implemented. Missing or inconsistent source measurements remain explicit. No execution or live evaluation is inferred.
- E: Responsive Chromium captures cover every page at 1440, 768 and 390 pixels. Zero page-level overflow was measured. Visual review found dynamically generated badge classes were removed by Tailwind; explicit class mappings now preserve the visual states in production.

## Source limitations

- Default mode is SYNTHETIC, imported through the client only. No live backend was supplied or authenticated. Setting VITE_API_BASE enables the documented HTTP interface. Failures never silently change provenance.
- Synthetic gate values/flags and regime measurements are generated independently. Recorded booleans are authoritative presentation inputs; this frontend does not recalculate outcomes.
- Track-record by-tier n sums to 1,808 while settled_count is 1,200. Both are preserved with a reconciliation notice. These are generated records, not historical performance.
- All nine trace node pairs have different timestamp intervals and reported duration_ms. Both are inspectable. Timeline has a source selector; timestamp span, explicit llm_call count and reported token sums are separately labeled. Model-bearing node_end records do not imply additional LLM calls.
- Calibration axes use source scale because the schema does not define their units. No portfolio return, live performance or unavailable confidence estimate is invented.
- Filing factors remain INSUFFICIENT_DATA in unsupported pools. No interactive model recomputation is offered.

## Local operation

From the repository: `cd web`, `npm install`, `npm run dev`. Leave VITE_API_BASE unset for the fixture demo. If the variable is present in .env.local or the shell, remove it and restart Vite to use fixtures. For backend integration, set VITE_API_BASE to the service URL and restart Vite. All requests have a fifteen-minute maximum for full runs.

The production host must rewrite unknown non-asset paths to index.html for BrowserRouter deep links. `npm run preview` supports local verification; no deployment was performed.

## Review and recovery

All implementation changes are confined to web/. B1 helpers, existing tests, contracts and shared fixtures are unchanged from the baseline. No dependencies were added and no remote branch or PR was modified.

Use the complete B2-B10 patch on c8e1d7da9bf18fd78ee297896e9a60b61cf857ea. A separate combined patch is provided for a5c685dfad7f4e710e2edc6d48dcc15c5428879f. Apply only one patch, in a new local worktree; do not overwrite an existing checkout or B1 PR. Re-run the acceptance commands and perform backend integration before a team PR. The user, not this task, decides when to create/push that PR.

## Validation evidence

- `npm test`: 4 files, 29 tests passed, 0 failed; exit 0. Original 15 B1 tests remain intact.
- `npm run check:contracts`: RunOutput and all 19 trace lines ok; exit 0.
- `npm run build`: success, no warnings; exit 0. Largest chunk: modular lazy ChartEngine, approximately 627 kB (210 kB gzip), below the 1 MB task ceiling. Lazy contract fixture: approximately 521 kB.
- `git diff --check`: exit 0.
- Chromium acceptance: 17/17 grouped checks passed; screenshots for 11 page variants at 1440, 768 and 390 pixels; no page-level horizontal overflow; no browser console warnings/errors during the normal fixture journey.
- Additional browser cases: unavailable `VITE_API_BASE=http://localhost:9` with working Retry, REPLAY/REAL modes, all empty supporting datasets, malformed run rejection, and independent trace HTTP failure. Mocked API responses are test inputs only.
- `web/scripts/browser-acceptance.cjs` is repeatable in an environment with a preinstalled Playwright runtime. Configure `TRADEPULSE_CHROMIUM`, `TRADEPULSE_PREVIEW_URL` and `TRADEPULSE_QA_DIR` as needed. No browser-testing dependency was added to package.json. The production preview also passed all 17 grouped checks. A production-only controlled-checkbox delay was fixed with synchronous URL navigation; chart margins were adjusted after native-size inspection.
- Screenshots are genuine Chromium captures. Browser testing found and repaired callback arity, explicit accessible select names, and Tailwind dynamic tone-class retention. No existing tests or shared fixtures were edited.

## Export constraints

During the original implementation phase, the managed environment could not create the designated chat output directory (read-only root, then permission denied outside the sandbox). No generic file-upload tool is available. Local handoff files are preserved in the task workspace. A filesystem path is not claimed to be a downloadable attachment. The task's file export facility, if provided by its client, is required to move those bytes out of the isolated environment; no GitHub push, deployment, email or external upload was used as a substitute during that phase. Subsequent branch publication is governed by separate explicit user authorization.
