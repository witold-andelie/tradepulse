# Member A — Data ingestion (`ingest/`)

> **Status (2026-10-24): A1–A7 and A9 code is implemented and merged.** Do not rebuild it.
> Member A's provider fixes and local evidence were preserved in PR #5 (merge `af229b4`).
> The lead has taken over follow-up fixes and remaining delivery; Member A is not assigned
> more implementation work. No lake or sample snapshot is present in the publication checkout,
> and the curated crypto CSV was excluded from #5. See `docs/STATUS.md` for dependencies.
> The following requirements remain owned by the lead, with Member D handling the upload destination:
>
> 1. **First live run.** Put a real contact e-mail in your `.env` (`SEC_USER_AGENT`,
>    `WIKIMEDIA_USER_AGENT`), then run `py -3 -m ingest all --as-of <latest trading day>`. Fix every
>    failure in `ingest/` and open PRs for the fixes.
> 2. **Data quality.** Read `data/lake/_reports/` and meet every number in `ACCEPTANCE.md`. List each
>    exception with its reason in your PR.
> 3. **Crypto universe.** Complete `config/universe/crypto.csv`: Yahoo symbols (some need numeric
>    suffixes), Wikipedia titles, about 40 assets, no stablecoins or wrapped tokens.
> 4. **EDGAR timezone check.** Compare 3 filings with their index pages and record the result in your PR.
> 5. **Sample snapshot (A9).** Run `py -3 -m ingest sample`, check that it is under 25 MB, and commit
>    `data/sample/`. Judges run the whole product from it.
> 6. **Upload the lake to S3** using the location and write-only credentials Member D sends you
>    privately. Never commit them.
> 7. **News-tone probe** (open item in `docs/architecture/decisions.md`): can GDELT give one year of
>    tone for 3 tickers? Report yes or no with evidence.

You build the **Market Data Lake**: every table the engine reads. The engine never calls the
internet itself. If your tables are correct, complete and point-in-time, the whole product works.
If they are wrong, every ranking is wrong.

- Architecture view: `docs/architecture/opm/svg/SD2_acquiring.svg` (blue boxes are yours).
- Contracts you must satisfy: `contracts/tables/*.json`, explained in `contracts/README.md`.
- Sources and point-in-time rules: `docs/architecture/data-sources.md`.

## What you own

```
ingest/
  __main__.py      CLI: py -3 -m ingest <command>
  net.py           polite HTTP: User-Agent, rate limit, retries
  universe.py      universe_member table
  prices.py        price_bar table
  pageviews.py     pageview table
  edgar.py         filing, fundamental_fact, filing_text tables
  macro.py         macro_point table
  lake.py          read/write parquet with contract validation
  sample.py        cut data/sample/ for SAMPLE_MODE
  tests/           acceptance tests (given; do not weaken them)
config/universe/   us_extras.csv, eu_extras.csv, crypto.csv (you complete crypto.csv)
data/sample/       committed sample snapshot (you produce it)
```

Do **not** edit `contracts/`, `tradepulse/`, `quant/` or `web/`. If a contract looks wrong, open an
issue for the team lead.

## Setup

```
py -3 -m pip install -e ".[ingest,dev]"
copy .env.example .env      # then put a real contact e-mail into SEC_USER_AGENT and WIKIMEDIA_USER_AGENT
py -3 -m pytest ingest -q   # offline tests; absent lake/sample cases skip until delivery
```

## Global rules

1. **Signatures are fixed.** The function names, arguments and return columns in the stubs are the
   contract the tests check. Maintain the existing implementations.
2. **Unit tests never touch the network.** Parse functions take already-downloaded text or JSON.
   Network code lives in separate `fetch_*` functions.
3. **Be polite to providers.** Every request goes through `net.build_session()` and a `RateLimiter`:
   - SEC: at most **8 requests/second** and a User-Agent with an e-mail address (SEC blocks
     clients without one).
   - Wikimedia: at most 50/second and a User-Agent with contact details.
   - Yahoo: download in batches of 50 symbols with a pause between batches.
4. **Retries:** 3 attempts with exponential backoff (1 s, 2 s, 4 s) on HTTP 429, on 5xx and on
   timeouts. Timeout is 30 s.
5. **Everything is UTC** except `date` columns, which are session dates.
6. **Validate before writing.** `lake.write_table()` must call
   `tradepulse.contracts.assert_table()` and refuse to write invalid data.
7. **No secrets in code or data.** The User-Agent e-mail comes from `.env`.
8. **English only** in code, comments, logs and commit messages.

## Existing implementation and remaining live acceptance

### A1 · Universe (`universe.py`) → `universe_member`

- **US pool:**
  - S&P 500 from https://en.wikipedia.org/wiki/List_of_S%26P_500_companies (table
    `id="constituents"`: Symbol, Security, GICS Sector, CIK).
  - Nasdaq-100 from https://en.wikipedia.org/wiki/Nasdaq-100 (table `id="constituents"`:
    Ticker, Company, GICS Sector). Its CIKs come from the SEC ticker map
    `https://www.sec.gov/files/company_tickers.json`.
  - Plus `config/universe/us_extras.csv`.
  - Deduplicate. `index_membership` joins the sources in this fixed order: `SP500|NDX|EXTRA`.
