# Global internationalization V2 integration

This is a frontend-only proposal based on main `eee913ad7b310e277b8b334ab6649e5cb0877bc4`.
The task authorizes one implementation branch, `b/global-i18n-accessibility-v2-20261026`,
and at most one implementation PR. No merge or deployment is authorized.
The original main, feature, repair, and historical QA-documentation branches remain intact.
The historical approval for guide-only localization is not presented as automatic approval
of this wider proposal. Team-lead review remains required.

## Patch provenance

- Ported the frontend changes from `5b3ff33d774416bf3fe318ef54b8f087dea1c531` and the chart-axis follow-up `3d2ae4ff1a74837b9dd41bfe8d505ca2f0861584`.
- The first patch conflicted in App, ResearchGuide, Trace and TrackRecord. Resolutions retained current-main provenance and trace semantics before applying localization.
- Did not reapply `e2644d296265947efbae9ed656c5effe84c328fe`: its web tree is identical to `b64ef94abb79e58a12742aba0f4fd1fbfaa107be`, already in main's ancestry.
- The local historical repair `cd2b610049424fd6b3b7c8c169a9e2e426acc1b1` was available. Selected UI, speech, filter and regression changes were ported, without importing its obsolete base or dependencies.
- Neither the old implementation branch nor the QA-documentation branch was merged as-is.

## Preservation record for the twelve shared files

| File | Current-main behavior retained | V2 presentation change / regression evidence |
| --- | --- | --- |
| `AGENT_ACCESSIBILITY_DEMO.md` | Historical author and lead acceptance record stays verbatim. | This separate document describes the wider V2 scope; historical pass counts are not V2 evidence. |
| `scripts/agent-research-acceptance.cjs` | All original financial, evidence, temporal, keyboard, speech, error and cancellation assertions. | Uses the global selector and waits for the requested application/guide catalog. All eleven locales receive responsive checks. Catalog readiness waits require the guide only on Ticker Detail, so returning to Discover cannot wait for an absent region. |
| `src/App.jsx` | Named Run context, run-aware `dataModeBanner(data.data_mode, data)`, original warnings/disclaimer and one main landmark. The brand keeps its visible-text accessible name. | Global selector, localized shell and a guide-resource route gate. No source run is inferred or recomputed. |
| `src/components/ResearchGuide.jsx` | REPLAY is a sample snapshot; unavailable model recordings may cause abstentions. | Same caution translated; the older assertion of available recorded model answers is not restored. |
| `src/components/agentResearch/GuidedResearch.jsx` | Original abstention summary, recorded failures, source boundaries and existing speech controller. | Global locale, localized structured labels, visible Listen entry and on-demand guide gate. |
| `src/components/agentResearch/messages.js` | English fallback, all 52 keys per locale, corrected missing-check wording and legacy public helpers. | English is eager; ten guide dictionaries are separate cached lazy imports. Existing unit assertions preload them in test-only setup. |
| `src/components/agentResearch/speech.js` | Global paused-engine recovery, generation isolation, event lifecycle, watchdog and no autoplay. | Script/region-aware matching, without swapping explicit Chinese or Portuguese regions. |
| `src/components/agentResearch/summary.js` | Recorded summary is retained when checks are absent and is excluded from speech. | Optional localized field descriptions; source narratives and verdicts remain untouched. |
| `src/components/agentResearch/useReadAloud.js` | Owned cancellation on route/instrument/locale/voice change and disposal. | Bounded enumeration retries, event listener and manual refresh. |
| `src/pages/Detail.jsx` | Original claims/checks/evidence, separate tiers and verdicts, missing timestamps and absent-source disclosures. | Localized labels plus canonical LTR values, without translating Agent source text. |
| `src/pages/Trace.jsx` | Failed spans, retry/error chronology, timing discrepancies, original messages and run-aware provenance. Transparent offsets retain the main decal behavior. | Localized labels and accessible axis descriptions; source events and timestamps are unchanged. |
| `src/pages/TrackRecord.jsx` | REPLAY does not establish successful inference or live performance; recorded score-percentile/outcome definitions and missing observations. | Localized caution, labels and numeric table alternatives. |

The package manifest, package lock, CI workflow, `reviewRegressions.test.js`, provenance
helpers, trace pairing implementation, contracts and shared fixtures remain unchanged.
Existing main regression tests are retained byte-for-byte. The build warning threshold
remains the main value of 1000 kB; no threshold was raised to satisfy the budget.

## Twelve repairs

