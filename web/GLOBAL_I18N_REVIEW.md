# Global language correction — implementation and review record

**READY FOR REVIEW. Not ready for merge until the lead approves the multilingual product
exception and shared presentation changes.** No publication, PR, merge or deployment was performed.

## Git baseline and integration

- Verified `origin/main`: `d862ab21c985fef5f0cd6665f7f0cdc92989e509` (read-only remote inspection at task start).
- Isolated branch: `b/global-i18n-accessibility-20261025`.
- The original `b/agent-accessibility-demo-20261025` remains at
  `b64ef94abb79e58a12742aba0f4fd1fbfaa107be`.
- Its single feature commit was cherry-picked without conflicts as
  `e2644d296265947efbae9ed656c5effe84c328fe` onto verified main. The existing branch was not rewritten.
- This report belongs to the final local correction commit immediately after `e2644d2`.
  Obtain its immutable SHA with `git rev-parse HEAD`; it is also recorded in the delivery response.
- The old `AGENT_ACCESSIBILITY_DEMO.md` is preserved as the historical guide-only report;
  this report supersedes its localization scope and language-selector acceptance.

The repository's English-only instructions are unchanged. This branch explicitly proposes an
exception for application-authored multilingual UI. Team-lead approval is required before merge.
Backend, schema, fixtures, ingestion, financial algorithms, API client and dependencies are unchanged.

## Source inventory and boundaries

The initial source audit recorded 598 raw occurrences before separating authored messages from
runtime records. The final machine check covers 596 authored application messages, 521 explicit
source sites, known structured vocabularies and the existing 52 guide messages. Each of 11 locales
has 648 app/guide messages, no empty entries and identical named placeholders. Only explicit authored
message sites are translated: there is no DOM text replacement, translation service or inference.

| Surface | Application-authored localization | Original records retained |
| --- | --- | --- |
| Shell | Topbar selector, navigation, view controls, titles, provenance, footer, loading/errors | Warnings, disclaimer, run ID, source dates and modes |
| Discover | Hero, journeys, architecture, methodology, candidate actions | Instrument names and recorded narratives |
| Leaderboard | Search, filters, sorting, table, pagination, sector map and tooltips | Symbols, raw sector/filter keys, financial values |
| Detail | Stance, metrics, evidence/check labels, caveats, unavailable states | Claims, check details, IDs, hashes, models, dates, raw enums |
| Factor Lab | Gate education, controls, measurement labels, chart axes/tooltips | Definitions, availability, measurement narratives and gate notes |
| Regime | Conditions, indicators, history, chart summaries/legends, lift limitations | Indicator notes and canonical measurements |
| Track Record | Evaluation methodology, labels, charts/tables, reconciliation notices | Actual supplied evaluation records and counts |
| Run Trace | Stage labels, timing, filters, summaries, accessible alternatives | Event messages, payloads, technical node IDs and timestamps |
| Agent guide | Four questions, structured explanations, localized narration/controls | Source narratives, original claim statuses and verdict codes |

Unapproved source narratives remain verbatim, with a localized original-content label. Their language
is not supplied by the contract; `lang=""` and `dir="auto"` avoid inventing a source language.
Tickers, hashes, query/table IDs, signed numbers and ISO dates use LTR isolation where applicable.
Existing B1 numeric formatting, precision, units and canonical ISO dates are deliberately retained
for reproducibility. Localized words/count sentences never become sorting/filtering inputs.

## Product behavior

- One global provider and `tradepulse.locale` preference. Default English; one-time migration from
  the former guide preference when absent; invalid preferences become English; blocked storage
  leaves usable in-memory state.
- The visible topbar has native language names and a labeled globe, next to Simple/Pro. It remains
  available on loading, API errors, missing instruments and lazy-route rendering failures.
- Changes preserve URL, query, pool, ticker, filters, ordering, pagination, view and validated data.
  Columns update their labels without changing table data or canonical option values.
- `html.lang` follows the locale; Arabic sets RTL, mirrors the sidebar and selected navigation
  marker, and reflows header controls. Chart time/number axes retain their original direction.
- The existing guide consumes this same context; its obsolete local language selector is removed.
  Known tier/verdict/factor labels are localized alongside original inspection codes.
- Browser-native speech follows the global locale, with no autoplay; pause/resume/stop and cancellation
  on locale change, navigation and unmount remain intact. Arbitrary source narratives are not spoken
  as if translated. No matching voice or no API leaves readable localized text and clear controls.

## Route-by-locale acceptance matrix

Every PASS includes a representative interaction, actual rendered localization checks, original-data
checks and reflow at 1440, 768 and 320 CSS pixels. This is browser evidence, not dictionary coverage alone.

