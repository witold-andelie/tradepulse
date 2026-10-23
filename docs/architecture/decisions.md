# Decision log

Short records of decisions that shape the code. Newest first. Change a decision by adding a new
entry, not by editing an old one.

## 2026-10-23

| # | decision | why |
|---|---|---|
| D14 | **A fifth member (Member D) owns the sponsor integrations** (`integrations/`): Zetaris deployment, registration, templates, adapters; Meterless Runtime, the LLM chain with cassette, the engines sidecar; the sponsor write-up draft. Zetaris registration moves from `ingest/` (old A8) to D1. | Sponsor work is load-bearing and specialised. It also takes the Zetaris instance off the lead's laptop (only 6 GB available to Docker). |
| D15 | **Zetaris hosting: AWS (required, see D17) with the lake in a private S3 bucket** (`s3a://` paths, which the Zetaris recipes have proven). Local Docker remains the fallback. | Removes the open question of how a local container reads host files, and gives the team one shared instance. |
| D17 | **Member D deploys on AWS only (EU region), exposing HTTPS, IP-allow-listed, token-protected endpoints documented in `integrations/ACCESS.md`.** Meterless Runtime (Nightshift) runs on the lead's RTX 4060 laptop in Europe; D writes the integration code and the setup guide. The engines sidecar runs locally (docker-compose, judges) and on AWS (shared). | D is in the US and the rest of the team is in Europe, so no one can use D's machine. Nightshift needs a local NVIDIA GPU. |
| D16 | **Agents query data only through allow-listed SQL templates** (`integrations/zetaris/templates/`) rendered with typed parameters. `rows_sha256` is back-end independent. | Safety (no LLM-written SQL), and the verifier can re-run evidence on either back end. |

## 2026-10-22

| # | decision | why |
|---|---|---|
| D1 | **Product = explainable cross-sectional ranking** (WorldQuant-style) for three pools: `us_equity`, `eu_equity`, `crypto`. Each pool is ranked separately, and the pools are linked through cross-pool graph edges. | Recommendation must be strong. Diagnosis becomes the "why" layer of each ranking. |
| D2 | **No A-shares.** | Product decision. |
| D3 | **Universe:** US = S&P 500 ∪ Nasdaq-100 (~520) + extras; EU = EURO STOXX 50 + extras; crypto = top ~40 by market cap, excluding stablecoins and wrapped tokens. Any US ticker can also be looked up on demand. | Customers want many examples. Breadth also makes IC statistics meaningful (IR ≈ IC·√breadth). |
| D4 | **Backtest window = last 1 year** (plus warmup history for lookbacks). | Product decision. Limitation: few regime episodes, survivorship bias from current constituents. Both are disclosed. |
| D5 | **LLMs never score.** LLMs extract structured events, propose graph edges, draft explanations and play skeptic. Scores, gates, weights, tiers and verification are deterministic code. | Auditability; the "LLM proposes, data disposes" pattern. |
| D6 | **Measure / predict / earn gates** on every factor (G1–G5). A failing factor is shown with weight 0. | Separates description from prediction from profit. |
| D7 | **Sponsors:** Zetaris = federated query layer over the lake plus EDGAR REST; Meterless Runtime = local extractor and guard LLM; Meterless World Model = relation graph and event timeline (as_of snapshots); Meterless H-MEM = recommendation memory and settlement; NVIDIA NIM = analyst and skeptic LLMs. | Each one carries load. |
| D8 | **Runtimes:** Python core (LangGraph) + a Node sidecar that hosts the official TypeScript reference engines (World Model, H-MEM). | Keeps the official conformance suites runnable. |
| D9 | **SAMPLE_MODE:** DuckDB over the committed `data/sample/` snapshot; LLM answers replayed from recorded cassettes, labelled `REPLAY` with hashes; deterministic code runs for real. | Judges have no Zetaris instance, no GPU and no keys. |
| D10 | **Frontend = React 18 + Vite + plain JavaScript**, Tailwind CSS, TanStack Table, Apache ECharts, React Router. | JS was required. This is the stack LLM coding tools know best (vibe-coding friendly). It is a static SPA with no server rendering to learn. ECharts handles 500-row heatmaps and treemaps. |
| D11 | **Architecture is modelled in OPM**, written as Graphviz DOT (`docs/architecture/opm/`), with OPL text. | One reviewable source of truth before modules are implemented. |
| D12 | **Repository language: English only** (code, comments, docs, commit messages, UI). | Public submission. |
| D13 | **Cost assumptions (one-way):** US 5 bp, EU 8 bp, crypto 15 bp. | Large-cap half-spread plus fees. These are assumptions, configurable in `config/tradepulse.toml`, and shown on every card. |

## Open items

| item | owner | how it closes |
|---|---|---|
| How Zetaris reads the lake files | D | D0: AWS + private S3 (recommended, D15) or a local mount; documented in `integrations/zetaris/DEPLOY.md`. |
| EDGAR `acceptanceDateTime` timezone | A | Compare 3 filings with their index pages. Record the result in `ingest/TASK.md`. |
| News-tone history coverage | A | Probe GDELT for a 1-year range on 3 tickers. |
| Meterless Nightshift Windows licence for participants | D (lead asks at onboarding) | Ask at onboarding. |
| NIM model choice for the analyst and skeptic roles (two different families) | D proposes, lead decides | Pick from the NIM catalogue. Record the choice in `.env.example`. |
