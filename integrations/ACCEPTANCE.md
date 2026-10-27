# Sponsor acceptance: current submission

Updated 27 October 2026. This checklist follows the lead's latest requirements.
The earlier AWS-only/NIM-only assignment is historical context in TASK.md.
Check items only after observing the actual result.

## Code and local engine acceptance

- [x] Offline integration tests pass; original given test assertions are preserved.
- [x] Official unchanged H-MEM and World Model references include LICENSE, commit NOTICE
  and upstream Git-hash verification for all 23 vendored files.
- [x] Official conformance: H-MEM 13/13 and World Model 8/8.
- [x] Eight service tests and TypeScript checks pass; dependency audit has zero findings.
- [x] The built Docker image starts and passes health checks with a persistent named volume.
- [x] The real core pipeline calls EnginesClient over HTTP for three sample pools and
  persists/retrieves output. Restart preserved the first run's 616 records.
- [x] Requests use bounds/timeouts and the original GraphEdge/ExtractedEvent schemas.
- [x] Wrong/missing tokens are rejected when ENGINES_TOKEN is configured.
- [x] Historical queries exclude future records and preserve earlier eligible edge versions.
- [x] Nightshift is first for every role when configured, including skeptic.

See [engine measurements](engines/VALIDATION.md) for scope. The core/container run used
an empty model replay cassette and empty World Model snapshots. It establishes H-MEM
service use, not Nightshift inference or non-empty real event/graph ingestion.

Run the offline checks from the repository root:

    py -3 -m pytest integrations -q
    py -3 -m ruff check integrations --no-cache

Then in integrations/engines:

    npm ci
    npm test
    npm run check
    npm run conformance
    npm audit

## Actual services on the Mac

- [x] Local Zetaris Docker runs and the official helper executes SELECT 1.
- [x] Seven registered lake tables match the committed sample manifest row counts.
- [x] Official helper returns crypto 38, eu_equity 55 and us_equity 523 members.
- [ ] TradePulse ZetarisClient and ZetarisAdapter live smoke succeed on the Mac.
- [ ] Every template matches DuckDB rows_sha256 on the frozen sample.
- [x] The lead reports Nightshift M1-M4 Edition responding through its Bearer-token API.
- [x] A real token produces a text response through TradePulse's smoke check (lead-reported).
- [ ] Wrong token gets 401/403 and the configured model matches the advertised runtime catalog.
- [ ] The engine image builds and runs on the Mac's actual architecture.

Use [MAC_LIVE_SETUP.md](MAC_LIVE_SETUP.md). Never request, print or include raw credentials
in acceptance evidence.

## End-to-end submission evidence

- [ ] integrations.live_acceptance completes all three pool cases with status=ok and
  submission_complete=true. A selected-pool run cannot satisfy the full submission check.
- [ ] Every run queries Zetaris and receives live Nightshift analyst and skeptic answers.
- [ ] Original traces show successful engine snapshot, recall and recommendation writes.
- [ ] Three inputs, outputs, original traces and the computed README table are reviewed.
- [ ] Every result comes from computation; tiers and verification gates are preserved.
- [ ] Model text/cassettes pass privacy review before publication.
- [ ] README and sponsor write-up link actual artifacts and disclose remaining limits.
- [ ] If offline model replay is claimed, exact prompts/cassette pass with networking blocked.

AWS/S3 shared hosting, outside-universe EDGAR, automatic settlement scheduling, production
multi-writer persistence and separate model-family routing are not certified by these tests.
