# Member A ingestion operations

## Scope and status

PR #5 (merge `af229b4`) preserves Member A's provider fixes and historical evidence. The lead
has now independently collected a new real lake, crypto CSV and seven-table sample for
2026-10-23. See REAL_DATA_EVIDENCE.md and data/sample/manifest.json for current measured results.
The strict audit is 31/32: all 35 missing-exhibit indexes were independently checked and have
no permitted candidate. The lead accepted these source exceptions for release on 2026-10-25.
Preserve the strict failure separately from exception-qualified acceptance.

The lead follow-up fixes acceptance coverage to use current bars instead of a cached CSV,
retains missing crypto article mappings as explicit gaps, and limits sample exhibits by
document keys while keeping all attached share classes. Eleven new offline regressions cover
these cases; existing tests and shared table contracts are unchanged.

## Environment

Use Python 3.11 or later. The review ran on Python 3.12 with dependencies recorded in
requirements-tested.txt. This file records the tested environment; shared pyproject.toml is
unchanged. On Windows replace python with py -3.

```sh
python -m pip install -e ".[ingest,dev]"
# Optional dependencies needed by the complete repository suite:
python -m pip install -e ".[agent]" httpx
python -m pytest -q
```

Supply genuine SEC_USER_AGENT and WIKIMEDIA_USER_AGENT settings in a local ignored .env.
Never print or commit contact details. Explicit environment settings take precedence. The
simple local loader handles quotes/export without executing or interpolating shell expressions.
Syntax checks reject empty/example identities but cannot establish ownership of a real address.

```sh
python -m ingest config
python -m ingest smoke --as-of 2026-10-23
```

Smoke probes make small real requests before a deliberate bulk acquisition. Do not confuse
historical cached smoke results with proof of current provider availability.

## Acquisition and offline checks

```sh
python -m ingest universe --as-of 2026-10-23
python -m ingest prices --as-of 2026-10-23
python -m ingest pageviews --as-of 2026-10-23
python -m ingest filings --as-of 2026-10-23
python -m ingest texts --as-of 2026-10-23
python -m ingest macro --as-of 2026-10-23
python -m ingest validate --as-of 2026-10-23
python -m ingest sample --as-of 2026-10-23
python -m ingest audit --as-of 2026-10-23
python -m pytest ingest -q -m lake
python -m pytest ingest/tests/test_lake_and_sample.py::test_sample_snapshot_is_complete_and_valid -q
```

`all` runs acquisition then validation; it does not publish a sample, register services or upload
anything. Failed upstream stages block dependent stages while independent macro work continues.
`validate` checks table contracts and rejects empty tables. `audit` additionally recomputes
coverage from current bars and benchmark calendars, checks text integrity/completeness and
evidence, and fails coverage when a required benchmark calendar is absent. A cached coverage
CSV is not acceptance evidence. `handoff` generates the same local audit/manifest;
it is not an upload. The lead's fresh snapshot audit exited 1: 35 earnings filings had no
allowed exhibit, although exception accounting passed. All 35 indexes were independently
checked; retain the strict failure separately from any exception-qualified result.
The sample CLI validates the complete source lake against its requested --as-of before cutting;
missing, empty or future-dated source tables block publication. Audit the published snapshot
against that same decision date afterwards.

## Fresh collection through final delivery

The real sample is delivered for decision date 2026-10-23. The following sequence rebuilds it
from public sources. Configure the two contact settings in the ignored .env before provider
requests; configuration checks never print them. The collector's yfinance 1.4.1 session crumb
request returned HTTP 429 while Yahoo's public chart returned HTTP 200. This collection uses
the explicit public transport below, with the same bounded requests and source provider.

```powershell
$env:YAHOO_TRANSPORT = "public_chart"
py -3 -m ingest smoke --as-of 2026-10-23
py -3 -m ingest crypto-research --as-of 2026-10-23
py -3 -m ingest crypto-verify --as-of 2026-10-23
py -3 -m ingest config
py -3 -m ingest all --as-of 2026-10-23
py -3 -m ingest timezone --as-of 2026-10-23
py -3 -m ingest validate --as-of 2026-10-23
py -3 -m ingest sample --as-of 2026-10-23
py -3 -m ingest audit --as-of 2026-10-23
py -3 -m pytest ingest -q -m lake
py -3 -m pytest ingest/tests/test_lake_and_sample.py::test_sample_snapshot_is_complete_and_valid -q
```

