# TradePulse

**Evidence-first crypto research: inspect a ranking, its explanation, and the checks behind it.**

**Track 2 — The Agent That Can Explain Why.** The submitted demonstration focuses on Crypto.
US and European equities are planned upgrades; experimental code and offline samples exist,
but their live end-to-end acceptance is not complete.

> Research and education only. TradePulse does not place, route or size orders.
> A research stance is not investment advice. An explained observation is not a profitable trade.

## What problem does it solve?

A financial ranking is easy to display and difficult to trust. A plausible model narrative
can cite the wrong observation, use information unavailable at the decision date, confuse
correlation with causality, or hide missing data. A high score alone does not explain why
an instrument appears in a list.

TradePulse gives researchers a path from a recorded ranking to its underlying evidence.
An analyst drafts an explanation, a skeptic challenges it, and deterministic checks inspect
the claim's references, source hashes, timing and supported measurements. The interface
retains rejected claims, missing observations and abstentions. The aim is inspectable
research rather than a promise that an AI can predict markets.

The product separates three questions: **what can be measured, what predicts out of sample,
and what survives modeled costs?** Those are different tests. The system does not lower a
gate simply to produce a positive recommendation.

## What was delivered?

The accepted Crypto run is `2026-10-23-87de33aa`, using the decision date **2026-10-23**
and a five-day horizon. Its original files contain **38 instruments, 38 NO_CALL stances,
three explained observations and 49 trace events**, including six actual GLM calls.
These are measured artifact counts, not promised outcomes of a future run.

The application includes Discover, a filterable leaderboard, instrument evidence drill-down,
Factor Lab, regime diagnostics, Track Record and Run Trace; Simple/Pro presentation; and
eleven-language authored UI labels. English is the default and other catalogs load on demand.
Original model narratives, financial values, identifiers and evidence remain unchanged.

The live Crypto case passed API/UI review on the lead's Mac. The public repository now
includes the **same original input, output and trace shown in the video**, plus a read-only
review server. It does not require a reviewer to own cloud credentials or rerun a paid model.

## Review the video result locally — no keys, GPU or Docker

Prerequisites: Python 3.11+ and Node 22.12+ or Node 24+. Initial package installation needs
internet access; serving the saved case does not call Zetaris, an engine or an AI provider.

```sh
git clone https://github.com/witold-andelie/tradepulse.git
cd tradepulse
```

**macOS / Linux, terminal 1:**

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[agent,dev]"
python -m scripts.review_demo --verify-only
python -m scripts.review_demo --port 8001
```

**Windows PowerShell, terminal 1:**

```powershell
py -3 -m pip install -e ".[agent,dev]"
py -3 -m scripts.review_demo --verify-only
py -3 -m scripts.review_demo --port 8001
```

Windows users choosing a virtual environment should use that environment's Python executable
consistently for installation and launch. The team's default Windows commands use `py -3`.

**Terminal 2, macOS / Linux:**

```sh
cd tradepulse/web
npm ci
VITE_API_BASE=http://localhost:8001 npm run dev
```

If already in the repository root, use `cd web` instead. On Windows:

```powershell
cd web
npm ci
$env:VITE_API_BASE = "http://localhost:8001"
npm run dev
```

**Open http://localhost:5173/pool/crypto**, not the default US route.
Use `localhost` to match the API's default CORS origin. Start with the leaderboard, open
WLD-USD, expand a claim's checks/evidence, then visit Factor Lab and Run Trace.

The verifier checks original file hashes and contracts before serving. `POST /run` is
disabled in this review server. The `REAL` field describes the **original execution**;
this viewing session is an offline inspection of saved results, not fresh inference.
See [detailed reproduction and troubleshooting](docs/RUNNING.md).

## Data, examples and reproducibility

The committed [real public-data snapshot](data/sample/README.md) is dated 2026-10-23 and is
under 25 MB. Its seven tables cover prices, pool membership, attention, macro observations
and filing/fundamental inputs. Public sources include Yahoo Finance through yfinance,
Wikimedia pageviews, SEC EDGAR and FRED. Not every source applies to every pool.

| Example | Input | Output | Original trace | Meaning |
| --- | --- | --- | --- | --- |
| Accepted Crypto demonstration | [input](runs/hosted-glm-acceptance-1/crypto/input.json) | [output](runs/hosted-glm-acceptance-1/crypto/output.json) | [trace](runs/hosted-glm-acceptance-1/crypto/trace-2026-10-23-87de33aa.jsonl) | Original REAL execution; GLM + Zetaris + Meterless engines |
| Offline Crypto computation | [input](examples/crypto/input.json) | [output](examples/crypto/output.json) | [trace](examples/crypto/trace.jsonl) | REPLAY data path; missing model recordings cause abstention |
| Offline US research baseline | [input](examples/us_equity/input.json) | [output](examples/us_equity/output.json) | [trace](examples/us_equity/trace.jsonl) | Experimental baseline for a future market upgrade |
| Offline European research baseline | [input](examples/eu_equity/input.json) | [output](examples/eu_equity/output.json) | [trace](examples/eu_equity/trace.jsonl) | Experimental baseline for a future market upgrade |

These are distinct recorded inputs and computed outputs. Offline examples are not relabelled
as passed live sponsor cases. [The evidence manifest](docs/review/crypto-evidence.json)
records the accepted case's original byte hashes and source commit. Generative text is not
promised to repeat verbatim in a new model run.

To recompute deterministic research from the sample, rather than inspect saved output, use
[the separate offline-computation path](docs/RUNNING.md#recompute-from-the-public-snapshot).
Without the matching model cassette, new offline explanations honestly abstain.

## How it works

```text
Dated source data -> typed, allow-listed queries -> deterministic research gates and ranking
                                            -> Analyst -> Skeptic -> Verifier
