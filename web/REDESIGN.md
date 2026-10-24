# TradePulse 2.0 implementation map

Historical record from Huyin's accessibility branch. The branch was subsequently published
and is now being integrated with main. The original validation and environment limitations
below are preserved as provenance; see `INTEGRATION.md` for current integration status.

Base: verified latest remote b/b2-b10-frontend at a4a516909aae88b324f95ab5facbf6fd4b531ae2. PRs #1 and #2 were open and unmerged at inspection. Local isolated branch: b/agent-accessible-ui. This work is not authorized for publication.

## Product and regression map

| Requirement | Implementation | Verification |
| --- | --- | --- |
| Existing routes and root redirect | Existing router retained; Discover is additive | Original browser regression suite in Pro View; new direct-route checks |
| Agent-first entry | Guided Discover journeys select actual matching run records | New browser journeys; record-selector unit tests |
| Honest Agent capability | No freeform chat or conversational endpoint; structured API unchanged | Contract inspection; Discover capability note |
| Shared presentation | PresentationProvider; safe preference helpers; no separate rankings | Preference unit tests; both-view parity and storage-disabled browser checks |
| Leaderboard | One TanStack model for cards/table, shared helpers, URL filters/sort/page | Existing screening suite plus mode/context persistence tests |
| Detail | Same original row and explanation; progressive ordering, all contrary evidence | Parity, rejected claim, abstention and null-value checks |
| Supporting pages | Original metrics/gates preserved; Simple orientation; actual trace summary | Regression suite and chart-equivalent checks |
| Accessible visualizations | Numeric tables/disclosures for each chart family | Keyboard access and source-value assertions |
| Accessibility and reflow | Shared readable tokens, native controls/disclosures, one title-focus handler | ACCESSIBILITY.md; computed contrast, keyboard, reflow and motion checks |
| Source integrity | Client, contracts, fixtures, B1 helpers and prior tests unchanged | Git scope/hash audit and contract tests |

Only tradepulse.view is persisted in browser storage. Market filters and pagination remain in URLs; the current market return path is in memory and navigation state. No personal research questions or data are persisted.

The original browser suite is unchanged. Because the product now defaults to Simple View, its table-specific assertions are exercised with a Playwright preload that selects Pro View. This changes initial UI preference only; it does not remove assertions. Separate tests exercise the new default presentation.

Do not target main with an eventual redesign PR while PR #2 is unmerged. The review base should be b/b2-b10-frontend so reviewers see the UI-only redesign. Push/PR creation needs separate explicit user authorization.

## Final verification

- Unit tests: 5 files, 36 tests passed; the original 29 tests are unchanged. New tests cover safe preferences, original-record identity, actual discovery records and safe market return paths.
- Contracts: RunOutput and all 19 trace lines pass the existing checker.
- Build: no warnings; largest lazy ChartEngine chunk 627.54 kB (209.94 kB gzip), below the unchanged 1 MB ceiling.
- Original browser regression: 17/17 groups pass in Pro View, with the original script unmodified.
- New research/accessibility journeys: 18/18 groups pass in the production build, including both presentations at 1440/768/390/320 CSS pixels, 200% text enlargement, keyboard flow, storage disabled and data parity.
- Computed accessibility checks: 14 route/view combinations, 5,414 visible text nodes checked; minimum observed text contrast 5.66:1; sampled view-control border contrast 3.35:1; no unnamed controls or inspected effective targets below 24px. This is a focused check, not a conformance audit.
- Additional local API checks: unavailable API with Retry, REPLAY/REAL modes, contract-valid empty datasets, malformed run rejection and independent trace HTTP failure pass.
- Browser: Chromium 154.0.8037.57 on Linux. No native screen reader, native 400% zoom or non-Chromium browser was tested. 320 CSS pixels is the equivalent reflow width; see ACCESSIBILITY.md.
- Final evidence set: 100 genuine PNG captures (33 legacy route captures, 43 new route/reflow captures, 23 full-page/panel/focus captures and one API error capture). These files are kept outside the source tree and have not been uploaded or attached to any PR.

## Repeatable browser tooling

Playwright and Chromium must already be available in the tooling environment. They are not new application dependencies. From the repository root, point TRADEPULSE_PREVIEW_URL at a running local production preview and configure TRADEPULSE_CHROMIUM / TRADEPULSE_QA_DIR if needed:

```sh
node --require ./web/scripts/pro-view-preload.cjs web/scripts/browser-acceptance.cjs
node web/scripts/redesign-acceptance.cjs
node web/scripts/accessibility-check.cjs
```

The preload selects only the Pro UI preference for the legacy table suite. It does not change records, intercept requests or disable assertions. Run the redesign suite without that preload to verify the fresh Simple default.

## Handoff and publication boundary

This branch is local and unpublished. Existing B1/B2-B10 history and PRs are not rewritten. A local patch and bundle preserve a reviewable UI-only diff against the verified B2-B10 base. Native assistive-technology testing, independent team review and actual backend integration remain outstanding.

The managed environment cannot create the designated chat output directory, so an internal file path is not a downloadable attachment. Use a task-client export facility if one is available; otherwise obtaining the artifact bytes remains a platform limitation. Do not claim that git fetch can retrieve this unpublished branch.

After a bundle is exported, fetch its branch into an existing clone and create a new worktree with a fresh local branch name. Never copy source files over the B1 or B2-B10 checkout. An eventual remote branch push and Draft PR require separate authorization; while PR #2 is unmerged, the appropriate review base is b/b2-b10-frontend, not main.
