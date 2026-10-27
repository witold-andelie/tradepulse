# Short path from the current failure to recording

The US first-3 error is a confirmed ten-second World Model POST ReadTimeout, followed by a
late server completion. The fix is bounded transport handling, not new models or different
research gates. Preserve its failed manifest and the original raw evidence.

## One new US run

Update lead/sponsor-integration-wip-20261027 without losing private configuration. Keep the
existing services and data/cache/extraction_cache.jsonl. Run the current explicit command in
[HOSTED_ACCEPTANCE.md](HOSTED_ACCEPTANCE.md), output runs/hosted-glm-us-first-4, with:

```sh
export ENGINES_WORLD_BATCH_SIZE=50
export ENGINES_REMEMBER_BATCH_SIZE=50
export ENGINES_WRITE_TIMEOUT_SECONDS=60
export ENGINES_READ_TIMEOUT_SECONDS=60
```

Keep the working GLM low/8192/json_object settings, real engines, live instrument evidence,
and original first-2 receipt sources. The already extracted documents reuse their cache;
additional uncached documents remain subject to the unchanged core bound. No service rebuild,
state reset, provider switch, additional parity network run or standalone write probe is needed.
Existing events must return actual duplicate acknowledgements when reused. Never count them
as newly ingested. Snapshot checks still require all acknowledged event identities.

If it fails, inspect the preserved specific request receipt; do not launch a sequence of
whole-pool retries. The accepted Crypto case remains usable independently.

## Prepare the real API/UI while US runs

In another activated terminal from the project root:

```sh
python3 -m integrations.launch \
  --env-file ~/getting-started/.env.local \
  --env-file .env.glm.local \
  --serve
```

In a web terminal, using the existing installed dependencies:

```sh
cd ~/tradepulse/web
VITE_API_BASE=http://localhost:8000 npm run dev -- --host 127.0.0.1
```

Open http://localhost:5173. The server exposes GET /health, /runs/latest,
/runs/{run_id} and /runs/{run_id}/trace. Check the selected run ID against the original
accepted-case manifest, and check REAL mode. HTTP 200 alone is not this identity check.
Do not POST /run to generate another run just to open the UI. Confirm no fixture fallback,
no browser errors, and agreement between API values, tiers/verdicts and displayed values.

Initially use the accepted Crypto output to review Leaderboard, one instrument, Factor Lab
and Run Trace. Do not navigate to a pool absent from that single-pool output. Once first-4
passes selected_cases_ok, inspect its saved output/trace API endpoints, reload the frontend
and check that the new latest run is that accepted US run before making it the main demo.
Review explanation prose for unsupported facts; verifier checks are not universal entailment.

Then index Crypto plus the accepted first-4 source using assemble_acceptance. A two-pool
index honestly stays submission_complete=false. EU and a third accepted input/output pair
remain separate work; do not rewrite failed EU evidence. Existing README examples can be
shown with their original offline/abstention disclosures, not relabelled as hosted success.

## Capture the working feature

Prepare a short walkthrough while inference is running. Record the actual accepted case
once its API/UI checks pass; opening saved results does not mean the LLM is recomputing live.

1. Introduce the research question and the selected historical decision date.
2. Show the real pool and an instrument, its stance, original explanation and query evidence.
   Open a claim and show the actual checks/source hashes; keep abstentions visible.
3. Show Run Trace: actual Zetaris evidence, GLM analyst/skeptic and Meterless engine operations.
   If demonstrating a live Zetaris query, reuse the already working universe_pool template.
4. Show Factor Lab or regime limitations. NO_CALL and inactive factors are valid outputs;
   do not alter gates to manufacture a positive recommendation.
5. Disclose limits: historical research, no order execution, checked versus unverified text,
   and any incomplete pools. Keep every key/token and private configuration off screen.

Normal inference in this profile is GLM; Meterless contributes real World Model/H-MEM
functionality. Separate earlier Nightshift evidence must not be presented as the provider of
these GLM explanations. Video recording preparation is independent of three-pool completion,
native voice tests and eleven-language editorial. This is not an event eligibility attestation.