Meterless World Model / H-MEM <--------------> evidence, dated context and persistence
                                            -> saved output + original trace -> API -> web
```

Point-in-time checks limit what is available at a decision date. The verifier checks specific
properties; it is not universal fact checking and does not prove economic causality.
Skeptic suggestions remain hypotheses. Coverage is data availability, not confidence;
Track Record is historical evaluation, not a forecast or trading record.

## Sponsors and pre-existing components

| Component | Actual role and delivery boundary |
| --- | --- |
| **Zetaris** | Real data and evidence queries in the accepted Crypto run. Original full-template parity was measured separately. The read-only viewer does not contact Zetaris. |
| **Meterless World Model / H-MEM** | Actual snapshot, recall and remember operations in the Crypto trace. Official reference engines are third-party components, not engines invented by this team. |
| **Nightshift** | Connected and genuinely called by an earlier Analyst/Skeptic workflow. That earlier Crypto run failed full acceptance. The video shows this history separately. |
| **GLM-5.3-Flash** | Actual inference provider for the accepted Crypto demonstration. Its answers must not be attributed to Nightshift. |
| **NVIDIA NIM (Nemotron 3.5)** | Nine real hosted NIM calls (analyst `nemotron-3.5-lightning-30b-a3b`, skeptic `nemotron-3.5-bolt-e4b`) in Crypto run 2026-10-23-b8637c6c on the committed sample; three explanations verified. That run used DuckDB, not Zetaris or the engines. See [the NIM evidence](runs/nvidia-nim-crypto-1/README.md). |
| **spacexsi / Cursor** | No implemented sponsor-use claim is made for this delivery. Historical plans are not completed integrations. |

The organizer's reminder explicitly lists Nightshift as an AI provider. The accepted GLM
case alone is not proof that Nightshift generated that request; the distinction above is
intentional. [Sponsor evidence and boundaries](docs/sponsors.md) explain what was actually tested.

Third-party software includes React, Vite, TanStack Table, ECharts, FastAPI, LangGraph,
DuckDB, pandas, NumPy, PyArrow and the OpenAI-compatible client SDK. Zetaris and Nightshift
are existing sponsor platforms. The Meterless reference engines retain upstream licenses
and attribution in the [integration source](https://github.com/witold-andelie/tradepulse/tree/194033a1d7f78d96e60ec16f28e633f8c81ebf29/integrations/engines).
Existing libraries, public datasets and sponsor platforms are not claimed as original team work.
See [component provenance](docs/PRE_EXISTING_COMPONENTS.md).

## Team and delivery ownership

| Member | Contribution |
| --- | --- |
| **Wentao Ma — lead** | Product/Track 2 direction; architecture, contracts, core research/ranking/explanation/API; integration and final QA. Took over unfinished sponsor deployment/integration, completed the working Crypto path, and owns final packaging and demo delivery. |
| **Mengya Feng — Member A** | Ingestion-pipeline groundwork. Her implementation history is preserved; the lead completed fresh data collection, frozen-sample preparation and remaining data acceptance. |
| **Yin Hu — Member B, GitHub YinnHuu** | Frontend pages, Discover, Simple/Pro, evidence UI, accessibility and global localization V2. Original contributor commits are preserved. |
| **Hao Tan — Member C** | Quantitative-library work, 235 added property tests, and review/fixes for Regime, Track Record and Run Trace. |
| **Ojas Vairagkar — Member D** | Initially assigned AWS sponsor deployment/integration. No project code, working service or reviewable deliverable was supplied. Reported AWS account/policy/ARN/region blockers; Wentao Ma implemented and completed the TradePulse-specific sponsor work. |

The ownership change describes delivery status, not an assessment of a person's intent or
effort. See [contributions and takeover scope](docs/TEAM.md) for details.

## Next upgrades

1. **US equities:** complete filing-event identity/grounding, valuation constraints and live
   sponsor/API/UI acceptance before presenting that market as delivered.
2. **European equities:** expand appropriate local inputs and complete model/evidence acceptance.
3. **Stronger inference and replay:** improve structured-output reliability, preserve reviewed
   cassettes, and make provider-specific provenance easier to reproduce.
4. **Broader research validation:** independent crypto weekend timing, longer/less biased
   histories, additional graph evidence and out-of-sample evaluation.
5. **Accessibility editorial:** native screen-reader completion, financial-language review and
   device speech testing. These are not certified complete.

US/EU experimental samples remain available for inspection; they are not finished live-market
products. [Limitations](docs/honest-limitations.md) retain known data and verification gaps.

## Tests, video and delivery

```powershell
py -3 -m pytest -q
py -3 -m ruff check ingest quant integrations tradepulse run.py serve.py scripts --no-cache
cd web
npm test
npm run check:contracts
npm run build
```

CI needs no sponsor credentials. Network-marked sponsor checks and private full-lake checks
are separate from the public sample. See [CI scope](docs/CI.md).

The local recorded video is **130 seconds**, within the organizer's 1-4 minute range.
Video and narration are distributed separately from Git; the local `video/` directory is
excluded from both Git and Docker build contexts. Recording does not itself prove platform
upload or a completed submission. See [submission checklist](docs/submission/README.md).

Full sponsor re-execution uses the separate integration checkout described in
[the running guide](docs/RUNNING.md#optional-live-sponsor-re-execution).
The paused integration/US repair branch is not silently merged into main by this review release.

## License

Apache-2.0; third-party components retain their original licenses.
