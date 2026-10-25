# Real-data delivery evidence

Decision date: **2026-10-23**. Collected independently by the lead after PR #5; this is real provider data, not a synthetic fixture.

## Snapshot and source tables

| Table | Lake rows | Sample rows | Sample bytes | Sample SHA-256 |
| --- | ---: | ---: | ---: | --- |
| filing | 9005 | 9005 | 312269 | `7a2b23b8e3516ad629225d1271923cbb5a9fcbf670c354db6fb29b731b3d909d` |
| filing_text | 2155 | 321 | 4209242 | `63444f64d2f13f86873a6b9e11f488671b57163c45f9611dff6da8119ab88033` |
| fundamental_fact | 250968 | 250968 | 2242092 | `dc2ce2c2af7d1a85344899720b7099b8016b1f498a46433aa786219d2046b04d` |
| macro_point | 564 | 564 | 13106 | `06f8852d10e198572ba96b0a21562b1b01660eea374584d42402c3c5b6df3ef7` |
| pageview | 463068 | 463068 | 986476 | `212d3b7ed9c2e3a14f2657de7ef10f1d048152b83393343b3416ee76aa28f39b` |
| price_bar | 342804 | 342804 | 7553889 | `74c97673f8315cde7169b3dff869f459227d7533209e19a8fa7256911edae121` |
| universe_member | 616 | 616 | 24671 | `b416bada4a50c4999ac117156ec17202939487c23305c9a3f0a39006125fb558` |

Seven table files: **15,341,745 bytes**. Complete sample, including provenance and metadata, remains below 25,000,000 bytes.
The sample has 300 distinct earnings documents, 302 earnings share-class rows and 19 annual rows. The document cap is not a row cap.

## Independent checks

- Complete Python suite: **595 passed, 0 failed, 0 errors, 0 skipped**. All eight real lake/sample cases ran.
- A clean export of the staged repository, without `.env`, provider caches or the production lake, passed **588 tests with 7 expected production-lake skips**. The committed sample test passed, all seven sample hashes matched, and external network connections were blocked with zero attempts. Windows loopback IPC remained available to the test runner. See [clean-checkout evidence](../data/sample/provenance/clean_checkout_validation.json).
- Modified ingestion implementation/tests passed Ruff 0.17.2. The old quant unused-noqa maintenance issue is outside this result.
- `py -3 -m ingest all --as-of 2026-10-23` completed using current provider caches plus live metadata/FRED reads and ended with `all tables valid`.
- Sample rows, contracts, date bounds and DuckDB views were checked with networking blocked; zero connections were attempted.
- Source contact addresses are redacted before canonical text length/hash calculation. 1567 full-lake text rows contain the redaction marker; publishable sample contact scans found zero addresses.

| Pool | Members | Members with titles/pageviews | Members meeting 95% price coverage |
| --- | ---: | ---: | ---: |
| crypto | 38 | 35 | 38 |
| eu_equity | 55 | 50 | 55 |
| us_equity | 523 | 517 | 523 |

- All US members have CIKs. All five required reference symbols are present.
- Earnings filings cover 513 companies and diluted-EPS facts cover 511 companies.
- Three saved filing timestamps match their original SEC index Accepted times. Live persistence uses index Eastern time converted to UTC; the raw-field Eastern hypothesis was disproved.
- Raw provider responses and full production lake/cache/logs are ignored local artifacts. Portable provenance and hashes are delivered with the sample.

## Explicit source limitations

Strict audit: **31/32 checks pass**, exit 1. The only failing check is `texts.earnings_complete`, with 35 missing exhibits. Every original index was independently verified to have no EX-99.1, EX-99.01 or EX-99 candidate. No placeholder text or fabricated document was inserted.

The team lead explicitly accepted the 35 verified source exceptions and authorized publication on 2026-10-25. This is a source-qualified release: the strict completeness flag remains false and the audit remains 31/32. The evidence is in [the source exception ledger](../data/sample/provenance/source_exception_verification.csv).

Original exhibit aliases: 199 rows ({'EX-99': 175, 'EX-99.01': 24}) retain source types/URLs and the canonical text hash in [normalization provenance](../data/sample/provenance/filing_text_normalization.csv).

Three crypto article titles remain unavailable; mapped titles can represent platform or issuer attention. This is a curated identity-reviewed pool, not an exact historical top-40 market-cap index. Supplemental CoinGecko detail collection stopped on HTTP 429; unavailable detail responses are not claimed as verified. Article/project identity sources are recorded in [crypto provenance](../config/universe/crypto_provenance.json).

Current constituents, revised adjusted-price/macro histories and day-level availability do not certify historical membership, original FRED vintages or a universal market-close cutoff. TSM has no selected 10-K; a foreign-form expansion was not invented.

## Complete offline product load

Run `2026-10-23-7560d397` completed with **0 network attempts**, returned a contract-valid RunOutput with 616 records, 33 factor cards and 9 explanations.
Measured factor states: `{'MEASURED_ONLY': 20, 'INSUFFICIENT_DATA': 13}`. Research stance counts: `{'NO_CALL': 616}`. The gates were not weakened to create an ACTIVE factor.
The matching model cassette is absent: 9 explanations abstained and 0 were explained. No model response was fabricated. This establishes data loading, deterministic execution, contracts and abstention; full model replay/sponsor acceptance remains separate.

The local ignored run and trace are named in [offline product evidence](../data/sample/provenance/offline_product_validation.json). D must record against this exact redacted-text sample and its hashes. Private S3 upload awaits a destination/access method.

## Reproduction and handoff

Use [OPERATIONS.md](OPERATIONS.md). Select `YAHOO_TRANSPORT=public_chart` for the observed collection path; the downloader crumb request was limited while the public chart/search requests returned HTTP 200. Requests retain contact identification, limits and timeouts.

The published manifest freezes table hashes. A changed source snapshot requires a fresh destination and refreshed provenance/model recordings; recutting different tables into the published destination is rejected.

No credentials, contact identities, original HTML bodies or production caches are included in the sample.

## Private handoff closure, 25 October

The complete production lake was packaged locally with reproducible `package` and
`verify-package` commands. The ZIP is **25,772,991 bytes** with SHA-256
`6c2104111d69c1ed901f2344096b2ffe1d1a961e0796d35eb73b6a5650f907da`.
All seven table payloads, allowlisted provenance, row counts, contracts and as-of bounds
were checked without extraction; a second verification blocked networking and observed
zero attempted connections. The archive preserves strict completeness as false and records
the source-qualified release. See [the safe receipt](../data/sample/provenance/private_handoff_validation.json)
and [A1–A9 closure map](DELIVERY.md).

The ingestion suite now has **128 passed**, with eight new offline handoff-policy/tampering
regressions and the same 19 parser deprecation warnings. All given tests are unchanged.
The seven published sample table hashes are unchanged. Its 14 pageview gaps are explicitly
listed in [gap provenance](../data/sample/provenance/pageview_gaps.csv).

No S3 destination or access delivery has been received from D. The ZIP remains private on
the collector; no cloud resources, upload, hosted query or model recording is claimed.