| Locale | Discover | Leaderboard | Detail / guide | Factor Lab | Regime | Track Record | Run Trace |
| --- | --- | --- | --- | --- | --- | --- | --- |
| en | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| zh-CN | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| zh-TW | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| es | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| fr | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| de | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| pt-BR | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| ja | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| ko | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| cs | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| ar | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

The journey selects a language on Discover, opens the market, changes sort and pagination, filters
SYN369 by its canonical sector/tier, switches Simple/Pro, opens the detail and rejected evidence,
checks original hashes/parameters/narratives/measurements, selects Factor Lab gates, opens Regime and
Track Record chart tables, filters retries and opens exact JSON trace payloads, then reloads.
Locale round-trips retain those records and state. All 11 locales are exercised on all seven routes.

## Validation and evidence

All commands below exited 0 on the final source:

| Check | Result |
| --- | --- |
| `npm test` | 93/93 tests, 14/14 files; includes 13 new localization tests, existing assertions retained |
| `npm run check:contracts` | RunOutput plus all 19 trace records valid |
| `node scripts/check-i18n.cjs` | 596 app keys in 11 locales, 521 explicit source sites, no empty values or placeholder mismatch |
| `npm run build` | Production build passed; largest entry chunk about 981 kB (348 kB gzip), below existing 1 MB warning threshold |
| `git diff --check` | Passed; final staged scope checked separately before commit |
| Existing original browser suite | 17/17 groups passed, English Pro compatibility |
| Existing redesign browser suite | 18/18 groups passed, both views, keyboard, charts and reflow |
| New global browser suite | 84/84 groups passed; 77 locale-route cases and seven shared behavior groups |
| API simulation suite | 5/5 groups passed; loading, errors, empty records, root recovery, request counts |
| Existing focused accessibility script | 14 view-route combinations; 4,550 text nodes; zero contrast, small-target or unnamed-control findings |

The focused contrast check reports minimum text contrast 5.66:1 and control border contrast 3.64:1.
It is not axe, a complete WCAG audit or certification. The new selector is additionally checked at
44 CSS pixels minimum height, with preserved focus and a visible outline. Arabic keyboard/menu/Escape,
200% root text enlargement at 320px, reduced motion, chart tables and an ARIA snapshot pass. The
existing English suite also checks 200% text enlargement and 320px equivalent reflow in both views.

105 full-page screenshots cover English, Simplified Chinese, Spanish, Japanese and Arabic × seven
routes × three widths, plus an Arabic 200%-text screenshot. Additional native-width chart captures
support visual inspection. Desktop, tablet and mobile screenshots were actually captured, with manual spot review across the five representative languages and chart families. This does not claim a human inspected every pixel of all 105 images.
Session evidence is outside tracked source at `/workspace/work/global-i18n/`:

- `global-final/results.json`, screenshots, `arabic-discover-aria.yml`, `native-speech.json`.
- `api-states/results.json`, `request-counts.json` and localized error screenshots.
- `final-original/results.json`, `final-redesign/results.json`, `final-accessibility/contrast-targets.json`.
- `final-validation/results.json` and exact command logs; `visual-details/` chart captures.

These are local session evidence paths, not downloadable attachment claims. Reproduce using the
committed scripts and an already available Playwright/Chromium installation; no app dependency is added:

```sh
cd web
npm ci
npm test
npm run check:contracts
node scripts/check-i18n.cjs
npm run build
npm run preview -- --host 127.0.0.1 --port 5185 --strictPort
# In another terminal from the repository root:
TRADEPULSE_PREVIEW_URL=http://127.0.0.1:5185 TRADEPULSE_CHROMIUM=/usr/bin/chromium node web/scripts/global-i18n-acceptance.cjs
# Existing English suites:
TRADEPULSE_PREVIEW_URL=http://127.0.0.1:5185 TRADEPULSE_CHROMIUM=/usr/bin/chromium node --require ./web/scripts/pro-view-preload.cjs web/scripts/browser-acceptance.cjs
TRADEPULSE_PREVIEW_URL=http://127.0.0.1:5185 TRADEPULSE_CHROMIUM=/usr/bin/chromium node web/scripts/redesign-acceptance.cjs
TRADEPULSE_PREVIEW_URL=http://127.0.0.1:5185 TRADEPULSE_CHROMIUM=/usr/bin/chromium node web/scripts/accessibility-check.cjs
```

