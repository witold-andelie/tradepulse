# Zetaris registration SQL (task D1)

Write these files and run them with `py -3 -m integrations.zetaris.register`.

| file | content |
|---|---|
| `01_create_database.sql` | `CREATE LIGHTNING DATABASE TRADEPULSE_LAKE DESCRIBE BY "TradePulse market data lake";` |
| `02_filestore_tables.sql` | One `CREATE LIGHTNING FILESTORE TABLE <name> FROM TRADEPULSE_LAKE FORMAT PARQUET OPTIONS (PATH "<lake path>/<name>.parquet");` per table in `contracts/tables/`, using the same table names |
| `03_edgar_rest.sql` | A `CREATE LIGHTNING REST TABLE` on `https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json`, followed by `CACHE TABLE ...;` |
| `04_smoke_select.sql` | `SELECT * FROM TRADEPULSE_LAKE.<name> LIMIT 5;` for every table |

Rules:

- One statement per block. End each with `;` and separate blocks with a blank line.
- Copy the option syntax from the working recipes in the Zetaris getting-started repo
  (`open_data/parquet_csv/sql/*_create.sql` and `open_data/rest_apis/sql/`).
  - A local copy lives at `D:\AI_Models\hackson\refs\zetaris\repo`.
- Write `<lake path>` as the placeholder `${LAKE_PATH}`. The runner substitutes the path the Zetaris
  container can see. How a local Docker install reads host files is still an open item (see
  `docs/architecture/decisions.md`).
- The EDGAR REST table needs `ZETARIS_USER_AGENT` in the form `"app_name user@domain.tld"`. Write it
  as the placeholder `${ZETARIS_USER_AGENT}`. Never put a real address in the file.
