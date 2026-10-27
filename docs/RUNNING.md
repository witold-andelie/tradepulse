# Reproduce and review TradePulse locally

There are three different activities. Choose one deliberately:

| Path | What runs | Keys/services | What it proves |
| --- | --- | --- | --- |
| Saved Crypto review | Original accepted input/output/trace, schema/hash checks, read-only API and latest main UI | None after dependency installation | You can inspect the same recorded case shown in the video |
| Offline computation | Real frozen Parquet data, deterministic pipeline, honest unavailable-model abstention | None | Public-snapshot data/math/contract reproducibility |
| Fresh sponsor execution | Live Zetaris, actual Meterless engines, configured AI provider | Your own installed services and private credentials | A new execution, whose quality/acceptance must be checked anew |

A saved REAL result is not a newly generated answer. A REPLAY result does not prove that a
model cassette exists. A SYNTHETIC preview contains fictional instruments/generated numbers.

## Recommended: inspect the saved Crypto demo

Requirements: Python 3.11+, Node 22.12+ or 24+, Git. No GPU, Docker or sponsor account is
needed. Package installation requires internet; the review server makes no provider calls.

Clone the public repository, then install from its root. macOS/Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[agent,dev]"
python -m scripts.review_demo --verify-only
python -m scripts.review_demo --port 8001
```

Windows team commands:

```powershell
py -3 -m pip install -e ".[agent,dev]"
py -3 -m scripts.review_demo --verify-only
py -3 -m scripts.review_demo --port 8001
```

If you use a Windows virtual environment, use its Python executable for both pip and launch.
The verify command checks the original bytes against docs/review/crypto-evidence.json,
validates RunRequest/RunOutput/TraceEvent and checks run/provider/engine identity.
The served artifact is 2026-10-23-87de33aa: 38 Crypto records, all NO_CALL, three explained
observations and 49 original trace events. These counts describe that artifact only.

Start the frontend in another terminal from web/. macOS/Linux:

```sh
npm ci
VITE_API_BASE=http://localhost:8001 npm run dev
```

PowerShell:

```powershell
npm ci
$env:VITE_API_BASE = "http://localhost:8001"
npm run dev
```

Open **http://localhost:5173/pool/crypto**. The root route defaults to US, which is not present
in this single-pool artifact. Discover is at /discover. Open WLD-USD from the leaderboard and
inspect explanation checks/evidence, then Factor Lab, regime diagnostics and Run Trace.

Useful GET endpoints:

- http://localhost:8001/health
- http://localhost:8001/runs/latest
- http://localhost:8001/runs/2026-10-23-87de33aa
- http://localhost:8001/runs/2026-10-23-87de33aa/trace

The API and original JSON agree. Responses carry X-TradePulse-Review-Mode:
saved-real-run; generation-disabled. POST /run returns 405. The review server does not
generate model answers, update engine memory or place orders. The original output's REAL
and sample_mode=false remain unchanged to preserve its provenance. The standard health
sample_mode flag describes current server configuration, not how the artifact was generated.

For a production UI build, set the same VITE_API_BASE before npm run build, then use
npm run preview -- --host 127.0.0.1 --port 5173 --strictPort. Keep the browser URL on
localhost to match the API's default CORS origin.

## Troubleshooting

- Port 8001 occupied: choose another --port and set the matching VITE_API_BASE.
- Blank/unknown US pool on initial navigation: use /pool/crypto for this single-pool result.
- CORS: use localhost:5173; for a different origin, set WEB_ORIGIN on the API process.
- SYNTHETIC banner: the frontend has no effective API base. Set it, check web/.env.local for
  conflicting settings and restart/rebuild Vite. Do not treat a fixture as the accepted run.
- API unavailable: Retry is visible; no fixture fallback should replace configured API data.
- Hash verification fails: restore the original committed files. Do not change the manifest
  to bless edited results. Published evidence uses fixed original bytes on Windows too.
- Python import error: install the agent extra in the same interpreter that starts the API.

## Recompute from the public snapshot

This computes new research output, rather than serving the saved GLM artifact. The committed
seven-table snapshot is dated 2026-10-23 and below 25 MB. No hosted model cassette is supplied
for full inference replay, so explanations may abstain and research stances remain NO_CALL.

PowerShell, repository root:

```powershell
$env:SAMPLE_MODE = "true"
$env:RECORD_LLM = "false"
py -3 serve.py --port 8002
```

macOS/Linux:

```sh
SAMPLE_MODE=true RECORD_LLM=false python serve.py --port 8002
```

Point a separately started frontend at http://localhost:8002. serve.py verifies table paths,
sizes, hashes and the sample date before bootstrapping a missing saved run. It can reuse an
existing run saved directly by RunStore in runs/<run_id>/. The nested published acceptance
folder is not imported automatically by this launcher. To force independent computations
without overwriting original evidence, use a new output directory:

```powershell
$env:SAMPLE_MODE = "true"
$env:RECORD_LLM = "false"
py -3 -m scripts.generate_examples --offline-check --output runs/recomputed-examples
```

On macOS/Linux use python -m scripts.generate_examples with the same SAMPLE_MODE and
RECORD_LLM environment settings. Choose a new directory for another run. The generator
blocks socket/DNS activity during computation and validates output/trace schemas. Run IDs,
creation times and timings change; do not demand byte-identical generative text or metadata.
The original three examples are linked from examples/README.md. US/EU examples are research
baselines for future upgrades, not completed live-market acceptance.

## Optional Docker offline computation

```sh
docker compose up --build --wait
```

Open http://localhost:8080/pool/crypto. The Compose stack runs the core and web; it does not
install Zetaris or Nightshift, and does not automatically start the separate engine project.
Its Docker context excludes runs/ and video/, so it computes from the real sample rather
than importing the saved live-demo case. Named volumes retain new outputs. Preserve them
when you need evidence. Set CORE_PORT/WEB_PORT if the host ports are occupied.

## Optional live sponsor re-execution

The complete tested sponsor adapters/engine source are available on the separate integration
branch, not silently included as a merge of the pending US work. For a reproducible source
baseline corresponding to the published Crypto artifact, use commit
194033a1d7f78d96e60ec16f28e633f8c81ebf29 in a separate checkout/worktree. Later US identity
repairs are reviewed separately in PR #9; the Crypto viewer does not require them.

```sh
git fetch origin
git worktree add --detach ../tradepulse-live 194033a1d7f78d96e60ec16f28e633f8c81ebf29
cd ../tradepulse-live
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[agent,dev]"
docker compose -f integrations/engines/compose.yaml up -d --build --wait
```

Install/register Zetaris using its own platform distribution and register the seven sample
tables. It is a separately supplied service; it is not included in the TradePulse image.
The lead's actual registration route was NDP File System -> individual root uploads ->
move to /file-store -> File Source & API -> TRADEPULSE_LAKE -> Parquet table registration.
Use microsecond-compatible copies where that Spark distribution rejects timestamp nanoseconds.
Source Parquet bytes are preserved. The helper integrations/zetaris/prepare_parquet.py in the
integration checkout validates conversion.

Create your own ignored .env.crypto.local. Never reuse another person's credentials:

```dotenv
LLM_PROVIDER=glm
ZETARIS_API_MODE=proxy
ZETARIS_BASE_URL=http://localhost:3000
ZETARIS_ORG_ID=YOUR_NUMERIC_ORG_ID
ZETARIS_API_KEY=YOUR_OWN_KEY
ENGINES_ENABLED=true
ENGINES_URL=http://127.0.0.1:8790
ENGINES_WORLD_BATCH_SIZE=50
ENGINES_REMEMBER_BATCH_SIZE=50
ENGINES_WRITE_TIMEOUT_SECONDS=60
ENGINES_READ_TIMEOUT_SECONDS=60
GLM_BASE_URL=https://opencode.ai/inference/go/openai/v1
GLM_MODEL=glm-5.3-flash
GLM_API_KEY=YOUR_OWN_AUTHORIZED_KEY
GLM_REASONING_EFFORT=low
GLM_RESPONSE_FORMAT=json_object
GLM_MAX_TOKENS=8192
GLM_MAX_CONCURRENCY=1
GLM_TIMEOUT_SECONDS=180
GLM_QUEUE_TIMEOUT_SECONDS=600
```

Use an authorized provider/account; the recorded endpoint is not a free public service.
The loader reads configuration as data, without shell evaluation. Then:

```sh
python -m integrations.preflight --service zetaris --env-file .env.crypto.local
python -m integrations.preflight --service engines --env-file .env.crypto.local
python -m integrations.launch --env-file .env.crypto.local --as-of 2026-10-23 --pools crypto --top-k 1
```

This is a new live computation, not a promise to reproduce the exact old prose. Inspect its
actual output and trace before calling it accepted. For the full acceptance pack, use
integrations.live_acceptance in that checkout; it runs the separately bounded parity gate
and can be much slower than the saved review. The existing saved case is the quick judge path.

Nightshift uses its own local app, advertised model and private proxy-token file. Its
historical provider integration is separate from the accepted GLM run. Do not switch provider
labels to satisfy a checklist; preserve actual model/role provenance. See docs/sponsors.md.
