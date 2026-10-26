# Project status — 26 October 2026

This is the current implementation and ownership index. Detailed task catalogues remain
requirements, not evidence of completed deployment or historical market performance.
The preserved frontend integration is merge commit `aaf3b5f`, with parents `55ddedd` and
Huyin's `f9c8e0b`. Her B1, B2–B10 and accessibility commits remain in its ancestry.
Tanhao's B7–B9 fixes and C9 properties were preserved in PR #4 (`f5652c9`) and PR #3
(`d119be1`). Member A's ingestion branch was preserved in PR #5 (`af229b4`) as an
implementation integration, with follow-up fixes and remaining data acceptance taken over
by the lead. These merges retain the original contributor commits.
Huyin's scoped multilingual research guide (`b64ef94`) is preserved in merge `9a0d76d`.
The lead approved that guide-only UI exception and took over the two follow-up review fixes.

## Current implementation

| Area | Implemented | Remaining |
|---|---|---|
| Core / lead | Research gates, ranking, regime, walk-forward, grounded extraction, LangGraph explanation/verifier, API/traces, sample launcher, three examples and optional World Model/H-MEM core wiring with offline port tests | Actual engine acceptance, pending/conflict semantics, complete model replay and final media |
| A / ingest, lead follow-up | Real seven-table lake/sample for 2026-10-23, crypto CSV/provenance, source checks, accepted source exceptions, offline execution and reproducible private full-lake package/verification | Actual S3 upload awaits D's destination/access; model recordings are D's separate dependency |
| B / Huyin | Six business pages, Discover, Simple/Pro, evidence drill-down, responsive/accessibility interactions, localized guide, independent Lighthouse/axe/native zoom and real-API journeys | New guide's actual NVDA/VoiceOver check, native-speaker editing and audible voice quality |
| C / Tanhao | C1–C7 math, 235 C9 property cases, B7–B9 fixes, fixture accessibility acceptance and real-API regressions completed by the lead | Recheck after D supplies fully explained real outputs |
| D / integrations | SQL templates, DuckDB adapter, registration runner, hosted NIM record/replay client and Python engines client | Zetaris deployment/registration/live client/parity, recorded cassette and TypeScript engines sidecar |
| Docker | Actual core/web builds, empty-volume startup, non-root core, health ordering, nginx proxy, memory limits and nine passing real-API browser groups | Engines service remains commented out; hosted sponsor acceptance |

Do not ask Huyin or Tanhao to recreate pages already supplied by the integration.
Existing page adapters preserve the agreed `*Page` prop interfaces; shared hook paths use
one provider and all charts delegate to the shared figure/modular renderer.

## Artifact and service availability

The real sample and crypto configuration were independently rebuilt from public sources for
2026-10-23. Seven table files occupy 15,341,745 bytes; the complete package remains below
25 MB. It includes source-index evidence, hashes, privacy normalization and offline checks.
See [real-data evidence](../ingest/REAL_DATA_EVIDENCE.md) and
[the sample manifest](../data/sample/manifest.json). The collector's full lake, caches, saved
run and genuine traces remain local/ignored. PR #5's older excluded sample is historical evidence.

Strict data audit: 31/32 checks pass. The remaining completeness check truthfully reports
35 missing exhibits; every source index was independently verified to have no permitted
candidate. The lead accepted these exceptions for a source-qualified release on 2026-10-25;
the strict completeness flag remains false. Source timestamp descriptions now match the
verified index-based UTC policy, while explicitly preserving the legacy synthetic helper and
disclosing the current date-only cutoff rather than claiming a market-close implementation.

A complete three-pool run finished with networking blocked and a contract-valid RunOutput:
616 NO_CALL records, 33 factor cards (20 MEASURED_ONLY, 13 INSUFFICIENT_DATA), and nine abstained
explanations because the matching model cassette is absent. No ACTIVE factor or model answer
was fabricated. Full explained replay and sponsor acceptance remain incomplete.

The checkout lacks `integrations/ACCESS.md`, deployed-service evidence, engines server/vendor
files, a committed LLM cassette and live parity/model smoke evidence. The standalone frontend
still defaults to synthetic fixtures. `serve.py` now generates a saved run on a fresh sample
checkout; the actual API-backed frontend and container stack are verified. Cloud upload is
pending D's private destination and access method. The verified local full-lake ZIP and A1–A9
closure matrix are in [A delivery](../ingest/DELIVERY.md); no upload has occurred.

