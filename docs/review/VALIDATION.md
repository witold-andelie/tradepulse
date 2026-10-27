# Saved Crypto review package validation

Checked on Windows on 2026-10-27 against release source commit `468b5e8`.
This validates inspection of authentic saved results, not a new sponsor/model execution.

## Results

- Python suite: **637 passed, 7 skipped**, with 19 dependency warnings.
  The skipped checks were not converted into passes.
- Ruff: passed for ingest, quant, integrations, tradepulse, run.py, serve.py and scripts.
- Frontend: **18 test files, 130 tests passed**; contract checks passed; production build passed.
- Build: largest JavaScript chunk was approximately **672 kB** uncompressed.
- Original Crypto input/output/trace: exact byte hashes and existing contracts passed.
  See [artifact hashes](crypto-evidence.json).
- Exported tracked files using `git archive` into an empty directory with no private env,
  model cache, node_modules or video. The saved-case verifier and API ran from this copy;
  Python's imported TradePulse package was confirmed to be inside the exported directory.
- Production main UI reviewed in Chrome: Crypto leaderboard, WLD-USD detail, Factor Lab,
  Run Trace. API output equaled the original JSON; the API returned all **49** original events.
  WLD's original explanation was preserved. No browser console errors or fixture downloads
  were observed in these journeys.
- API write blocking and unknown-run behavior were covered by the new review tests.
  An edited artifact byte was rejected by the verifier.
- `video/` remains ignored and has no tracked files. The separately recorded local video
  is 130 seconds; its English narration remains local in that ignored directory.

## Scope

The clean-source check used already installed Python packages and existing locked frontend
dependencies. It was not a fresh dependency download or a new Docker build on every platform.
The frontend source is unchanged from main `e76486a`; this release adds a saved-case server,
authentic published artifacts, tests and documentation.

No model, Zetaris or Meterless service was called during this saved-result validation.
The original artifact records GLM inference and real Zetaris/Meterless integration. Historical
Nightshift use is documented separately; it did not generate this accepted GLM result.
US/EU live acceptance, all-language editorial review, device speech testing and submission
platform upload are not certified by these checks.

Use [the running guide](../RUNNING.md) to repeat this review or choose a separate computation.
