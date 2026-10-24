# Project status — 24 October 2026

This is the current implementation and ownership index. Detailed task catalogues remain
requirements, not evidence of completed deployment or historical market performance.
The preserved frontend integration is merge commit `aaf3b5f`, with parents `55ddedd` and
Huyin's `f9c8e0b`. Her B1, B2–B10 and accessibility commits remain in its ancestry.
Tanhao's B7–B9 fixes and C9 properties were preserved in PR #4 (`f5652c9`) and PR #3
(`d119be1`). Member A's ingestion branch was preserved in PR #5 (`af229b4`) as an
implementation integration, with follow-up fixes and remaining data acceptance taken over
by the lead. These merges retain the original contributor commits.

## Current implementation

| Area | Implemented | Remaining |
|---|---|---|
| Core / lead | Research gates, ranking, regime, walk-forward, grounded extraction, LangGraph explanation/verifier, reports, API and traces | Engine wiring, real artifact/service acceptance and delivery materials |
| A / ingest, lead follow-up | Provider fixes, local-evidence documentation, lake/sample code, current-bar coverage auditing and offline regressions | Lead: collect real artifacts/crypto CSV from sources, independently accept data and source policies, publish sample and arrange S3 upload with D |
| B / Huyin | Six business pages, Discover, Simple/Pro, filtering, evidence drill-down, responsive design and accessibility interactions | Visual/interaction review, concrete findings and remaining manual acceptance |
| C / Tanhao | C1–C7 math, 235 C9 property cases, B7–B9 review fixes and recorded fixture accessibility acceptance | Regression against delivered real API outputs |
| D / integrations | SQL templates, DuckDB adapter, registration runner, hosted NIM record/replay client and Python engines client | Zetaris deployment/registration/live client/parity, recorded cassette and TypeScript engines sidecar |
| Docker | Core and web definitions, nginx API proxy and memory limits | Runtime validation after sample artifacts arrive; engines service remains commented out |

Do not ask Huyin or Tanhao to recreate pages already supplied by the integration.
Existing page adapters preserve the agreed `*Page` prop interfaces; shared hook paths use
one provider and all charts delegate to the shared figure/modular renderer.

## Artifact and service availability

The publication checkout has no `data/lake/`, `data/sample/`, saved `runs/` or real `logs/`.
It also lacks `integrations/ACCESS.md`, a deployed-service evidence record, engines server
source/vendor files, a committed LLM cassette and live parity/model smoke-test evidence.
PR #5's sample hashes, coverage figures and SEC comparisons describe the author's excluded
local artifacts. They do not deliver those artifacts or independently establish acceptance.
The lead follow-up fixes stale coverage-report acceptance, missing crypto article lookup and
sample document selection without changing schemas or original tests. The 35 reported exhibit
exceptions and SEC timestamp-policy synchronization still require explicit lead disposition.
No existing real artifact delivery is available; the lead is preparing fresh collection for
2026-10-23. The local contact User-Agent settings are not yet configured, so provider requests
have not started. The ignored .env template is ready for local completion.

The standalone web preview works with synthetic fixtures. Full SAMPLE_MODE is not yet an
accepted offline delivery. Docker's API-mode web build needs a saved backend output and will
show a visible API error when one is missing.

## Remaining sequence and owners

1. **Lead, taking over A's delivery:** collect the lake, curated crypto CSV and source reports
   from the providers for the fixed decision date. Independently validate them,
   publish the snapshot/decision date and arrange upload to D's private location. Existing
   coverage and point-in-time acceptance thresholds remain in force. Do not assign A more fixes.
2. **D:** finish Zetaris client/deployment/parity; agree the NIM models with the lead; record
   model answers for A's exact snapshot/date; implement and test the Meterless engines sidecar.
3. **Lead:** connect engines, verify hosted access from Europe, and run offline SAMPLE_MODE
   with networking disabled. Inspect actual reports, data provenance and JSONL traces.
4. **B and C / lead QA:** review the integrated pages against those real outputs and fix specific
   findings. B7–B9 fixture acceptance is recorded; other-page and real-output acceptance remains.
5. **Lead:** finalize sponsor evidence, honest limitations, three or more genuine sample
   input/output pairs, demo script, slides, video and submission.

Team planning dates remain: B's hard limit 25 October 23:59 UTC; D's hard limit
26 October 03:59 UTC (25 October 23:59 US Eastern); submission 27 October 23:45 UTC.
These are the recorded project deadlines, not a live check of organizer announcements.

## Verified checks

- Full offline Python suite after PRs #3–#5, ingestion fixes and collection readiness: **576 passed, 8 skipped**,
  with 19 existing BeautifulSoup/lxml deprecation warnings.
  The skips are seven lake-table cases and the sample snapshot case; absent real artifacts
  still block A's acceptance.
- Eleven new ingestion regression cases passed; eight failed against the merged implementation
  before the fixes, covering stale/missing coverage evidence, absent crypto article mappings
  and multi-share-class sample selection. No original test was edited.
- Nine further collection-readiness cases cover absent Yahoo candidates and source-date
  validation before sample publication. Ingest alone: **101 passed, 8 skipped**.
- Changed ingestion files and new regression files pass Ruff **0.17.2** with `--no-cache`.
  Full-repository Ruff 0.17.2 acceptance is not claimed: the previously identified unused
  `noqa` at `quant/tests/test_evaluation.py:87` remains a separate maintenance item.
- Frontend, last checked for PR #4: **68 tests passed** across 12 files; fixtures and all 19 trace lines validate;
  production build passes, largest chunk **627.84 kB**.
- Huyin's unchanged original browser suite: **17/17 groups passed**.
- Her unchanged redesign/accessibility journeys: **18/18 groups passed**, including 320 CSS
  pixel reflow and 200% text enlargement.
- Focused Chromium check: **14 route/view combinations**, **5,414 visible text nodes**,
  minimum measured contrast **5.66:1**, no reported contrast failures, unnamed inspected
  controls or inspected targets below 24px.
- B7–B9 fixture manual acceptance is recorded in
  [PR #4's comment](https://github.com/witold-andelie/tradepulse/pull/4#issuecomment-6388234439):
  Lighthouse 100 on each page, axe zero critical/serious, keyboard, 200% zoom, 320px reflow,
  NVDA 2026.2 and native reduced motion. The lead independently checked all eight chart tables
  at 320px, indicator row headers, emulated reduced motion and a clean production console.

Original browser/contrast checks above belong to the Huyin integration; the PR #4 checks are
identified separately. Python and changed-file Ruff were rerun for the lead ingestion follow-up.
Local browser evidence is outside Git under
`D:/AI_Models/hackson/.work/huyin-integration/`. No automated result certifies WCAG conformance,
proves live services work, or establishes predictive investment performance.

## Documentation map

- [Frontend tasks](../web/TASK.md), [integration details](../web/INTEGRATION.md) and
  [acceptance](../web/ACCEPTANCE.md)
- [Detailed current instructions for Huyin](../web/HUYIN_NEXT_STEPS.md)
- [Ingest](../ingest/TASK.md), [quant/C review](../quant/TASK.md),
  [sponsor integration tasks](../integrations/TASK.md)
- [Core implementation](../tradepulse/README.md), [architecture](architecture/README.md),
  [decisions](architecture/decisions.md)
- [Honest limitations](honest-limitations.md) and [sponsor evidence status](sponsors.md)
