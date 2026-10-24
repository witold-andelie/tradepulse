# Zetaris registration SQL (task D1)

Write these files and run them with `py -3 -m integrations.zetaris.register`.

The registration runner exists; the SQL files and real registration evidence remain Member D's
delivery. See [current status](../../../docs/STATUS.md) and the integration TASK/ACCEPTANCE files.

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
- Write `<lake path>` as `${LAKE_PATH}`. The agreed live route is a private S3 lake exposed through
  `s3a://` paths on the AWS deployment (D15/D17). The runner substitutes the configured path;
  demonstrate access rather than assuming a local host mount is visible.
- The EDGAR REST table needs `ZETARIS_USER_AGENT` in the form `"app_name user@domain.tld"`. Write it
  as the placeholder `${ZETARIS_USER_AGENT}`. Never put a real address in the file.
