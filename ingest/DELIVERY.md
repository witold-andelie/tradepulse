# Member A delivery closure — 25 October 2026

Decision date: **2026-10-23**. This is the current A1–A9 acceptance map; original contributor
history and the published sample table hashes are preserved. The lead accepted the verified
source exceptions for a source-qualified release. Strict completeness remains false.

| Task | Delivered state | Evidence and remaining qualification |
| --- | --- | --- |
| A1 Universe | 523 US, 55 EU and 38 crypto members; all US CIKs present; curated exclusion/identity review supplied | Frozen universe table, `config/universe/crypto.csv` and crypto provenance. Current membership is not a historical membership reconstruction. |
| A2 Prices | All 616 members meet the 95% coverage threshold; all five reference symbols present | Current-bar audit and frozen price table. Public-chart transport preserves provider adjusted closes and exchange-local session dates. |
| A3 Pageviews | Member coverage is 517/523 US, 50/55 EU and 35/38 crypto | The 14 missing mappings/observation records are listed in `data/sample/provenance/pageview_gaps.csv`. Missing rows are not fabricated. |
| A4 Filings/facts | Earnings filings cover 513 companies; diluted-EPS facts cover 511; index-based UTC verified on three source filings | Frozen tables and `edgar_timezone_verification.csv`. Shared legacy timezone wording still needs the lead's reviewed correction. |
| A5 Filing texts | 2155 full-lake rows; canonical text lengths/hashes and privacy normalization verified | 35 SEC indexes have no permitted exhibit, independently documented and accepted as source exceptions. Strict completeness is 31/32, not 32/32. TSM has no selected 10-K; no foreign form was invented. |
| A6 Macro | 564 valid FRED observations delivered | Frozen macro table. Revised histories are disclosed; original vintages are not reconstructed. |
| A7 Lake/validation | Seven nonempty contract-valid tables and reproducible audit/validation commands | Final ingestion suite: **128 passed**, including all real lake/sample cases and eight private-handoff regressions; 19 existing parser deprecation warnings. Changed files pass Ruff. |
| A8 Private handoff | Full-lake package built and independently verified locally; packaging and verification CLI delivered | **Upload is not done. Member D has supplied no S3 destination or access delivery.** No cloud resources were created and no upload was attempted. |
| A9 Sample | Seven frozen real tables, 300 distinct earnings documents / 302 share-class rows plus 19 annual rows; below 25 MB | Sample manifest, portable provenance, offline DuckDB/product checks and clean-checkout checks. The missing model cassette is D's integration dependency. |

The separate GDELT experiment is also delivered: three year-spanning daily series with
345 observations each and 20 calendar gaps each. These are availability probes, not a new
news factor or gap-free annual coverage. See `GDELT_PROBE.md`.

## Private archive receipt

- File: `tradepulse-lake-2026-10-23-20261025T122858Z.zip`
- Size: **25,772,991 bytes**
- SHA-256: `6c2104111d69c1ed901f2344096b2ffe1d1a961e0796d35eb73b6a5650f907da`
- Local folder: `D:/AI_Models/hackson/.work/`; the ZIP remains outside Git.
- The archive contains all seven complete production Parquet tables, the strict audit and
  allowlisted source evidence, plus the exact published sample reference manifest. Table
  files are copied byte-for-byte. Raw provider bodies, caches, credentials, contacts and logs
  are excluded.
- Archive membership, table hashes, sizes, rows, contracts and decision-date bounds were
  verified without extracting files. A second verification blocked all network connections;
  **zero network attempts** occurred. Safe evidence is committed as
  `data/sample/provenance/private_handoff_validation.json`.

Reproduce and verify from the repository root:

```powershell
py -3 -m ingest package --as-of 2026-10-23 --output "D:\AI_Models\hackson\.work\tradepulse-lake-new.zip" --allow-source-exceptions
py -3 -m ingest verify-package --archive "D:\AI_Models\hackson\.work\tradepulse-lake-new.zip"
```

Choose a new output file; existing files are never overwritten. The source-exception flag is
an explicit opt-in to the already documented source-qualified release, not a way to bypass
other failed acceptance checks. The strict flag stays false. Private full-lake archives are
refused inside the public sample folder. Verification checks hashes and contracts, not cloud
delivery or hosted query parity; an archive's external SHA-256 must match the receipt above.

The remaining external action is for D/the lead to supply the actual private bucket/prefix
and permitted access method, then upload and verify the seven files there. The original A8
`handoff` command remains a local audit, not an upload. Model recording, Zetaris registration,
hosted parity and engines integration belong to D/the lead, not another A collection pass.
