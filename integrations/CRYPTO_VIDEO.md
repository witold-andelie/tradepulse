# Crypto-only final demo: 1-4 minutes

Use the organizer's latest checklist supplied by the lead: a working end-to-end feature,
Zetaris, a Meterless Engine in that feature, Nightshift as an AI provider, original agent
traces, at least three sample inputs/outputs, public repository, setup/usage, sponsor and
pre-existing-component disclosures, no credentials, finished slides and a recorded video.
The supplied checklist does not require every asset pool to appear in the video.

## Actual provider scope

Nightshift was connected and genuinely called by the earlier Crypto Analyst/Skeptic flow;
this was more than a standalone Hello. The earlier full Crypto run nevertheless failed its
engineering acceptance and abstained. Keep that status. The accepted demo run
2026-10-23-87de33aa uses GLM, with live Zetaris and actual Meterless snapshot/recall/remember.
Nightshift and the Meterless engines are separate components.

Show the authentic Nightshift connection/history and role evidence in a separate, labelled
integration segment. Do not describe the accepted GLM Crypto output as Nightshift-generated
or turn the earlier failed run into a passed run. A connection test alone does not establish
that a current Crypto explanation was produced by Nightshift. If the organizer requires
Nightshift specifically in the accepted demonstrated request, this GLM case alone does not
prove that requirement: obtain confirmation or an actual qualifying feature execution before
claiming it. Do not invent a new requirement that all roles must use one provider either.

NVIDIA and spacexsi were not used for this delivery and should not be credited as implemented
integrations. Describe any available unused route as unused, not demonstrated sponsor usage.

## Frontend must come from latest main

Keep the already accepted backend on port 8001, with its original saved Crypto output/trace.
Do not replace it or generate another run merely to open the UI. Build a separate frontend
from latest origin/main; do not copy feature-branch files into it:

```sh
cd ~/tradepulse
git fetch origin
git worktree add --detach ~/tradepulse-video-main origin/main
cd ~/tradepulse-video-main/web
npm ci
VITE_API_BASE=http://localhost:8001 npm run build
npm run preview -- --host 127.0.0.1 --port 5173 --strictPort
```

If that worktree already exists, preserve its state and verify/reuse it. If 5173 is occupied
by the old TradePulse frontend, stop that frontend before starting the new preview; do not
terminate unrelated applications. Use http://localhost:5173, matching the backend's existing
CORS origin. Record git rev-parse HEAD and verify it matches freshly fetched origin/main
before building. Recheck for a newer main before the final capture and rebuild if needed.

Before recording, compare GET http://localhost:8001/runs/latest to the accepted manifest:
run_id must be 2026-10-23-87de33aa, data_mode REAL, sample_mode false. Check its trace endpoint,
then the main-build Leaderboard, WLD-USD, Factor Lab and Run Trace. Retain original numbers,
NO_CALL stances and model caveats. No console errors or fixture fallback are acceptable.

## Suggested three-minute sequence

| Time | Capture | Required wording/boundary |
| --- | --- | --- |
| 0:00-0:20 | Title, question, decision date | Crypto research with evidence, not trading advice. |
| 0:20-0:50 | Accepted Crypto leaderboard and an instrument | Source-driven counts/values; no US/EU success claim. |
| 0:50-1:35 | Original explanation, claim checks and evidence | Open references/hashes; speculative skeptic text is not verified fact. |
| 1:35-2:15 | Run Trace and sponsor evidence | Real Zetaris queries, GLM calls and actual Meterless engine operations. |
| 2:15-2:40 | Separate authentic Nightshift evidence | Historical provider integration; distinguish it from this GLM run. |
| 2:40-3:00 | Factor limitations and README/setup | NO_CALL/inactive factors remain visible; state remaining work honestly. |

Show the real input and corresponding output/trace together. If results were generated
earlier, label them as a saved real run; do not simulate fresh inference. An optional short
live Zetaris query should reuse the already working template. Waiting may be edited out,
with no fabricated terminal output or timing. Hide tokens, keys, configuration files and
credential screens throughout. Background speech/eleven-language editorial are deferred.

README must contain at least three actual computed input/output pairs, their trace links
and correct REAL/REPLAY/SYNTHETIC disclosures. They need not be three pools, but do not label
offline abstention examples as passed hosted cases or reuse one output for different inputs.
Credit the official Meterless reference engines and upstream/pre-existing components.

Confirm the roster before creating the submission because the organizer says it locks then.
Submit an honest usable version early and update it before 23:45 UTC on 27 October 2026.
This document is a capture plan, not evidence that a video or slides have been produced.
