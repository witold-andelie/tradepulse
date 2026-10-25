# Eight-slide deck — review content and speaker notes

Use a 16:9 navy/white/violet design consistent with the actual product. All slides should
carry “Review draft — hosted sponsor acceptance pending” until that acceptance exists.
Use actual captures from `assets/`; do not generate financial charts, model answers or
service screenshots. Primary track is unconfirmed. The audience is hackathon judges.

## 1. Inspect a signal before trusting a stance

TradePulse: an inspectable financial research workspace.

- Intended users: individual researchers and small research teams examining public markets.
- Problem: attractive scores can conceal missing data, weak validation and unsupported narratives.
- Research and education; no trade execution.

Speaker note: State the user problem without claiming a measured commercial benefit. The
delivered app turns a record into a path through measurements, limits and evidence.

## 2. One workflow, two levels of detail

Visual: `assets/leaderboard-real-api.png`.

- Browse separately ranked US equities, European equities and crypto.
- Simple and Pro display the same source records.
- Open measurements, explanations, limitations and the original trace.

Speaker note: These are real API-backed product visuals. The sample has 523 US, 55 European
and 38 crypto instruments. The run is dated 2026-10-23; it is not a claim of live market data.

## 3. Deterministic measurements, inspectable explanation

Diagram: request/as-of → frozen tables → factor gates → ranking/regime → analyst/skeptic/
verifier → report/API → research UI and trace.

- Code calculates scores, gates, costs and stances.
- The explanation workflow drafts, challenges and checks claims.
- Missing support produces an abstention.

Speaker note: The pipeline and explanation machinery exist. Matching real model recordings
are absent in this snapshot; do not draw a “successful hosted inference” arrow as evidence.

## 4. A valid result can be no call

Visual: `assets/factors-real-api.png`.

- Real snapshot: 616 instrument records, 33 factor cards.
- Zero ACTIVE factors; all 616 stances are NO_CALL.
- Nine explanations abstain; unavailable recordings remain visible.
- Measuring, predicting and earning are separate tests.

Speaker note: These numbers come from the captured actual run and committed examples. The
team has not loosened gates to create a more attractive demonstration. No return claim is made.

## 5. Built to be inspected and reproduced

Visual: `assets/trace-real-api.png`.

- Python, pandas/numpy, DuckDB/Parquet, LangGraph and contract-validated API.
- React, TanStack Table and ECharts; keyboard and numeric chart alternatives.
- Fresh offline startup and actual core/web Docker stack verified.
- 609 Python tests; 89 frontend tests; nine real-API browser groups passed.

Speaker note: Scope accessibility evidence accurately: Ticker Detail Lighthouse 100
desktop/mobile, 28 axe cases without violations and 18 native zoom cases. Actual NVDA on the
new guide remains pending; this is not a whole-product WCAG certification.

## 6. Sponsor roles and current delivery boundary

| Technology | Intended role | Verified state |
| --- | --- | --- |
| Zetaris | Live federated query and dated evidence layer | SQL/registration/offline adapter exist; hosted/live parity pending |
| Meterless | World Model relations and H-MEM feedback/conflicts | Python client exists; official engines/sidecar/core wiring pending |
| NVIDIA NIM | Hosted extraction, analyst and skeptic roles | Bounded record/replay client exists; real recording/smoke pending |
| Cursor | Development environment | Actual team usage and description require confirmation |

Speaker note: Do not use sponsor logos or architecture as proof of completed integration.
Replace this draft state with precise observed operations and evidence after D delivers.

## 7. The distinction we are building

Visual: `assets/ticker-real-api.png`.

- Keep financial computation deterministic and model narratives challengeable.
- Preserve rejected claims, missing inputs and source hashes.
- Target design: federated evidence plus persistent relation/feedback memory.

Speaker note: The first two points describe implemented behavior. The persistent memory /
hosted federation combination is the intended sponsor design, not a validated performance
advantage or completed engine deployment. Explain what is distinctive without inventing a benchmark.

## 8. Delivery path and next research

- Delivered: real sample, complete research UI, API, containers and three traced examples.
- Finish: hosted sponsor acceptance, actual model replay, final reader check and submission media.
- Future: validated out-of-universe lookup, longer evaluation histories and prospective tracking.
- Public source: `https://github.com/witold-andelie/tradepulse`.

Speaker note: Current-constituent survivorship bias, point-in-time source limitations and the
35 explicit source exceptions stay disclosed. Primary track, roster and pre-existing
components must be confirmed before the first submission. No final submission has been made.

## Source map

Counts: `assets/manifest.json`, `../validation/docker.json`, `../../examples/manifest.json`.
Checks: `../validation/README.md`, `../../web/ACCESSIBILITY_ACCEPTANCE.md`.
Sponsor state: `../sponsors.md`, `../../integrations/ACCEPTANCE.md`.
Limitations and delivery: `../honest-limitations.md`, `../STATUS.md`.
