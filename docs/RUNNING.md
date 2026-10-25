# Running the delivered sample and API

Run these commands from a clean repository checkout on Windows. The sample already contains
seven real provider tables for 2026-10-23; provider collection, GPU hardware and credentials
are not needed for the offline path.

```powershell
py -3 -m pip install -e ".[agent,dev]"
$env:SAMPLE_MODE = "true"
$env:RECORD_LLM = "false"
py -3 serve.py
```

`serve.py` reuses an existing contract-valid saved run. On a fresh checkout it verifies all
seven frozen table paths, sizes and hashes, derives the decision date from the sample
manifest, computes a run and saves it before exposing the API. A corrupted, missing or
future-dated snapshot fails startup. Automatic startup never records model answers; if a
new run is needed while `RECORD_LLM=true`, it stops with a clear error instead.

The measured first startup took 32.26 seconds on the collector; cached startup took 0.12
seconds. Both were checked with all socket connection/DNS calls blocked during computation,
and zero network attempts occurred. Timing depends on the machine. Evidence is in
`validation/sample-startup.json`.

The API listens on http://127.0.0.1:8000. Its health endpoint is `/health`, the saved result is
`/runs/latest`, and its trace is `/runs/{run_id}/trace`. The existing lower-level command
`py -3 run.py --serve` still starts only the HTTP service and does not bootstrap a run.

In a second PowerShell terminal:

```powershell
cd web
npm ci
$env:VITE_API_BASE = "http://127.0.0.1:8000"
npm run dev
```

Open http://localhost:5173, matching the API's default allowed browser origin. For a different
frontend origin, set `WEB_ORIGIN` on the API process before starting it. An API connection
failure is displayed with Retry; it never silently switches to synthetic data.

For the separate synthetic frontend preview, leave `VITE_API_BASE` empty and ensure no
`web/.env.local` overrides it. The SYNTHETIC banner identifies that mode.

## What the current real-data run means

The delivered snapshot currently yields 616 NO_CALL records, 33 factor cards and nine
abstained explanations. No factor passes all gates; no ACTIVE factor is invented. The
matching model cassette has not been supplied, so unavailable model answers lead to
abstention. REPLAY describes the execution mode; it does not prove successful NIM inference.
The UI's Run limitations and original explanation records retain this distinction.

The [three examples](../examples/README.md) contain computed inputs, outputs and original
trace bytes. They demonstrate actual offline data processing, not complete sponsor acceptance
or investment performance.

## Local container configuration

The core image now uses `serve.py`. Compose waits for the core health check before starting
web, preventing an initial proxy error while a fresh sample is being computed. Health-check
retries and startup grace are bounded. Both images were built and started with empty named
volumes in the isolated `tradepulse-acceptance-20261025` project. The core ran as the
unprivileged `tradepulse` user, computed and persisted the sample, became healthy, and served
616 records through the web container's nginx proxy. All nine browser groups passed on
this stack, including the corrected REPLAY disclosure. See [the runtime report](validation/docker.json)
and [browser report](validation/docker-browser.json). This does not certify the missing
engines service or hosted sponsor integrations.

```powershell
docker compose up --build --wait
```

Open http://localhost:8080. If the default ports are occupied, set `CORE_PORT` and `WEB_PORT`
in the shell before starting Compose. Runs and traces use named volumes so an empty Linux
host directory cannot prevent the non-root core from saving results. Existing host `runs/`
and `logs/` directories are not imported or overwritten. `docker compose stop` preserves
the container data; avoid deleting the volumes when keeping recordings and evidence.

## Repeat the real API browser checks

The optional `web/scripts/real-api-acceptance.cjs` uses an existing Playwright tooling runtime,
not a new application dependency. Build a separate API frontend and point the script at it:

```powershell
cd web
$env:VITE_API_BASE = "http://127.0.0.1:8000"
npm run build -- --outDir node_modules/.cache/tradepulse-api-build
npm run preview -- --host 127.0.0.1 --port 5198 --strictPort --outDir node_modules/.cache/tradepulse-api-build
```

Start the API with `WEB_ORIGIN=http://127.0.0.1:5198` for this preview. From the repository
root, run the browser script in a tooling environment where `require('playwright')` resolves.
Set `TRADEPULSE_CHROMIUM` to system Chrome, `TRADEPULSE_PREVIEW_URL` to the preview URL,
`TRADEPULSE_API_URL` to the API and `TRADEPULSE_QA_DIR` to a private evidence folder.
All expected record/filter counts are calculated from the actual API response. Normal data
requests are not intercepted; a separate deliberate 503 tests visible failure without a
synthetic fallback.
