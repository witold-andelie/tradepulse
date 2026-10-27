# Meterless core wiring preparation

Current submission note, 27 October: the lead completed real Meterless snapshot/recall/remember in the accepted Crypto run. Main provides saved-result review; full sidecar source is in the separate integration checkout linked from RUNNING.md. The dated interface/assignment text below remains historical where it says D must still deliver. US/EU live completion remains future work.

This is core integration code against the existing `integrations/engines/API.md`, not delivery
of the official engines or acceptance of D's cloud service. No API/table schema or original
test has been changed.

## Activation and failure behavior

- Engine HTTP use is explicit: live mode plus `ENGINES_ENABLED=true` and `ENGINES_URL`.
  Shared endpoints require HTTPS; local loopback/the Compose `engines` hostname may use HTTP.
  The existing client reads `ENGINES_TOKEN` privately and has a ten-second request timeout.
- SAMPLE_MODE never constructs an environment-selected engine HTTP client. Its offline
  behavior is unchanged. Tests may explicitly inject an in-process `EnginesPort` fake;
  those tests are identified as SYNTHETIC and are not sponsor evidence.
- With engines disabled the RunOutput warning explicitly states that no World Model/H-MEM
  persistence or memory context was used. A configured engine failure stops the run with a
  sanitized `EngineIntegrationError`; there is no silent successful-persistence fallback.
- Trace entries describe actual port calls and failures. Remote exception text, records,
  credentials and endpoint values are not written to the trace.

## Pipeline flow

1. Calculate the existing seed-edge validation and deterministic event grounding.
2. Validate all outgoing events/edges against unchanged contracts and the decision date.
   Commit grounded events and only validated edges to the World Model.
3. Request the as-of snapshot. Check the response date, schemas, unique IDs and availability
   times, and require acknowledged writes to appear. Use these validated snapshot events and
   edges as the signal-panel inputs. The engine does not bypass research gates.
4. Recall dated H-MEM records for focus instruments. Reject future, wrong-symbol, duplicate or
   oversized responses. Only historical record counts enter the analyst's task, explicitly
   labelled unverified context. Raw memory text cannot become instructions or claim evidence.
   The existing query-based verifier remains authoritative.
5. After the contract-valid report is assembled, remember its original recommendation values,
   execution lag, data mode, run identity and verified evidence IDs. Per-record IDs are stable
   for the same run/pool/symbol/date/horizon. Failure to remember prevents a successful run return.

Work limits: at most 5,000 events or edges per world list, 1,000 recommendation records,
100 focus recalls and ten records per recall. Additional focus items still receive their
ordinary explanation without memory context; the trace records that recall limit.
There are no additional automatic retries. A partial operation can already have reached the
server before a later failure; client trace status is not a transaction rollback guarantee.

## Prepared feedback mapping

`EngineBridge.feedback(record, prices, benchmark)` calculates one explicitly selected pending
record's observed excess return using its stored execution lag and horizon. It uses actual
sorted session dates, requires entry/exit/benchmark observations no later than the run's as-of
date, and defers incomplete or immature outcomes without inventing zero returns. Neutral/
NO_CALL records retain `hit=null`; directional tiers use `quant.settlement.hit`.

The function sends the existing `/hmem/feedback` body and checks its acknowledgement. It is
caller-driven: do not indiscriminately settle every recalled record on every run. The current
API does not define a pending/settled marker, complete pending enumeration or feedback
idempotency. D and the lead must agree and verify those semantics before enabling an automatic
settlement loop. The current HTTP contract has not been silently extended.

The `/hmem/conflicts` endpoint similarly has no `as_of` argument or declared dated response
structure. It is therefore not fed into a historical analysis. D's conflict conformance tests
and a point-in-time interpretation are still required. The existing Python client remains
available for explicit real-service conflict inspection.

RunOutput TrackRecord remains the original deterministic walk-forward simulation. This
preparation does not relabel it as persisted H-MEM performance.

## What D still needs to deliver

- Official unmodified World Model/H-MEM engines, LICENSE/NOTICE, passing conformance and
  persistence tests, plus the agreed HTTP sidecar.
- Real HTTPS access and safe smoke instructions; validate core calls and snapshots from Europe.
- Confirm write acknowledgements/read-after-write behavior, pending/settled selection,
  duplicate-feedback behavior and dated conflict handling with actual engine results.
- Genuine service/recording acceptance before any sponsor-use claim. No host deployment,
  real engine execution or successful NIM inference is established by the injected-port tests.