- **EU pool:** EURO STOXX 50 from https://en.wikipedia.org/wiki/EURO_STOXX_50 (the components
  table) plus `config/universe/eu_extras.csv`. Convert each ticker to its Yahoo symbol with
  `eu_yahoo_symbol()` using this exchange map:

  | exchange text contains | suffix |
  |---|---|
  | xetra, frankfurt, deutsche börse | `.DE` |
  | euronext paris, paris | `.PA` |
  | euronext amsterdam, amsterdam | `.AS` |
  | euronext brussels, brussels | `.BR` |
  | borsa italiana, euronext milan, milan | `.MI` |
  | bolsa de madrid, bme, madrid | `.MC` |
  | nasdaq helsinki, helsinki | `.HE` |
  | euronext dublin, dublin | `.IR` |
  | euronext lisbon, lisbon | `.LS` |

  An unknown exchange raises `ValueError`. Never guess a suffix.
- **Crypto pool:** complete `config/universe/crypto.csv` to about 40 assets by market cap.
  - Exclude stablecoins and wrapped or staked tokens.
  - Fill `yahoo_symbol`. Some coins need a numeric suffix on Yahoo; check each one returns data.
  - Fill `wikipedia_title`.
- **`wikipedia_title` for equities:** take the article link of the company name in the Wikipedia
  table. When no link exists, leave it null.
- **US symbols:** Yahoo uses `-` where Wikipedia uses `.` (`BRK.B` → `BRK-B`).

### A2 · Prices (`prices.py`) → `price_bar`

- Pull daily bars with `yfinance` for every pool member plus the reference symbols `SPY`, `^VIX`,
  `^VIX3M`, `^STOXX50E` and `BTC-USD`. Reference symbols use `pool="reference"`; `BTC-USD` is also
  stored in the crypto pool.
- Range: from `as_of - (window_days + warmup_days)` to `as_of` (values in
  `config/tradepulse.toml`).
- Use `auto_adjust=False`, so that both `close` and `adj_close` exist.
- Drop rows where `close` is missing. Never forward-fill prices.
- Write a **coverage report** (`data/lake/_reports/prices_coverage.csv`) with one row per symbol:
  rows, first date, last date, and the share of the pool's trading days present. Any symbol below
  95% coverage must be listed in the PR description.

### A3 · Pageviews (`pageviews.py`) → `pageview`

- Use the Wikimedia per-article daily pageviews with agent `user` and access `all-access`, over the
  same date range as the prices.
- `available_at` = the day after `date`, at 00:00 UTC.
- A 404 means the title is wrong. Log it in `data/lake/_reports/pageviews_missing.csv` and continue.

### A4 · Filings and facts (`edgar.py`) → `filing`, `fundamental_fact`

- Filing index: `https://data.sec.gov/submissions/CIK{cik10}.json`. Keep only the forms in the
  contract enum.
  - The `filings.recent` block holds up to about 1000 filings. That is enough for a one-year
    window, so ignore the older `files` pages.
- Facts: `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json`. Keep only the 4 tags listed
  in `contracts/tables/fundamental_fact.json`.
- **Timezone check (required):** the `acceptanceDateTime` field ends in `Z` but is believed to be
  US/Eastern clock time.
  - Open the filing index page of 3 filings and compare the times. The index page shows
    "Accepted" in Eastern time.
  - Write the result in the PR description.
  - `acceptance_to_utc()` implements the Eastern interpretation. If your check disproves it,
    tell the team lead before changing the test.

### A5 · Filing texts (`edgar.py`) → `filing_text`

- For every 8-K with item `2.02` inside the window, download exhibit `EX-99.1` (the earnings press
  release).
  - Find it in the filing index page (its table has a Type column):
    `https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_no_dashes}/{accession}-index.htm`.
    Parse it with `find_exhibit_url()`.
- For the showcase names in `config/graph/seed_edges.csv`, also download the latest 10-K primary
  document.
- `html_to_text()` must:
  - remove `<script>` and `<style>` content
  - decode HTML entities
  - collapse whitespace
  - truncate to 200 000 characters
- `sha256` is the hash of the final text.

### A6 · Macro (`macro.py`) → `macro_point`

- FRED CSV without a key: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2`.
  - Drop rows whose value is `.` (FRED's missing marker).
  - Accept either `DATE` or `observation_date` as the date header.

### A7 · Lake I/O and validation (`lake.py`, `__main__.py`)

- `write_table(df, name, root)` validates the frame, then writes `root/data/lake/<name>.parquet`.
- `py -3 -m ingest validate` validates every table present and prints a summary.
- `py -3 -m ingest all --as-of YYYY-MM-DD` runs A1 → A6 → validate in order.

### A8 · Hand-off to Zetaris (owned by Member D)

Member D registers your lake tables in Zetaris (`integrations/zetaris/`). Your part:

- Keep file names and columns exactly as in `contracts/tables/`. Zetaris reads the same files.
- When D asks, upload `data/lake/*.parquet` to the location D gives you, for example a private S3
  bucket, using credentials D shares privately. Never commit those credentials.

### A9 · Sample snapshot (`sample.py`) → `data/sample/` (committed)

SAMPLE_MODE runs from this folder alone, without internet access.

- It holds the same 7 tables, written by `write_table()` with `root` pointing at the sample folder.
- Contents:
  - all universe members
  - all prices and pageviews for the window plus warmup
  - US filings and facts
  - filing texts only for the showcase names and at most 300 EX-99.1 documents
- The total size must stay **below 25 MB**.

## Definition of done

See `ACCEPTANCE.md`. Open one PR per task or per pair of tasks. Branch names are `a/<task>`, for
example `a/a2-prices`.
