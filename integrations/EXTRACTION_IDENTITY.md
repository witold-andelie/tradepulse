# US identity repair: review branch, not merged to main

The lead paused merging the sponsor integration. The fourth US run failed before any World
Model request: 857 cached events contained three repeated event IDs. Crypto run
2026-10-23-87de33aa separately passed actual API/UI review on port 8001; its inference is GLM.

Local source inspection confirms 321 filing-text rows but 319 distinct document hashes.
FOX/FOXA share one document and NWS/NWSA share another. These are legitimate source rows.
The former SHA-only extraction cache could reuse one symbol's events for the other share
class. This reproduces duplicate IDs without any duplicated source row or failed engine.
The exact Mac duplicate groups still need the read-only diagnostic below.

The repair uses document hash, symbol, accession and availability for cache identity. Original
event IDs and source hashes are unchanged. Legacy nonempty results are reused only with
matching provenance and renewed grounding checks; old bytes are retained. Legacy empty
results without source identity may require one new extraction. New entries include source
metadata and remain append-only. Identical event repetitions are counted and folded before
factor computation; same-ID different-payload events raise an error. Pipeline handling must
not turn that error into empty factors. The World Model duplicate guard is unchanged.

After reviewing the core repair PR, use lead/fix-extraction-identity-20261027 for a controlled
Mac validation. Do not merge main, clear the cache or repeatedly generate whole-pool runs.

```sh
python3 -m integrations.extract_identity \
  --report runs/hosted-glm-us-first-4/identity-preflight.json
```

This reads local sample/cache only, never calls a model or engine, and refuses to overwrite
an existing report. Review different_fields for old duplicate groups and needs_extraction.
If any conflicting-payload group or identity_conflict remains, stop and retain the report.
Do not select an arbitrary version. If safe, run one new US first-5 using the existing
first-2 parity/bulk receipts and bounded GLM/engine settings. Reuse valid cached work; only
missing source identities need extraction. All original failed manifests remain failed.

Do not delay Crypto recording while waiting for US. Keep the 8001 API serving the accepted
Crypto run. Build the frontend separately from latest origin/main, with its API base set to
http://localhost:8001. Do not record the US/EU pages as passed or change the active Crypto
run while the recording is in progress. Nightshift's historical provider evidence is separate
from the current GLM Crypto case; do not describe them as the same successful execution.
