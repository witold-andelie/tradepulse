# Data sources

Every source is public and free. No source needs an API key, but several require a contact
User-Agent (see `.env.example`). All data lands in `data/lake/` as parquet, following
`contracts/tables/`. Zetaris federates the lake. DuckDB reads the same files in SAMPLE_MODE.

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
- Price-volume, attention, spillover and regime work as for the other pools.
- Cross-pool edges carry European names into the relation graph. One example is semiconductor
  equipment suppliers linked to US chip makers.

## Point-in-time rules

- Prices: a bar dated `t` is available at that market's close. When pools are compared, the latest
  close at or before the decision time is used.
- Pageviews for day `t` are complete only after 00:00 UTC of `t+1`: `available_at = t+1 00:00 UTC`.
- EDGAR: a filing is available at its **acceptance time**. The `acceptanceDateTime` field in the
  submissions JSON carries a trailing `Z` but is believed to be US/Eastern clock time. `ingest/`
  must verify this against the filing index page and convert to UTC. A filing accepted after the
  16:00 New York close counts for the next trading day.
- Fundamental facts are available from their `filed` date, and only the first-reported value of a
  period is used.
- FRED values are revised. We use the series as downloaded and note the revision risk.

## Sponsor routing

- **Zetaris:** one `FILESTORE` table for each lake table (bulk queries), plus a `REST` table on EDGAR
  `companyconcept` for on-demand lookups of a ticker outside the universe. REST tables re-fetch on
  every query, so `CACHE TABLE` is issued right after registration.
  - **Open item:** how a local Docker install reads host files (volume mount path). The fallback is
    an S3-compatible bucket.
- **DuckDB:** runs the same templated SQL against `data/sample/` (SAMPLE_MODE) or `data/lake/`.
  Templates use only SQL that both Spark SQL and DuckDB accept.
