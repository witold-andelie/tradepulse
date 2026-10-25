# Real TradePulse sample

Decision date: 2026-10-23. This snapshot contains real provider data, not the synthetic
frontend fixture. Table identities and hashes are in manifest.json.

The seven Parquet tables occupy 15341745 bytes. The earnings selection contains
300 distinct documents and 302 share-class rows, plus 19 annual rows.
Public contact addresses were removed before text hashes and lengths were calculated.

Strict data audit: 31/32 checks passed. The strict earnings-text completeness check remains
false for 35 source filings with no permitted exhibit; each index was independently
verified and its hash/type list is preserved in provenance/source_exception_verification.csv.
The team lead accepted these source exceptions for release on 2026-10-25. Strict completeness
remains false; this is not an unconditional claim of complete source coverage.

All tables were queried through DuckDB with network connections blocked. A full three-pool
product load also completed without networking, producing 616 recommendation records;
9 explanations abstained because the matching model cassette is absent. No model answers
are fabricated. See provenance/offline_product_validation.json.

A clean repository export without credentials, provider caches or the production lake passed
588 tests, with only the seven production-lake tests skipped. The sample test passed and
no external network requests were attempted. See provenance/clean_checkout_validation.json.

Current membership, revised price/macro histories and day-level availability remain disclosed
limitations. No investment performance or successful sponsor deployment is established by this data check.

Rebuild commands and provider policies are in ../../ingest/OPERATIONS.md.
