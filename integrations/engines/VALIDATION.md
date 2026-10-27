# Local Meterless engine acceptance

Measured on Windows with the Docker Linux backend on 27 October 2026. These checks do not
establish Nightshift inference or live Zetaris parity.

## Official source and conformance

Upstream commit: `1742dec56a66e58eef9dda2d2b865823758ca8cd` in
[Meterless/Meterless](https://github.com/Meterless/Meterless/tree/1742dec56a66e58eef9dda2d2b865823758ca8cd).
All 23 vendored files match the Git blob hashes returned by GitHub for that commit after LF
normalization. LICENSE files and the source NOTICE are included. Adaptation is outside vendor/.

```
cd integrations/engines
npm ci
npm test
npm run check
npm run conformance
npm audit
```

Observed results:

- HTTP/service tests: 8 passed. They cover ingestion, duplicate identity, invalid batches,
  historical versions, dated recall, token protection, settlement and recovery from storage.
- TypeScript: passed.
- Vendor verification: 23 files matched.
- Official H-MEM conformance: 13/13 passed.
- Official World Model conformance: 8/8 passed.
- Registry dependency audit: zero vulnerabilities.

The full Python regression suite after this integration passed 680 tests, with 14 live
network cases deselected by default. Nineteen existing BeautifulSoup/lxml deprecation
warnings were reported. The seven-table converter also passed exact lossless conversion
and read-back for all 1,067,346 sample rows, without modifying the source tables.

## Real core-to-container request path

```
docker compose -f integrations/engines/compose.yaml up -d --build --wait
```

Then, from repository root in PowerShell:

```powershell
$env:ENGINES_ACCEPTANCE_URL = "http://127.0.0.1:8790"
py -3 -m pytest integrations/tests/test_live_engine_pipeline.py -q -m network --basetemp=.pytest_tmp/engine-acceptance
```

The test ran three real-snapshot pool pipelines with DuckDB, a deliberately empty replay
cassette and the actual Python EnginesClient calling the running container over HTTP.
It passed in 40.69 seconds. It checked RunOutput contracts, original trace operation records
and retrieval of each run's persisted recommendation. No synthetic model reply was supplied.
The models abstained because the replay cassette was empty.

After the run, an actual container restart preserved:

```json
{"hmem_records":616,"hmem_ledger_entries":619,"world_model_events":0}
```

These are measured counts from the first dedicated test volume. Repeating the test creates
new run IDs and therefore new memories; do not assert that the store must always contain 616.
The snapshot calls returned empty World Model data in this run. No grounded event extraction
or non-empty validated graph on real data is claimed by this test. The service tests exercise
non-empty event and relationship behavior using contract-valid synthetic inputs.

## Remaining acceptance

- Run the Zetaris client and all-template parity on the Mac's actual registered tables.
- Complete a Nightshift request with the real runtime token, then the sponsor-connected cases
  in `integrations.live_acceptance`.
- Review actual model answers and the generated cassette before publishing or offline replay.
- The existing sample-mode launcher remains offline and does not auto-connect to the sidecar.
