# Zetaris local deployment and registered lake

The lead runs the downloaded Zetaris platform through Docker Desktop on the Mac.
This is the observed deployment, superseding the unfinished AWS plan. The official helper
successfully queried seven registered sample tables and returned pool membership totals.
TradePulse's own client and parity must still be run on that Mac before marking them accepted.

## Lake preparation

The original frozen source files remain in data/sample/data/lake. Spark rejected their
Parquet TIMESTAMP(NANOS,false) representation. Create separate compatible upload copies:

    python3 -m integrations.zetaris.prepare_parquet --source-root data/sample --output-dir runs/zetaris-upload

The helper casts nanoseconds to microseconds with Arrow's safe cast, checks exact cast-back
equality, writes Snappy Parquet and verifies read-back. A sub-microsecond value is an error.
It refuses to write onto a source path or overwrite existing output without --replace.
All seven current tables and 1,067,346 source rows passed this check on Windows.

## Actual UI registration path on the Mac

1. Open NDP File System and upload one compatible Parquet file to the root.
2. Move that file to /file-store. Repeat one file at a time.
3. In Data Explorer, select File Source & API and TRADEPULSE_LAKE.
4. Create Table: File store, Parquet, NDP File System, then the uploaded file.
5. Use the original contract table name. Repeat for all seven tables.
6. Check SHOW LIGHTNING TABLES and measured counts against data/sample/manifest.json.

On this deployment, direct /file-store uploads and a six-file batch failed. Individual root
uploads succeeded. Direct access to the driver's customer-data path was rejected by the GUI's
file-access boundary. Do not assume a host/container file path is an accepted file-source path.

The lead reports matching row counts for all seven tables and an official API response with
crypto 38, eu_equity 55 and us_equity 523. See the sanitized response fixture and the
[current sponsor evidence](../../docs/sponsors.md).

## Application verification

Use the UI-proxy channel matching the working official helper. Run the service smoke and
all-template parity described in [MAC_LIVE_SETUP.md](../MAC_LIVE_SETUP.md). Configure the
API key and organization ID privately; do not put them in commands that print their values.
No changes to the contracts or source Parquet files are needed.

The registration SQL runner remains available for a separately verified deployment recipe.
This UI registration does not certify an AWS/S3 setup, idempotent SQL registration or the
optional EDGAR REST-table extension.
