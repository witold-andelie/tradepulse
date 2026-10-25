# Automated acceptance

`.github/workflows/ci.yml` runs on pull requests, pushes to `main`, and manual dispatch.
It uses published official Actions pinned to full commit identities, read-only repository
permissions and bounded job durations. No cloud keys or production lake are required.

## Jobs

| Job | Checks |
| --- | --- |
| Python / Windows / Python 3.13 | Pinned Ruff policy, complete offline pytest suite, explicit committed-sample execution gate, fresh hash-verified sample computation with sockets/DNS blocked and cached reuse |
| Web / Linux / Node 22 | Frozen npm install, full npm audit, all unit tests, contract fixtures/trace validation, production build and non-fixture 1 MB chunk budget |
| Web / Linux / Node 24 | Same checks on the second supported Node line |

The Python job explicitly verifies which interpreter `py -3` launches. A clean checkout may
skip the seven parameterized production-lake cases because that private lake is not committed.
The committed sample case must execute successfully; its skip is a CI failure. Original test
assertions are preserved. Network-marked live tests remain outside credential-free CI.

The offline smoke executes the actual sample pipeline, rather than substituting a fixture
RunOutput. Counts, verdicts, trace-event totals, timing and network-attempt counts are calculated
from that run. SAMPLE_MODE does not auto-connect to engines, even if their settings exist.
Missing model recordings still produce the actual abstentions, not fabricated answers.

Each job uploads its actual JSON/JUnit reports with seven-day retention, including on failure.
Only `.ci-output/` is uploaded; credentials, provider caches and production logs are excluded.
Previous runs on the same branch are cancelled when a newer change supersedes them.

## Local equivalents

```powershell
py -3 -m pip install -e ".[ingest,agent,dev]"
py -3 -m ruff check ingest quant integrations tradepulse run.py serve.py scripts --no-cache
py -3 -m pytest -q
py -3 -m scripts.ci_offline_smoke --output .ci-output/offline-smoke.json
cd web
npm ci
npm audit --registry=https://registry.npmjs.org
npm test
npm run check:contracts
npm run build
```

The smoke keeps temporary runs next to the specified output file and removes them afterwards.
On the team's Windows machines choose a D: output/cache directory. Its recorded metadata
does not include credentials or source contact settings.

## Acceptance boundary

CI verifies offline behavior and repository artifacts. It does not establish Zetaris deployment,
official Meterless engine conformance/persistence, genuine NIM calls, sponsor integration
from Europe or native screen-reader acceptance. Those require their own real-service/manual
evidence. Branch protection is not changed by this workflow; the repository owner can make
these checks required separately if desired.
