# Pre-existing components and attribution

TradePulse combines project-specific research/orchestration/UI work with existing platforms,
libraries and public data. The team does not claim the following components as newly invented
during the hackathon.

| Component | How it is used | Attribution / boundary |
| --- | --- | --- |
| Zetaris | Registered data sources, templated SQL and evidence retrieval | Existing sponsor platform, installed separately; not bundled or authored by the team |
| Nightshift | Earlier local OpenAI-compatible AI-provider connection and real role calls | Existing Meterless application; current accepted Crypto inference is GLM |
| Meterless World Model and H-MEM | Typed snapshots, historical memory context and persistence through the sidecar | Unchanged official reference/conformance sources at upstream commit 1742dec56a66e58eef9dda2d2b865823758ca8cd; original licenses retained in the integration checkout |
| GLM-5.3-Flash / OpenCode gateway | Hosted model responses in the accepted Crypto run | Third-party model/service; requires authorized credentials; not a team-trained model |
| LangGraph, FastAPI, OpenAI-compatible SDK | Agent orchestration, HTTP API and provider transport | Existing open-source libraries |
| pandas, NumPy, DuckDB, PyArrow | Data processing, deterministic calculations and Parquet | Existing open-source libraries |
| React, Vite, React Router, TanStack Table, ECharts, Tailwind | Frontend, routing, tables, charts and styling | Existing open-source libraries, pinned in the package manifest/lockfile |
| Yahoo Finance/yfinance, Wikimedia, SEC EDGAR, FRED | Public market, attention, filing/fundamental and macro data | Source policies/provenance apply; no claim of ownership over third-party data |

The project-specific work includes schemas and adapters, research gates and point-in-time
handling, ranking/regime/walk-forward composition, explanation/evidence checks, original
API/UI integration, accessibility/localization, sponsor wiring and reproducibility tools.
Individual authorship follows the contribution history and docs/TEAM.md.

Official Meterless source, commit notice and per-engine licenses are public in the
[integration checkout](https://github.com/witold-andelie/tradepulse/tree/194033a1d7f78d96e60ec16f28e633f8c81ebf29/integrations/engines).
The main license is Apache-2.0; it does not replace third-party licenses or data terms.

NVIDIA NIM use is limited to the recorded Nemotron 3.5 run in runs/nvidia-nim-crypto-1.
No implemented spacexsi or Cursor sponsor-use claim is made. Historical plans,
configuration placeholders or available unused routes are not evidence of actual usage.
