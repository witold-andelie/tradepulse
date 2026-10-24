# TradePulse 2.0 implementation map

Historical record from Huyin's accessibility branch. Its original commits are preserved in main
by merge `aaf3b5f`. The validation and environment limitations below describe that earlier work;
see `INTEGRATION.md` and `../docs/STATUS.md` for the current baseline and remaining acceptance.

Original base: b/b2-b10-frontend at a4a516909aae88b324f95ab5facbf6fd4b531ae2. PRs #1 and #2
were open at that historical inspection; the original isolated branch was b/agent-accessible-ui.
The lead subsequently authorized publication and integration into main.

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

The original pre-integration plan used b/b2-b10-frontend as the review base. That instruction
is superseded: the lead authorized a history-preserving main integration. New review/fix PRs
start from current main rather than reconstructing the old stacked branches.

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

## Original handoff and publication history

At the original handoff this branch was local and unpublished. It was later published and
integrated without rewriting the B1/B2–B10 commits. The original patch/bundle is a historical
recovery artifact. Native assistive-technology testing and actual backend integration remain
outstanding.

The managed environment cannot create the designated chat output directory, so an internal file path is not a downloadable attachment. Use a task-client export facility if one is available; otherwise obtaining the artifact bytes remains a platform limitation. Do not claim that git fetch can retrieve this unpublished branch.

The old bundle-import instructions are superseded by the current main baseline. Update main,
retain original commits and work on concrete review findings. Do not copy the old patch over
the integrated implementation or recreate completed pages.
