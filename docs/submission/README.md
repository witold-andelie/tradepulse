# Submission preparation pack

Status: 25 October 2026. This is a review draft. A complete sponsor-integrated submission and
final uploaded video are not yet available. The recorded submission deadline is 27 October
2026, 23:45 UTC; the team still needs to confirm one primary track and its roster.

## Product description

TradePulse is a financial research workspace for examining separately ranked US equities,
European equities and crypto. Deterministic research gates distinguish description,
prediction and modeled net edge. The explanation workflow is designed to draft, challenge
and verify claims against dated source evidence. Users can inspect factor measurements,
limitations and traces in Simple or Pro View. Unsupported explanations abstain. The product
does not place, route or size orders.

## Prepared artifacts

- [Three-minute demo script](DEMO_SCRIPT.md), with exact workflow and a clearly identified
  cloud-services scene that must be replaced by genuine evidence after D delivers.
- [Eight-slide content and speaker notes](SLIDE_OUTLINE.md), covering users, solution,
  workflow, stack, sponsor roles, intended distinction, product visuals and future work.
- Four actual [product captures](assets/manifest.json), from a real container-backed run.
  Their capture tool uses no response interception; original UI values and abstentions remain.
- Three [computed input/output/trace examples](../../examples/README.md), plus
  [clean startup instructions](../RUNNING.md) and [runtime acceptance](../validation/README.md).
- [Sponsor implementation/evidence status](../sponsors.md) and
  [honest limitations](../honest-limitations.md).

## Evidence that may be stated now

The 2026-10-23 public-data snapshot contains 616 instruments across three pools. The complete
offline run yielded 33 factor cards, zero ACTIVE factors, 616 NO_CALL records and nine
abstained explanations. The missing model cassette is visible; REPLAY is not a claim of
successful NIM inference. Strict source acceptance remains 31/32, with 35 verified missing
exhibits accepted as explicit release exceptions. Gates and source rows were not altered.

The collector passed 609 Python tests and 89 frontend tests. Fresh offline startup, the
core/web Docker stack and nine actual API browser groups passed. Independent Ticker Detail
acceptance includes Lighthouse 100 desktop/mobile, 28 axe cases with zero violations and
18 native zoom cases. These scoped checks do not establish full WCAG conformance.

## Finalization checklist

| Item | Status and next action |
| --- | --- |
| Public source and setup | Repository is public; clean sample/API and container startup are documented and exercised |
| Example inputs, outputs and traces | Three real computed examples are committed; refresh after genuine model recording |
| Zetaris use | D must supply deployment, registration, live client, parity and access evidence |
| Meterless use | D must supply official engines, sidecar, persistence/conformance and hosted access; lead then wires the pipeline |
| NVIDIA use | Keep hosted NIM; agree model families and record genuine calls for this snapshot, then verify offline replay |
| Cursor use | Team must confirm actual development use and supply its description; do not infer it from generated code |
| Native guide acceptance | Actual NVDA/VoiceOver walkthrough, native-speaker editing and audible voice check are pending |
| Dependency maintenance | npm audit reported 15 findings on 25 October; no completed security migration is claimed |
| Primary track and roster | Lead must confirm exactly one track and final participants before creating the first submission |
| Pre-existing components | Confirm third-party and any prior product/data components; Git history alone is insufficient |
| Deck and video | Complete the draft media with genuine sponsor scenes; review length, legibility and disclosures before upload |
| Submission | Lead uploads all required components to HackOS before the recorded deadline; no submission has been made here |

The earliest recorded repository commit falls within the build window, but that does not
establish when every underlying component was authored. Describe third-party libraries and
data honestly. Do not claim Cursor use, live cloud services, persistent engine settlement,
an explained real run or investment performance without the corresponding evidence.

## Capture/rehearsal setup

Start the sample stack using `docker compose up --build --wait`, then open
http://localhost:8080. Use a fresh browser context, keep its data-mode banner visible at the
start, and record an actual run rather than a rewritten fixture. The optional
`web/scripts/capture-submission.cjs` captures four real API views using an existing Playwright
tooling runtime; set `TRADEPULSE_PREVIEW_URL`, `TRADEPULSE_API_URL` and `TRADEPULSE_CHROMIUM`
for a different environment. It writes hashes and the source run identity beside the images.

For final video recording, close unrelated windows and keep terminals/environment files off
screen. Re-record any section that depends on a newly delivered service. A labelled
SYNTHETIC fixture may demonstrate a UI state, but must never stand in for a real model run.
