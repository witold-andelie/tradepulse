# Data sources

Every source is public and free. No source needs an API key, but several require a contact
User-Agent (see `.env.example`). The target landing area is `data/lake/` as parquet, following
`contracts/tables/`. Live Zetaris federation remains pending; the DuckDB implementation reads
the same table layout in SAMPLE_MODE. A real seven-table sample is committed under
`data/sample/`; the complete production lake and provider caches remain local/ignored.
See [current delivery status](../STATUS.md). The table below is a source plan, not a coverage report.

## Availability by pool

| data | us_equity | eu_equity | crypto | source | history for a 1-year backtest |
|---|---|---|---|---|---|
| universe (members, sector) | S&P 500 ∪ Nasdaq-100 + `config/universe/us_extras.csv` | EURO STOXX 50 + `config/universe/eu_extras.csv` | `config/universe/crypto.csv` (top ~40 by market cap, no stablecoins or wrapped tokens) | Wikipedia lists, curated CSV | current snapshot only → survivorship bias (disclosed) |
| daily OHLCV | ✓ | ✓ | ✓ | Yahoo Finance via `yfinance` | ✓ (fetch window + warmup) |
| reference series | SPY, ^VIX, ^VIX3M | ^STOXX50E | BTC-USD | Yahoo Finance | ✓ |
| pageviews (attention) | ✓ | ✓ | ✓ | Wikimedia REST pageviews API | ✓ (since 2015) |
| filings index (8-K items, 10-Q, 10-K) | ✓ | ✗ | ✗ | SEC EDGAR `submissions` JSON | ✓ |
| fundamental facts (EPS, revenue, shares) | ✓ | ✗ | ✗ | SEC EDGAR `companyfacts` JSON | ✓ (with `filed` dates) |
| filing texts (8-K EX-99.1, 10-K customers) | ✓ | ✗ | ✗ | SEC EDGAR archives | ✓ |
| HY OAS (credit stress) | shared | shared | shared | FRED `fredgraph.csv?id=BAMLH0A0HYM2` | ✓ |
| social (StockTwits, Reddit) | P1 | ✗ | P1 | public endpoints | ✗ recent messages only → MEASURED_ONLY |
| news tone | P1 | P1 | P1 | to be verified (GDELT DOC API covers a rolling window) | unverified |

Consequences for the European pool:

- Filing-based factors (`earn_sue`, `earn_demand_language`, `evt_drift`) and the valuation
  constraint are **not available**. Their cards show `INSUFFICIENT_DATA` for `eu_equity`, and the
  weights of the remaining factors are renormalised.
- Price-volume, attention and regime have the same definitions as the other pools. Spillover
  is currently an in-sample diagnostic excluded from walk-forward ranking.
- Cross-pool edges carry European names into the relation graph. One example is semiconductor
  equipment suppliers linked to US chip makers.

## Point-in-time rules

- Prices: a bar dated `t` is available at that market's close. When pools are compared, the latest
  close at or before the decision time is used.
- Pageviews for day `t` are complete only after 00:00 UTC of `t+1`: `available_at = t+1 00:00 UTC`.
- EDGAR: a filing is available at its **acceptance time**. Live ingestion uses the SEC filing
  index page's **Accepted** clock, localizes it to `America/New_York` (including daylight-saving
  time), and persists UTC. The earlier hypothesis that submissions JSON `acceptanceDateTime`
  values with a trailing `Z` should be read as New York wall time was disproved by source
  comparisons. The live collector replaces that legacy interpretation with the verified index
  time; it does not apply a second Eastern-to-UTC shift to a genuine UTC JSON timestamp.
  Three persisted sample timestamps match their original indexes; see
  [the verification ledger](../../data/sample/provenance/edgar_timezone_verification.csv).
  `acceptance_to_utc()` and the original synthetic parser fixtures retain the earlier wall-time
  interpretation for compatibility. They are not the authority for persisted live acceptance
  times. The collector uses `_accepted_from_index()` in `run_filings()`.
- The current date-only ingestion cutoff keeps information timestamps strictly before
  `as_of + 1 day at 00:00 UTC`, and date fields on or before `as_of`. It does **not** implement a
  16:00 New York market-close decision or shift every after-close filing to the next session.
  The UTC cutoff is an ingestion bound, not a universal cross-market execution-time guarantee.
- Fundamental facts are available from their `filed` date, and only the first-reported value of a
  period is used.
- FRED values are revised. We use the series as downloaded and note the revision risk.

## Sponsor routing

- **Zetaris:** one `FILESTORE` table for each lake table (bulk queries), plus a `REST` table on EDGAR
  `companyconcept` for on-demand lookups of a ticker outside the universe. REST tables re-fetch on
  every query, so `CACHE TABLE` is issued right after registration.
  - **Agreed deployment:** AWS with a private S3 lake and `s3a://` table paths (D15/D17).
    Europe was preferred; the lead accepted D's reported Ohio (`us-east-2`) fallback on
    25 October after unsuccessful EU/N. Virginia attempts. Deployment, table registration,
    live parity and access from Europe remain unverified D deliveries.
- **DuckDB:** runs the same templated SQL against `data/sample/` (SAMPLE_MODE) or `data/lake/`.
  Templates use only SQL that both Spark SQL and DuckDB accept.

Direct core Python runs read process environment variables; Docker Compose reads root `.env`.
Ingestion's contact-setting helper also reads the ignored root `.env`, without loading all
core/provider configuration into the process. Contact settings belong
in the environment or local ignored configuration, never in a committed report.