For intercepted API cases, build a separate QA output with
`VITE_API_BASE=http://127.0.0.1:5196 npm run build -- --outDir /tmp/tradepulse-api-qa --emptyOutDir`,
serve it with `npm run preview -- --host 127.0.0.1 --port 5195 --strictPort --outDir /tmp/tradepulse-api-qa`,
then run `node web/scripts/global-i18n-api-acceptance.cjs` from the repository root. The browser
intercepts that test API URL with unchanged authorized fixture responses or explicit failure/empty
simulations. No backend is started or claimed as accepted. Eleven locale changes leave exactly one
GET `/runs/latest`, one GET trace and zero POST requests. Do not rebuild a preview's served directory
while a browser suite is using it.

During development, precise role selectors resolved ambiguity when singular/plural labels translated
identically. New tests also wait for React state before checking speech errors and compare raw numeric
values rather than translated units. An initial text-enlargement overflow in the brand was fixed. Native-width visual review also found a crowded calibration legend, edge-clipped date ticks and dense trace ticks; vertical legend layout, boundary-label suppression and overlapping-tick suppression resolve them. Arabic interpolation isolates canonical ASCII parameters in canvas/ARIA sentences as well as DOM rich text.
A supplemental screenshot attempt overlapped a rebuild; it was rerun after the build completed.
No existing assertions were weakened. The historical guide-only browser suite expects the deliberately
removed local selector and is superseded by the global suite, rather than edited to conceal that change.

## Honest limitations and lead review

- Current standalone preview is `SYNTHETIC`, run `synthetic-fixture-0001`, decision context 2026-10-21.
  No live backend or real-data end-to-end acceptance was performed. Main's new data delivery is preserved.
- Original synthetic provenance remains imperfect: evidence references do not supply underlying rows;
  `cause_before_move` does not provide independently inspectable event/move dates. The UI explicitly
  states the missing-date/synthetic-check limitation and does not invent dates or causal support.
- Fixture counts and timing inconsistencies remain visible: by-tier evaluation counts total 1,808 while
  settled count is 1,200; trace reported durations differ from timestamp intervals; regime reconciliation
  notices are retained. Localization changes none of those records or their meaning.
- Native Chromium exposes speech APIs but zero voices. Speech-language selection, lifecycle and error
  handling pass with a clearly identified test double, not audible playback. Real voice quality,
  pronunciation and OS/browser compatibility remain unverified. Browser voices may use network services.
- NVDA/VoiceOver and native browser zoom were unavailable. CSS text enlargement and equivalent-width
  reflow are useful checks, not a substitute for those tests. Neither axe nor Lighthouse is installed;
  no score or WCAG certification is claimed.
- All 11 catalogs are populated and rendered, but the ten non-English translations have not received
  independent native-speaker or financial-domain proofreading. Human review is a remaining priority.
- The first entry bundle includes all dictionaries; it remains below the existing 1 MB threshold but
  has a performance cost. Locale lazy loading is deferred to avoid a larger asynchronous architecture.
- Lead review must approve the English-rule exception, shared shell/provider/CSS changes and terminology.
  No backend, data-team, API schema or fixture work is required for this UI correction.

## Shared-file merge considerations

- `App.jsx`: one outer locale provider, topbar control, localized persistent shell and root-error recovery;
  existing data/view providers and routes are preserved.
- `components/ui.jsx`, `State.jsx`: shared labels/statuses/errors and original-source boundaries.
- `components/ResearchGuide.jsx`, `CandidateCard.jsx`: authored educational text and structured display labels.
- `components/ChartFigure.jsx`: localized figure/table controls, captions and headers; same numerical data.
- `components/ChartEngine.jsx`: an explicit LTR chart boundary and overlapping-tick suppression, preserving axes and signs in RTL.
- `components/agentResearch/GuidedResearch.jsx`, `summary.js`: global locale consumption and optional
  display-field narration callback; existing four-question model and original values remain intact.
- `lib/figureSummaries.js`: optional translator for complete accessible sentences; existing computations
  and default English behavior remain unchanged and covered by original tests.
- `index.css`: selector/reflow, source labels, bidi isolation and scoped RTL layout; original theme retained.
- The seven business page files and `NotFoundPage.jsx` change display messages, known labels and rich
  interpolation only. Canonical filters, query parameters, calculations, page adapters and API use are retained.

These files overlap shared frontend work. Review the entire local correction as one unit; dictionaries
and their call sites must travel together. The original feature integration is a separate local commit.

## Exact file manifest

