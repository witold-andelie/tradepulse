# Submission status — 27 October 2026

## Current delivered scope

**Crypto is the submitted working demonstration.** US and European equities are future
upgrades with experimental code and offline baselines; their live end-to-end acceptance
is not complete. Do not present either as passed or manufacture a directional stance.

| Area | Current evidence / boundary |
| --- | --- |
| Accepted Crypto | Run 2026-10-23-87de33aa; 38 records, all NO_CALL; three explained observations; original input/output and 49-event trace published from commit 194033a |
| Sponsors | Actual Zetaris queries and Meterless engine operations; GLM inference for this accepted run; separate earlier Nightshift provider calls, whose full Crypto attempt failed |
| Local API/UI | Lead-reported real Crypto checks on API port 8001 and latest-main frontend; review server now packages the same saved case for credential-free inspection |
| Frontend | Yin Hu's baseline and PR #8 V2 are preserved; 130 frontend tests and the recorded browser/contrast checks passed |
| Offline reproducibility | Committed real snapshot, original three input/output/trace examples, schema/hash checks and independent offline computations |
| Media | A local 130-second MP4 exists. Narration is in local video/NARRATION_EN.md; both are excluded from Git. Upload and slide completion are not inferred from file existence |
| US/EU | Not live-accepted; tracked as future upgrades, not current demo pages |
| Remaining human acceptance | Native guide reading is not completed; audio/cross-browser voice and eleven-language editorial are explicitly deferred |

## Current judge entry points

- [README](../README.md): purpose, quick start, scope, team and roadmap.
- [Running guide](RUNNING.md): saved case, offline recomputation and separate optional sponsor checkout.
- [Crypto evidence manifest](review/crypto-evidence.json): original byte hashes and source commit.
- [Sponsor boundaries](sponsors.md), [team](TEAM.md), [component attribution](PRE_EXISTING_COMPONENTS.md).
- [Limitations](honest-limitations.md) and [submission checklist](submission/README.md).

## Ownership and takeover

Wentao Ma leads core/integration/release. Mengya Feng supplied ingestion groundwork;
Yin Hu supplied frontend/accessibility/localization; Hao Tan supplied quantitative work,
235 property tests and B7-B9 review fixes. Ojas Vairagkar was initially assigned sponsor
deployment/integration but supplied no project code, working service or reviewable deliverable.
The lead completed all TradePulse-specific sponsor work and the demonstrated Crypto service path.
See TEAM.md; original contributor commits remain intact.

## Preserved implementation history

Frontend integration aaf3b5f preserves the original B1-B10 work; research-guide merge 9a0d76d
and localization PR #8 retain that history. PR #3 and #4 preserve quantitative/property/UI
review contributions; PR #5 preserves ingestion groundwork. Detailed dated measurements
remain in docs/validation/, web/qa-reports/ and the original module acceptance documents.
Older AWS/NIM-only and guide-only instructions are historical where they conflict with this
submission scope; they are not new assignments.

## Branch boundary

The lead paused merging the sponsor/US work. This judge release adds documentation, original
Crypto evidence and a small read-only inspection entry point to main. It does not merge the
pending US identity repair or pretend that its tests establish live US acceptance. Complete
sponsor source is available in the integration checkout referenced by RUNNING.md.
