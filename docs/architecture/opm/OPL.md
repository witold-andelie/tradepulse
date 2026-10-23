# OPL — Object-Process Language for the TradePulse model

OPL is the text twin of the OPM diagrams. Every sentence below corresponds to one link in a
`.dot` file in this folder. If a diagram and this file disagree, fix both in the same PR.

Owner tags: **[core]** team lead · **[A]** `ingest/` · **[B]** `web/` · **[C]** `quant/` ·
**[D]** `integrations/`. Every sponsor instrument (Zetaris / DuckDB adapter, World Model, H-MEM,
NVIDIA NIM chain) is implemented by **[D]**.

## SD0 · System diagram (`SD0_system.dot`)

- **TradePulse** exhibits **Recommending**.
- **Customer** handles **Requesting**. **Requesting** requires **Web App** and yields **Analysis Request**. [B]
- **Acquiring** requires **Public Data Providers** and affects **Market Data Lake**. [A]
- **Recommending** consumes **Analysis Request**. [core]
- **Recommending** requires **Market Data Lake**, **Zetaris**, **Meterless** (World Model and H-MEM engines) and **NVIDIA NIM** (every LLM role, decision D18).
- **Recommending** yields **Recommendation Report** and **Trace Log**, and affects **Track Record**.
- **Customer** handles **Browsing**. **Browsing** requires **Web App**, **Recommendation Report**,
  **Track Record** and **Trace Log**. [B]

## SD1 · Recommending in-zoomed (`SD1_recommending.dot`)

**Recommending** zooms into **Guarding Request**, **Settling**, **Extracting & Linking**,
**Researching Factors**, **Assessing Regime**, **Ranking**, **Explaining** and **Reporting**,
in that sequence.

- **Guarding Request** affects **Analysis Request** from *raw* to *validated* or *rejected*, and
  requires **NVIDIA NIM** (guard role). A request to place, route or size real orders is rejected.
- **Settling** changes **Recommendation Memory** from *pending* to *settled*, requires
  **Market Data Lake** and affects **Track Record**. (SD1.2)
- **Extracting & Linking** requires **Market Data Lake** and **NVIDIA NIM**, yields
  **Structured Events** and affects **Relation Graph**. (SD1.3)
- **Researching Factors** requires **Market Data Lake**, **Structured Events**, **Relation Graph** and
  **Zetaris / DuckDB**, and yields **Factor Panel** and **Factor Cards**. (SD1.4)
- **Assessing Regime** requires **Market Data Lake** and yields **Regime State**. (SD1.5)
- **Ranking** requires **Factor Panel**, **Factor Cards**, **Regime State** and **Analysis Request**,
  and yields **Ranked Book** and **Focus List**. (SD1.5)
- **Explaining** consumes **Focus List**, requires **Ranked Book**, **Zetaris / DuckDB** and
  **NVIDIA NIM**, and yields **Explanation Set**. (SD1.7)
- **Reporting** consumes **Ranked Book** and **Explanation Set**, yields **Recommendation Report**,
  and yields **Recommendation Memory** in state *pending*.
- Every subprocess of **Recommending** yields events into **Trace Log**.

## SD1.2 · Settling (`SD1.2_settling.dot`)

- **Loading Matured Recommendations** requires **Recommendation Memory** in state *pending*
  (entry date + horizon <= as_of). [core]
- **Scoring Outcomes** requires **Price Bars** and **quant.settlement**, and changes
  **Recommendation Memory** to *settled*. [C functions, core wiring]
- **Updating Track Record** affects **Track Record**. [core]
- **Detecting Conflicts** requires **Recommendation Memory** and yields **Conflict Notes**. [core]

## SD1.3 · Extracting & Linking (`SD1.3_extracting_linking.dot`)

- **Selecting New Documents** requires **Filing Texts** and **Extraction Cache**. Documents whose
  sha256 is already cached are skipped.
- **Extracting Events** requires **NVIDIA NIM** (extractor role) and yields **Structured Event** in state *raw*.
- **Grounding Check** changes **Structured Event** from *raw* to *validated* or *rejected*. It is
  deterministic: the JSON matches the schema, every quoted span occurs verbatim in the document,
  and `available_at` is not earlier than the document's own timestamp.
  **Grounding Check** invokes **Extracting Events** once more when the event is rejected.
- **Proposing Edges** requires validated **Structured Events** and **NVIDIA NIM**, and yields
  **Candidate Edge** in state *proposed*.
- **Validating Edges** requires **Price Bars** and **Lead-Lag Test**, and changes **Candidate Edge**
  to *validated* or *rejected*. It invokes **Proposing Edges** again with the rejection reasons
  while fewer than 3 rounds have run.
- **Committing to World Model** requires **Seed Edges** and validated **Structured Events**,
  consumes validated **Candidate Edges**, and affects **Relation Graph** (append-only,
  `valid_from = as_of`).

## SD1.4 · Researching Factors (`SD1.4_researching_factors.dot`)