D reports proceeding in AWS US East (Ohio), `us-east-2`, after unsuccessful EU and N. Virginia
attempts. Ohio is accepted as a documented region fallback; the reason for those failures,
service deployment and access from Europe are not independently verified yet. D must record
the actual region in `DEPLOY.md` and supply the HTTPS endpoints/smoke instructions in `ACCESS.md`.

## Remaining sequence and owners

1. **Lead, taking over A's delivery:** arrange upload to D's private location. Source exceptions
   were accepted for release on 2026-10-25. Preserve the delivered sample and hashes; do not
   replace measured gaps with invented rows or assign A more fixes.
2. **D:** finish Zetaris client/deployment/parity; agree the NIM models with the lead; record
   model answers for the delivered snapshot/date and redacted text hashes; implement and test
   the Meterless engines sidecar. The earlier excluded sample is not cassette-compatible.
3. **Lead:** validate the prepared core bridge against actual engines, verify access from Europe, and run offline SAMPLE_MODE
   with networking disabled after recording models. Offline data loading, pipeline execution,
   API contract and abstention behavior have already passed; model replay is still pending.
   Automatic H-MEM pending selection/idempotency and historical conflict handling require
   semantics not declared by the existing HTTP API; the bridge does not invent them.
4. **B and C / lead QA:** the current real-output regression is complete. Repeat it after D's
   cassette supplies genuinely explained outputs. The new guide still needs actual NVDA/VoiceOver,
   native-speaker editing and audible voice checks; automated tools do not certify those.
5. **Lead:** three genuine input/output/trace pairs and the demo/slide content are prepared.
   Finalize cloud-service scenes, sponsor evidence, the rendered deck/video and submission.
   The primary track is confirmed as **Track 2 — The Agent That Can Explain Why**. Confirm the
   roster and pre-existing component declarations before submission. Cursor is not part of the
   current submission requirements or project claims.

Completed maintenance, 25 October: existing libraries were upgraded and the official npm audit
fell from 15 findings to zero. Ruff 0.17.2 and 0.15.20 pass the same explicit rule policy;
all original tests are unchanged. SEC timestamp descriptions were synchronized with actual
index-based persistence and the documented UTC date cutoff. See [maintenance evidence](validation/maintenance-2026-10-25/README.md).

Team planning dates remain: B's hard limit 25 October 23:59 UTC; D's hard limit
26 October 03:59 UTC (25 October 23:59 US Eastern); submission 27 October 23:45 UTC.
These are the recorded project deadlines, not a live check of organizer announcements.

## Verified checks

- CI/core-wiring preparation: **642 Python tests** pass, including **33 new SYNTHETIC
  injected-port cases**. No given test or assertion changed. Ruff/actionlint, 89 frontend
  tests, contracts and build pass. Fresh real-sample computation still produces 616 records,
  33 cards and nine actual abstentions, with zero attempted network connections and cached
  reuse. This is offline/interface acceptance, not official Meterless execution.

- Full offline Python suite on the collector after fresh-start completion, with real lake and delivered sample: **609 passed, none skipped**,
  with 19 existing BeautifulSoup/lxml deprecation warnings.
  All seven lake cases and the sample case execute. Passing these tests does not override the
  separate strict completeness failure for the 35 verified source exceptions.
  At the initial real-sample release, a clean export without credentials/caches passed **588 tests with 7 expected
  production-lake skips** and zero attempted external network connections. The sample test
  passed. Its seven production-lake cases require local collection/private handoff.
- Eleven new ingestion regression cases passed; eight failed against the merged implementation
  before the fixes, covering stale/missing coverage evidence, absent crypto article mappings
  and multi-share-class sample selection. No original test was edited.
- Nine collection-readiness cases cover absent Yahoo candidates and source-date validation.
  Public Yahoo transport, privacy normalization and blocked-news reporting have new offline
  regressions. No given test assertion was changed.
- Full-project Ruff **0.17.2** and **0.15.20** pass with `--no-cache` under the explicit
  pre-0.16 project rules plus `RUF100`. The original quant test and its meaningful `E731`
  suppression remain unchanged. Four unused ingestion suppressions became plain comments.
- Frontend, last checked for PR #4: **68 tests passed** across 12 files; fixtures and all 19 trace lines validate;
  production build passes, largest chunk **627.84 kB**.
