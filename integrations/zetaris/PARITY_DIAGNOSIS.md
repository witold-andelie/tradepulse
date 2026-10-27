# Parity mismatch diagnosis: 27 October 2026

The lead reported 6/12 template matches at commit 6a2f71d. Live smoke passed, but three large
queries returned exactly 1,000 rows, and three smaller queries had equal counts with different
hashes. Engines and model-backed research were correctly not started.

## Exact timestamp-hash reproduction

Using the unchanged frozen sample on Windows, all three native DuckDB hashes equalled the
reported Zetaris hashes. Removing timezone information from UTC instants reproduced every
reported Mac DuckDB hash exactly:

| Template | Rows | Naive timestamp hash prefix (Mac report) | UTC hash prefix (Zetaris report) |
| --- | ---: | --- | --- |
| filing_texts_window | 128 | 2b11c3d7000d | c0939318385d |
| macro_window | 23 | acfba7a25814 | fa0ce55c2c06 |
| pageviews_symbol_window | 31 | 27909a70ff54 | bee9e7242411 |

Full observed hashes are locked into the regression harness. The local versions used in
reproduction were DuckDB 1.5.4 and pandas 2.2.3. The Mac's exact runtime versions are not yet
captured; the new parity report includes them.

The existing canonical hash deliberately treats naive datetimes as dates. That is correct
for contract date columns but loses the instant when a backend returns a contract datetime
without timezone information. Zetaris results already received contract type coercion;
DuckDB results did not. Both adapters now coerce result columns through the same unchanged
contract types before hashing. The hash function itself and source data are unchanged.

## Result truncation and completeness

Reported large-query counts:

| Template | DuckDB rows | Returned Zetaris rows |
| --- | ---: | ---: |
| facts_tag_window | 124,229 | 1,000 |
| pageviews_pool_window | 16,012 | 1,000 |
| price_pool_window | 12,545 | 1,000 |

The earlier client treated a response total equal to its returned rows as proof of completeness.
That cannot distinguish a complete result from a transport reporting only its capped slice.
Whether this deployment's 1,000 rows originate from the requested limit or a server-side cap
has not been independently established. A new report records request limits and response
totals without credentials or raw row data.

The live adapter now uses bounded ordinal pages over its allow-listed static lake templates.
Each page carries server-computed ROW_NUMBER and COUNT window metadata. It verifies contiguous
ordinals, stable total count and complete retrieval. It advances by the actual last ordinal,
so an API returning fewer rows than requested does not silently end retrieval. Metadata is
removed before contract coercion, hashing or delivery to the core.

Template ordering is preserved, with projected columns added as tie breakers. Fully identical
rows are retained. Empty results are verified using a scalar server count. Missing/repeated
ordinals, changing totals, premature empty pages and exhausted budgets fail explicitly.

Defaults: ZETARIS_PAGE_SIZE=1000, ZETARIS_MAX_PAGES=512 and ZETARIS_MAX_ROWS=500000. Existing
per-request timeouts and request-expansion limits still apply. These queries operate on frozen
file-source snapshots; this is not a transaction-isolation guarantee for concurrently changing
tables. Unsupported template shapes fail rather than being rewritten speculatively.

## Verification scope

Before the fix, the new seam regressions failed for capped retrieval and missing UTC timezone.
After the fix, all 22 new regressions passed. They include all 12 templates over the actual
frozen sample, through an explicitly simulated API that caps responses at 1,000 rows, reports
only the returned count and encodes non-null values as strings. Every template matched the
offline row count and hash. This is controlled local reproduction, not a live Zetaris result.

Re-run on the Mac before accepting the fix:

    python3 -m integrations.zetaris.parity --env-file ~/getting-started/.env.local --report runs/zetaris-parity-fixed.json

Set ZETARIS_API_MODE=proxy first. Choose a fresh report filename. Expect 12/12 matches with
full computed row counts, including 124,229 facts. Preserve failed reports and original source
files. Do not lower the row counts, relax hash assertions or start later stages on a mismatch.