This correction changes 39 files relative to `e2644d2`: 19 modified and 20 added.
```text
M web/src/App.jsx
M web/src/components/CandidateCard.jsx
M web/src/components/ChartEngine.jsx
M web/src/components/ChartFigure.jsx
M web/src/components/ResearchGuide.jsx
M web/src/components/State.jsx
M web/src/components/agentResearch/GuidedResearch.jsx
M web/src/components/agentResearch/summary.js
M web/src/components/ui.jsx
M web/src/index.css
M web/src/lib/figureSummaries.js
M web/src/pages/Detail.jsx
M web/src/pages/Discover.jsx
M web/src/pages/Factors.jsx
M web/src/pages/Leaderboard.jsx
M web/src/pages/NotFoundPage.jsx
M web/src/pages/Regime.jsx
M web/src/pages/Trace.jsx
M web/src/pages/TrackRecord.jsx
A web/GLOBAL_I18N_REVIEW.md
A web/scripts/check-i18n.cjs
A web/scripts/global-i18n-acceptance.cjs
A web/scripts/global-i18n-api-acceptance.cjs
A web/src/i18n/Locale.jsx
A web/src/i18n/catalog.js
A web/src/i18n/en.json
A web/src/i18n/errors.js
A web/src/i18n/labels.js
A web/src/i18n/locale.test.js
A web/src/i18n/locales/ar.json
A web/src/i18n/locales/cs.json
A web/src/i18n/locales/de.json
A web/src/i18n/locales/es.json
A web/src/i18n/locales/fr.json
A web/src/i18n/locales/ja.json
A web/src/i18n/locales/ko.json
A web/src/i18n/locales/pt-BR.json
A web/src/i18n/locales/zh-CN.json
A web/src/i18n/locales/zh-TW.json
```

The full branch differs from verified main in 46 files, all under `web/`, including the original feature integration.
```text
web/AGENT_ACCESSIBILITY_DEMO.md
web/GLOBAL_I18N_REVIEW.md
web/scripts/agent-research-acceptance.cjs
web/scripts/check-i18n.cjs
web/scripts/global-i18n-acceptance.cjs
web/scripts/global-i18n-api-acceptance.cjs
web/src/App.jsx
web/src/components/CandidateCard.jsx
web/src/components/ChartEngine.jsx
web/src/components/ChartFigure.jsx
web/src/components/ResearchGuide.jsx
web/src/components/State.jsx
web/src/components/agentResearch/GuidedResearch.jsx
web/src/components/agentResearch/GuidedResearch.module.css
web/src/components/agentResearch/agentResearch.test.js
web/src/components/agentResearch/messages.js
web/src/components/agentResearch/speech.js
web/src/components/agentResearch/summary.js
web/src/components/agentResearch/useReadAloud.js
web/src/components/ui.jsx
web/src/i18n/Locale.jsx
web/src/i18n/catalog.js
web/src/i18n/en.json
web/src/i18n/errors.js
web/src/i18n/labels.js
web/src/i18n/locale.test.js
web/src/i18n/locales/ar.json
web/src/i18n/locales/cs.json
web/src/i18n/locales/de.json
web/src/i18n/locales/es.json
web/src/i18n/locales/fr.json
web/src/i18n/locales/ja.json
web/src/i18n/locales/ko.json
web/src/i18n/locales/pt-BR.json
web/src/i18n/locales/zh-CN.json
web/src/i18n/locales/zh-TW.json
web/src/index.css
web/src/lib/figureSummaries.js
web/src/pages/Detail.jsx
web/src/pages/Discover.jsx
web/src/pages/Factors.jsx
web/src/pages/Leaderboard.jsx
web/src/pages/NotFoundPage.jsx
web/src/pages/Regime.jsx
web/src/pages/Trace.jsx
web/src/pages/TrackRecord.jsx
```

## Reproducible 60-second demo

1. **0–10s:** Open `/discover` with a fresh preference. Use the visible topbar globe/language selector
   to choose Simplified Chinese; point out the localized navigation and synthetic-data banner.
2. **10–20s:** Open the market in Simple View, search `SYN369`, then switch to Pro. Its canonical identity,
   rank 4/520, displayed score +1.39 and recorded tier remain the same.
3. **20–35s:** Open SYN369 and its four-question localized guide. Expand the rejected claim in original
   evidence. Explain that the recorded abstention is separate from the research tier.
4. **35–45s:** Read the localized synthetic/temporal limitation: source checks do not provide the event
   and movement dates. Show original evidence IDs/hashes; do not endorse the rejected capacity claim.
5. **45–52s:** If the device has a matching voice, explicitly Play, Pause and Stop. Otherwise show the
   localized no-voice message and readable guide; do not simulate audible output for the audience.
6. **52–60s:** Switch to Arabic to show RTL, confirm unchanged rank/score/identifiers and return to the
   leaderboard with the search/context intact. No ranking is recalculated and no Agent run is requested.
