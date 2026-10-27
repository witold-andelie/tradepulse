# Sponsor acceptance: current submission

Updated 27 October 2026. This checklist follows the lead's latest requirements.
The earlier AWS-only/NIM-only assignment is historical context in TASK.md.
Check items only after observing the actual result.

Current lead direction: hosted GLM for normal inference, live Zetaris and real Meterless
Engines. Nightshift evidence is retained separately and local-model diagnosis is stopped.
Follow [HOSTED_ACCEPTANCE.md](HOSTED_ACCEPTANCE.md). The earlier all-Nightshift profile is
still available, but does not block the explicitly selected GLM profile. This is engineering
acceptance, not a claim that submission media and every event-rule check are complete.

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
- [x] Explicit GLM routing bypasses local inference; the original auto/Nightshift route is preserved.

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
- [x] The lead reports TradePulse ZetarisClient and ZetarisAdapter live smoke on the Mac.
- [x] The lead reports real 12/12 template parity, with full rows and matching hashes.
- [x] The lead reports Nightshift M1-M4 Edition responding through its Bearer-token API.
- [x] A real token produces a text response through TradePulse's smoke check (lead-reported).
- [ ] Wrong token gets 401/403 and the configured model matches the advertised runtime catalog.
- [x] The lead reports Mac engine health and successful snapshot, recall and remember calls.

Use [MAC_LIVE_SETUP.md](MAC_LIVE_SETUP.md). Never request, print or include raw credentials
in acceptance evidence.
The initial 6a2f71d run matched 6/12. The lead reports the corrected 6966b0c run matched
12/12; the Mac artifact is runs/zetaris-parity-fixed-1.json. See
[the parity diagnosis](zetaris/PARITY_DIAGNOSIS.md). These Mac observations have not been
independently repeated on Windows.

The subsequent Crypto run failed at validate-case. Of 11 returned model replies, three
passed schema validation; all three explanations abstained. A further provider attempt
failed without a response. Engine operations succeeded, but this does not pass the case.
See [Nightshift diagnosis](meterless/STRUCTURED_DIAGNOSIS.md) before another full run.
The schema-format probe returned HTTP 400 without a model reply. Its exact rejection
cause is unknown. The json_object control also returned HTTP 400 naming response_format.
Prompt mode returned
invalid JSON with a normal stop after 37 output tokens. All probes remain failed. The next
step was the read-only model/resource inventory, now lead-reported complete. The installed
Nightshift code rejects structured formats for webllm providers. The next controlled trial
replaces the resident Llama 1B with Qwen2.5 3B q4f16, using prompt mode and one analyst request.
The lead now reports Qwen downloaded and ready as the sole resident model, but its one prompt
probe timed out after 180,153 ms with no reply. Model and Crypto acceptance remain incomplete.
The lead then found its runtime completion after 267,437 ms, retaining a separate original
export. The lane is idle, but the narrative includes an unsupported causal attribution.
Those original artifacts are retained. Further local-model diagnosis is stopped by the lead;
the next step is the hosted product acceptance command.
Bounded request/queue timeout overrides are implemented; defaults remain 180 seconds.
See the diagnosis's current step.

## End-to-end submission evidence

- [ ] integrations.live_acceptance completes all three pool cases with status=ok and
  submission_complete=true. A selected-pool run cannot satisfy the full submission check.
- [ ] Every run queries Zetaris and receives live analyst/skeptic answers from the declared provider.
- [ ] Original traces show successful engine snapshot, recall and recommendation writes.
- [ ] Three inputs, outputs, original traces and the computed README table are reviewed.
- [ ] Every result comes from computation; tiers and verification gates are preserved.
- [ ] Model text/cassettes pass privacy review before publication.
- [ ] README and sponsor write-up link actual artifacts and disclose remaining limits.
- [ ] If offline model replay is claimed, exact prompts/cassette pass with networking blocked.

AWS/S3 shared hosting, outside-universe EDGAR, automatic settlement scheduling, production
multi-writer persistence and separate model-family routing are not certified by these tests.
