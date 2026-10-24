# Huyin frontend integration

This integration preserves Huyin's work instead of replacing it with the later placeholder
frontend. It combines main `55ddedd` with `b/agent-accessible-ui` at `f9c8e0b`, including
the original B1 commit `c8e1d7d`, B2–B10 commit `a4a5169` and accessibility commits
`e2c3818` and `f9c8e0b`. The original commits and authors remain in the merge ancestry.

## Reused implementation

- All six business pages, their filtering, pagination, drill-down and evidence rendering.
- Discover, Simple/Pro presentation, research guidance and context-preserving navigation.
- The design system, responsive layout, mobile menu, keyboard behavior and focus work.
- Modular lazy ECharts, chart data disclosures and keyboard-operable sector filters.
- Strict API schema validation, source provenance and honest data discrepancy disclosures.
- Huyin's unit tests and original browser/accessibility scripts, without removing assertions.

## Compatibility work

- Main's `*Page` names and prop signatures delegate to Huyin's existing implementations.
- Both hook import paths use one cancellable `RunOutputProvider`; `retry` and `reload` are
  aliases. The UI validates API responses against the unchanged schema.
- Original named client transport functions remain compatible with their existing tests.
  The UI uses `loadValidatedRunOutput` and `loadValidatedTrace`; `createClient` preserves
  Huyin's strict client API. Her original client tests have their own filename so both
  pre-existing suites run unchanged.
- `Chart` delegates to `ChartFigure`, retaining the modular renderer and existing numeric
  alternatives. The shared figure also supports the agreed columns/rows table interface.
- The application shell owns global provenance, Run notes and footer; `Page` and `PageTitle`
  share heading behavior without introducing nested main landmarks.
- Track Record follows the current score-percentile/outcome definition and horizontal 50%
  reference. No contracts or fixture values were changed to make the presentation work.
- Main's Docker, nginx, package lock and backend files are retained.

## Remaining work and ownership

- Lead: review the integration diff, backend compatibility and final acceptance. Do not ask
  Huyin to resolve the duplicated-base work by rebuilding pages.
- Huyin: review visual and interaction fidelity, help attach existing screenshots, and fix
  concrete review findings. B4–B6 and the design system are existing work.
- Tanhao: review and extend the existing Regime, Track Record and Run Trace pages, rather
  than creating a second set of pages.
- Team acceptance: run Lighthouse, axe and a native screen-reader spot check. Existing
  Chromium checks do not substitute for those requirements. Actual backend integration
  still requires a real sample run and services; no live results are claimed here.

The earlier `IMPLEMENTATION.md`, `REDESIGN.md` and `ACCESSIBILITY.md` remain historical evidence.
Fresh validation results must identify the integrated build and actual commands used.

## Integration validation, 2026-10-24

- `npm test`: 10 files, 56 tests passed. Main's original tests and Huyin's original tests
  are retained; three new checks cover strict snapshot isolation, cancellation and rejection
  of malformed API records on the application entry point.
- `npm run check:contracts`: RunOutput and all 19 trace lines passed.
- `npm run build`: passed without chunk warnings; largest chunk 627.84 kB.
- Original `browser-acceptance.cjs`, with `pro-view-preload.cjs`: 17/17 groups passed.
- Original `redesign-acceptance.cjs`: 18/18 groups passed, including both presentations,
  keyboard use, 320 CSS pixel reflow and 200% text enlargement. This is not a claim of native
  browser zoom or screen-reader testing.
- Original `accessibility-check.cjs`: 14 route/view combinations and 5,414 visible text nodes;
  minimum measured text contrast 5.66:1, zero reported contrast failures, unnamed inspected
  controls or inspected targets below 24px. This focused check is not an axe or WCAG audit.
- Genuine desktop and mobile captures were inspected. Browser suites reported no console
  warnings or errors. Evidence is local under `D:/AI_Models/hackson/.work/huyin-integration/`,
  outside the source tree. The original browser scripts and existing test assertions were
  verified unchanged against their source commits.

Browser scripts used a preinstalled Playwright runtime and system Chrome; no application
dependency was added. TEMP/TMP and browser evidence were directed to D:. Lighthouse, axe,
native assistive technology and the real backend remain pending team acceptance.