Run stages in order, inspect each exit status, and stop acquisition when a provider blocks it.
Do not turn an audit failure into a success flag. Review every missing exhibit against its
source before presenting any exception-qualified result; retain the strict result separately.
Fresh crypto research writes empty candidate lists explicitly, and verification can refine
missing cells from older reports without inventing a ticker or article.

Module delivery includes the reviewed crypto CSV, seven real sample tables, recorded
decision date, recomputed coverage, provenance, table hashes and an explicit exceptions record.
All eight artifact-dependent tests execute without skips on the collector. A clean export
passes the sample test and skips only the seven absent production-lake cases. Local DuckDB reads and a complete
three-pool product load were verified with networking blocked. The run produced 616 NO_CALL
records and nine abstained explanations; no ACTIVE factor or model answer was invented.
Fully explained product replay additionally needs D's cassette recorded against the exact
delivered text hashes and core integration acceptance.
S3 upload follows only when D supplies a private destination and access method.

## Local artifacts and sharing

- Production lake: data/lake/<table>.parquet; ignored, not proposed for Git.
- Cached provider bodies: data/cache/; ignored.
- Quality/provenance reports and handoff_manifest.json: data/lake/_reports/; ignored.
- Current portable measured summary: ingest/REAL_DATA_EVIDENCE.md; PR_EVIDENCE.md preserves the author's earlier evidence.
- Commit-eligible sample: data/sample/data/lake/<table>.parquet; seven files, below 25 MB.

Member D must supply a private destination/access method before an authorized upload. Keep
credentials in local configuration. No service registration or upload has been executed.
Original lake bodies, logs, cache, environment files and complete backups must stay local.

## Provider and data policies

- HTTP uses build_session and RateLimiter, including redirect transport sends, with 30-second
  timeouts and at most three configured attempts. SEC workers share the same eight-per-second
  limiter. Yahoo downloads use batches of 50 and disable its extra configurable retry layer
  while the shared transport owns the retry budget, restoring the setting afterwards.
- The observed yfinance 1.7.0 accepts requests.Session. Other releases, especially curl-only
  variants, need verification rather than bypassing the shared request policy.
- `YAHOO_TRANSPORT=public_chart` selects the public daily-chart transport. It preserves the
  provider's adjusted closes and exchange-local dates, caches valid responses and stops on
  provider errors. The default yfinance transport and original tests remain available.
- Wikipedia Nasdaq constituents are followed to the linked dedicated article. Missing GICS
  sectors use official CNDX holdings labels with provenance; ICB is not silently relabelled.
- The live SEC path reads each selected filing's index Accepted time, localized to
  America/New_York and converted to UTC. The legacy pure parser remains unchanged; independent
  source verification and synchronization of the shared policy remain lead-owned.
- EX-99 and EX-99.01 normalization preserves #5's index/body evidence policy. Freshly collected
  original types, URLs and canonical hashes are in sample provenance; missing exhibits stay
  explicit exceptions and strict completeness remains false.
- Publishable filing text removes contact addresses before calculating text length and SHA-256.
  Original source bodies stay in ignored collector caches. Given pure HTML-parser assertions
  are unchanged; the privacy transform applies to persisted research text.
- Date filtering respects the following UTC midnight, rather than guaranteeing every market's
  close-specific availability. Pageviews and FRED data available next midnight are excluded
  on the as_of day. Current membership is not backdated; FRED vintage risk remains.
- Prices are never forward-filled. Coverage uses benchmark calendars and the tested denominator
  after the first observed bar. Recently listed members and European holiday differences need
  interpretation; coverage alone does not prove complete historical membership.
- Crypto identifiers and article existence have real-source review. Some titles are issuer or
  platform attention proxies; three remain null. This is a curated pool, not an exact top-40.
- Samples select at most 300 distinct earnings documents, retaining every share-class row for
  those document keys. They stage and size-check all outputs before publication. Individual
  file replacement is atomic, but publication of all seven files is not one transaction;
  avoid concurrent readers.
- Once manifest.json freezes a published sample, cutting different table hashes into that
  destination is rejected before replacement. Use a fresh destination for a new release and
  regenerate provenance and matching model recordings. Identical table hashes remain reusable.

## Additional commands

`coverage` recomputes the report from existing bars. `timezone` compares three saved filings
with their index Accepted times. `crypto-research` and `crypto-verify` curate and verify source
identifiers; the latter writes the owned crypto configuration. `sectors` checks issuer labels.
`diagnose` stores small public diagnostic bodies locally. `news-probe` performs the separate
bounded GDELT availability experiment; `news-report` summarizes stored responses. See
GDELT_PROBE.md for the three successful year-spanning probes and their explicit calendar gaps.