- **Computing Raw Factors** requires **Market Data Lake**, **Structured Events**, **Relation Graph**,
  **Zetaris / DuckDB** and **quant library**, and yields **Factor Panel** in state *raw*. [C + core]
- **Standardising** changes **Factor Panel** from *raw* to *standardised*. [C]
- **Residualising vs Price-Volume Baseline** changes **Factor Panel** from *standardised* to
  *residualised*. [C]
- **Evaluating** requires residualised **Factor Panel**, forward returns from **Market Data Lake**,
  **Gate Thresholds & Costs** and **quant library**, and yields metrics on **Factor Card**. [C]
- **Gating** requires **Gate Thresholds & Costs** and sets **Factor Card** to *ACTIVE*,
  *MEASURED_ONLY* or *INSUFFICIENT_DATA*. [core]
- **Weighting** requires **Factor Cards** in state *ACTIVE* and yields **Factor Weights**. [core]

## SD1.5 · Assessing Regime & Ranking (`SD1.5_regime_ranking.dot`)

- **Computing Fragility Indicators** requires **Market Data Lake** and yields
  **Fragility Indicators**. [C]
- **Classifying Regime** requires **Fragility Indicators** and **Tier & Cost Rules**, and yields
  **Regime State** (*normal*, *elevated* or *stressed*). [core]
- **Combining Scores** requires **Factor Panel** and **Factor Weights**, and yields **Ranked Book**
  in state *scored*.
- **Estimating Expected Alpha** and **Subtracting Round-Trip Cost** affect scored **Ranked Book**. [C math]
- **Assigning Tiers** changes **Ranked Book** from *scored* to *tiered*.
- **Applying Regime Overlay** requires **Regime State** and changes **Ranked Book** from *tiered* to
  *regime-overlaid*.
- **Selecting Focus Names** requires **Ranked Book** and **Analysis Request**, and yields **Focus List**.

## SD1.7 · Explaining (`SD1.7_explaining.dot`)

This runs once per focus name, in parallel (LangGraph `Send`).

- **Attributing** consumes **Focus Name** and requires the **Ranked Book row**. It is deterministic.
- **Gathering Evidence** requires **Zetaris / DuckDB** and **World Model**, and yields
  **Evidence Bundle**. Only allow-listed, templated queries are used; each bundle stores its query,
  its parameters and the sha256 of the returned rows.
- **Analyst role** handles **Drafting Claims**. **Drafting Claims** requires **Evidence Bundle** and
  yields **Claim** in state *drafted*.
- **Skeptic role** handles **Challenging**. **Challenging** requires drafted **Claims** and yields
  **Counter-case**.
- **Verifying Claims** requires **Evidence Bundle** and **Zetaris / DuckDB**, and changes **Claim**
  to *verified* or *rejected*. It re-runs the query and compares hashes, checks that the cause is
  dated before the move, checks that contributions sum to the score, and checks that no data after
  as_of was used. It invokes **Drafting Claims** with the failure reasons while fewer than 2 retries
  have run.
- **Composing Explanation** consumes verified **Claims** and **Counter-case**, and yields
  **Explanation**. With no verified claim it abstains: the explanation states "insufficient evidence".

## SD2 · Acquiring (`SD2_acquiring.dot`) — [A], except Registering in Zetaris [D]

**Acquiring** zooms into **Building Universe**, **Fetching Prices**, **Fetching Pageviews**,
**Fetching Filings & Facts**, **Fetching Filing Texts**, **Fetching Macro**, **Validating Contracts**,
**Registering in Zetaris** and **Cutting Sample Snapshot**.

- **Market Data Lake** consists of **Universe Members**, **Price Bars**, **Pageviews**, **Filings**,
  **Fundamental Facts**, **Filing Texts** and **Macro Points**.
- **Validating Contracts** requires **Table Contracts** and yields **Coverage Report**. It invokes
  **Fetching Prices** again (at most 2 times) when a contract is violated.
- **Registering in Zetaris** affects **Zetaris** (FILESTORE tables for every lake table, plus a REST
  table for on-demand EDGAR lookups).
- **Cutting Sample Snapshot** yields **Sample Snapshot**, which is committed and used by SAMPLE_MODE.

## SD3 · Browsing (`SD3_browsing.dot`) — all [B]

- **Loading Run Output** requires **HTTP API**. When no API is configured it requires
  **Contract Fixtures**. It yields **Run Output** with `data_mode` *REAL*, *REPLAY* or *SYNTHETIC*.
- **Validating Against Contract** requires **Run Output** and yields **Data-mode Banner**.
- **Customer** handles **Rendering Pages**, which yields **Web App Pages**. **Web App Pages**
  consists of **Leaderboard**, **Ticker Detail**, **Factor Lab**, **Regime**, **Track Record** and
  **Run Trace**.
- **Customer** handles **Requesting a New Run**, which affects **HTTP API**.