| Fix | Implementation and verification path |
| --- | --- |
| 01 — RTL signed values | Canonical/BDI boundaries for sector means, shortlists, measurements and identifiers; browser geometry and source-data parity checks. |
| 02 — regime severity | Badge tone uses the raw regime enum; labels alone are translated. Tests cover all three pool states and all locales. |
| 03 — table names | Add a localized caption only to tables lacking one; preserve captions and header scopes. Expanded seven-route matrix and axe inspect actual tables. |
| 04 — original Agent suite | Migrated global selector/preference and asynchronous catalog waits; preserved historical assertions. |
| 05 — visible narration | Localized Listen entry by the guide heading focuses the existing controls without starting speech. |
| 06 — speech enumeration | Initial/late/empty/eventless voice lists, bounded refresh, strict regional matching, engine pause recovery and cancellation. Real device availability remains a separate limitation. |
| 07 — filter race | Factor Lab commits query updates synchronously; rapid pool/status tests retain both canonical parameters. |
| 08 — reflow | Shrinkable wrapping candidate actions prevent enlarged pt-BR text from widening the page. No required content is hidden to obtain a pass. |
| 09 — abstention reasons | Keep a recorded summary; distinguish unavailable failed-check details from a missing reason. Main regression tests remain unchanged. |
| 10 — terminology | Preserve canonical enums; apply the reviewed Japanese/Korean elevated-risk labels, German abstention, Czech count wording and Arabic hit-rate wording. Native financial editorial review remains pending. |
| 11 — day inflection | Locale-aware unit forms preserve numeric values. Tests include 0/1/2/4/5/21/100 and fractions, including Czech `den/dny/dní/dne`; actual one-day tooltips are checked. |
| 12 — rich badge spacing | An inline wrapper prevents rich sentence fragments becoming separate flex items. Text and visual checks preserve spaces. |

Additional local fault injection found and repaired a retry notice hidden by the fixed
sidebar and a browser module-cache failure that prevented successful retry. Real axe checks
also identified English/Korean risk-link visible-name mismatches; the accessible name now
contains the exact visible label plus the canonical symbol. Screenshot review also replaced a
bidi-sensitive Arabic `0/5` reconciliation fraction with explicit points-out-of-five wording;
the underlying values remain unchanged.

## Loading and caching architecture

English application/guide strings and the small native-name locale registry are eager.
Each other application catalog has its own dynamic import; guide catalogs have a separate
loader and are requested only by Ticker Detail. The production manifest and actual browser
requests verify this, rather than relying on the appearance of `import()` in source.

A validated success cache and in-flight promise map deduplicate requests. Only complete
catalogs activate. A generation counter prevents a slower earlier selection or failure from
replacing the latest choice. Cold saved preferences gate the primary UI behind a neutral,
accessible loading state and an available language selector. Normal later switches retain
the current mounted route and state until the requested language is ready.

Failures explicitly activate English and persist that fallback. Retry remembers the failed
language. Because browsers can cache a rejected ESM fetch for a document, explicit retries
fetch the same versioned, same-origin JSON asset with a bounded 10-second timeout and the
same full-catalog validation. These fallback assets are not downloaded in successful normal
navigation. This avoids a document reload and preserves URL filters, pagination and view state.
No translation service, external TTS provider or new application dependency is introduced.

The guide route boundary prevents English financial caveats flashing before the selected
guide translation loads. Source prose stays verbatim, marked as original content, outside
localized-language inheritance. The existing B1 numeric/date policy is retained; locale
switching never recalculates financial values or turns research tiers into orders.

## Reproduction and final evidence

Browser scripts use an existing Playwright runtime and system Chromium. The repository's
normal npm dependencies remain pinned to main. Optional Lighthouse/axe tools are installed
outside the application dependency graph and supplied through environment paths.

Run the existing tests/contracts/i18n checker/build/audit and all applicable browser suites.
V2 adds `v2-loader-acceptance.cjs`, `v2-data-acceptance.cjs`,
`v2-mainline-acceptance.cjs` and `v2-accessibility-acceptance.cjs`.
The full locale script covers 462 standard cases and separate failure/speech states.

Final compact QA evidence is generated after the implementation SHA is published, on this
same branch. It identifies the tested implementation separately from any later documentation
HEAD and uses committed repository-relative evidence paths. Historical `cd2b610` results
are not substituted for V2 results. Native editorial, NVDA/VoiceOver, audible speech and
Windows Edge voice-inventory limitations must remain explicit. No automated result grants
merge or release approval.