- Research-guide follow-up on main: **84 tests passed across 14 files**, contracts and build
  passed, largest chunk still **627.84 kB**. Four new regression cases caught the summary and
  paused-engine issues before the fixes; existing tests were unchanged. The original 15-group
  guide browser suite and additional summary/pause-preserving browser regressions passed.
  See [guide acceptance scope](../web/AGENT_ACCESSIBILITY_DEMO.md); its native/manual checks
  remain separate from the earlier B7–B9 fixture acceptance.
- Fresh-start/provenance follow-up: **609 Python tests** and **89 frontend tests across 15 files**
  pass. Contracts and build pass; largest chunk remains **627.84 kB**. All original assertions
  are preserved. The UI now distinguishes REPLAY mode from actual model-answer availability.
- Security/tool maintenance: official registry audit **15 → 0 findings**; **609 Python** and
  **89 frontend** cases pass, contracts validate, and the largest production chunk is now
  **672.22 kB**. Original browser suites pass **17/17, 18/18 and 15/15**; real API/container
  checks pass **9/9**. Six chart families were visually inspected; timeline offset bars remain
  transparent instead of acquiring an accessibility decal. The SEC description-only change
  preserves every column/schema property and all seven frozen sample table hashes.
- First-start computation with an empty store and networking blocked passed in **32.26 seconds**;
  cached startup reused the same run in **0.12 seconds**, with zero network attempts.
  Three separately computed pool examples include original traces and verified hashes.
- Actual local API browser acceptance passed **9/9 groups**: nine routes in Simple/Pro at
  1440/320 px, data-derived counts, filters, keyboard detail navigation, factor/trace states
  and an intentional 503 without fixture fallback. The same nine groups passed through the
  freshly built core/web container stack after correcting the REPLAY disclosure. Normal
  browser journeys had no console errors or fixture chunk requests. See [runtime evidence](validation/README.md).
- Independent Ticker Detail acceptance: Lighthouse 13.5.0 scores **100 desktop / 100 at 320 px**;
  **28 axe-core 4.14.0 cases have zero violations** after fixing the brand name and Run context
  landmark; **18 native Chrome zoom cases passed**, including 200% at 320 CSS px. Original
  reports, residual contrast review and scope are [published with the web app](../web/ACCESSIBILITY_ACCEPTANCE.md).
  NVDA/VoiceOver on the new guide, native-speaker editing and audible voice quality remain pending.
  After that shell correction, unchanged guide/original/redesign browser suites passed
  **15/15, 17/17 and 18/18 groups**, respectively, on the corrected production build.
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
- Real sample DuckDB queries and a complete three-pool pipeline run passed with network
  connections blocked and zero attempted connections. These are data/contract/load checks,
  not claims of successful model inference or predictive performance.
- GDELT probes returned 345 daily observations each for NVDA, AMD and COHR over the requested
  year, with 20 missing dates per series. No missing dates were filled and no news factor was added.

Original browser/contrast checks above belong to the Huyin integration; the PR #4 checks are
identified separately. Python and changed-file Ruff were rerun for the real-data delivery.
Local browser evidence is outside Git under
`D:/AI_Models/hackson/.work/huyin-integration/`. No automated result certifies WCAG conformance,
proves live services work, or establishes predictive investment performance.

## Documentation map

- [Frontend tasks](../web/TASK.md), [integration details](../web/INTEGRATION.md) and
  [acceptance](../web/ACCEPTANCE.md)
- [Detailed current instructions for Huyin](../web/HUYIN_NEXT_STEPS.md)
- [Ingest](../ingest/TASK.md), [quant/C review](../quant/TASK.md),
  [sponsor integration tasks](../integrations/TASK.md)
- [Real collection evidence](../ingest/REAL_DATA_EVIDENCE.md),
  [portable sample](../data/sample/README.md) and [sample hashes](../data/sample/manifest.json)
- [Core implementation](../tradepulse/README.md), [architecture](architecture/README.md),
  [decisions](architecture/decisions.md)
- [Honest limitations](honest-limitations.md) and [sponsor evidence status](sponsors.md)
- [Clean sample startup and API](RUNNING.md), [runtime evidence](validation/README.md),
  [computed examples](../examples/README.md) and [submission preparation](submission/README.md)
- [Credential-free CI](CI.md) and [Meterless wiring/remaining semantics](METERLESS_WIRING.md)
