# Project status — 24 October 2026

This is the current implementation and ownership index. Detailed task catalogues remain
requirements, not evidence of completed deployment or historical market performance.
The preserved frontend integration is merge commit `aaf3b5f`, with parents `55ddedd` and
Huyin's `f9c8e0b`. Her B1, B2–B10 and accessibility commits remain in its ancestry.

## Current implementation

| Area | Implemented | Remaining |
|---|---|---|
| Core / lead | Research gates, ranking, regime, walk-forward, grounded extraction, LangGraph explanation/verifier, reports, API and traces | Engine wiring, real artifact/service acceptance and delivery materials |
| A / ingest | Acquisition, parsing, validation, lake/sample code and offline tests | Live data, quality evidence, crypto mappings, EDGAR timezone verification, sample snapshot and S3 upload |
| B / Huyin | Six business pages, Discover, Simple/Pro, filtering, evidence drill-down, responsive design and accessibility interactions | Visual/interaction review, concrete findings and remaining manual acceptance |
| C / Tanhao | C1–C7 math library | C9 property tests and review/extension of Huyin's existing B7–B9 pages |
| D / integrations | SQL templates, DuckDB adapter, registration runner, hosted NIM record/replay client and Python engines client | Zetaris deployment/registration/live client/parity, recorded cassette and TypeScript engines sidecar |
| Docker | Core and web definitions, nginx API proxy and memory limits | Runtime validation after sample artifacts arrive; engines service remains commented out |

Do not ask Huyin or Tanhao to recreate pages already supplied by the integration.
Existing page adapters preserve the agreed `*Page` prop interfaces; shared hook paths use
one provider and all charts delegate to the shared figure/modular renderer.

## Artifact and service availability

The publication checkout has no `data/lake/`, `data/sample/`, saved `runs/` or real `logs/`.
It also lacks `integrations/ACCESS.md`, a deployed-service evidence record, engines server
source/vendor files, a committed LLM cassette and live parity/model smoke-test evidence.

The standalone web preview works with synthetic fixtures. Full SAMPLE_MODE is not yet an
accepted offline delivery. Docker's API-mode web build needs a saved backend output and will
show a visible API error when one is missing.

## Remaining sequence and owners

1. **A:** build and validate the lake; publish the snapshot and its decision date; upload to D's
   private S3 location. Meet the existing coverage and point-in-time acceptance thresholds.
2. **D:** finish Zetaris client/deployment/parity; agree the NIM models with the lead; record
   model answers for A's exact snapshot/date; implement and test the Meterless engines sidecar.
3. **Lead:** connect engines, verify hosted access from Europe, and run offline SAMPLE_MODE
   with networking disabled. Inspect actual reports, data provenance and JSONL traces.
4. **B and C:** review the existing integrated pages against those real outputs; fix specific
   findings and finish Lighthouse, axe, native screen-reader and native zoom acceptance.
5. **Lead:** finalize sponsor evidence, honest limitations, three or more genuine sample
   input/output pairs, demo script, slides, video and submission.

Team planning dates remain: B's hard limit 25 October 23:59 UTC; D's hard limit
26 October 03:59 UTC (25 October 23:59 US Eastern); submission 27 October 23:45 UTC.
These are the recorded project deadlines, not a live check of organizer announcements.

## Verified checks

- Full offline Python suite: **282 passed, 8 skipped**, with 9 dependency deprecation warnings.
  The skips are seven lake-table cases and the sample snapshot case; absent real artifacts
  still block A's acceptance.
- Ruff: `ingest quant integrations tradepulse run.py scripts` passed with `--no-cache`.
- Frontend: **56 tests passed** across 10 files; fixtures and all 19 trace lines validate;
  production build passes, largest chunk **627.84 kB**.
- Huyin's unchanged original browser suite: **17/17 groups passed**.
- Her unchanged redesign/accessibility journeys: **18/18 groups passed**, including 320 CSS
  pixel reflow and 200% text enlargement.
- Focused Chromium check: **14 route/view combinations**, **5,414 visible text nodes**,
  minimum measured contrast **5.66:1**, no reported contrast failures, unnamed inspected
  controls or inspected targets below 24px.

Frontend checks were executed for the integration source. Python/ruff were rerun for this
publication. Local browser evidence is outside Git under
`D:/AI_Models/hackson/.work/huyin-integration/`. No automated result certifies WCAG conformance,
proves live services work, or establishes predictive investment performance.

## Documentation map

- [Frontend tasks](../web/TASK.md), [integration details](../web/INTEGRATION.md) and
  [acceptance](../web/ACCEPTANCE.md)
- [Ingest](../ingest/TASK.md), [quant/C review](../quant/TASK.md),
  [sponsor integration tasks](../integrations/TASK.md)
- [Core implementation](../tradepulse/README.md), [architecture](architecture/README.md),
  [decisions](architecture/decisions.md)
- [Honest limitations](honest-limitations.md) and [sponsor evidence status](sponsors.md)
