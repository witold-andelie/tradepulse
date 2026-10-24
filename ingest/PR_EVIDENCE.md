# PR evidence: Member A real ingestion

Integration note: PR #5 was merged as code integration in `af229b4` at the lead's explicit
request. The lead owns subsequent fixes and outstanding artifact/source acceptance. This
document preserves the author's local evidence; its reported results are not a new independent
verification or a delivery of the excluded datasets. See `../docs/STATUS.md` for current checks.

Review date: 2026-10-24. Dataset decision date: 2026-10-23.

This is a computed summary of existing real provider datasets. This review did not refresh
bulk providers or rerun `ingest all`. Local production lake and cache bodies are excluded from
Git. This submission is ingest-only: neither the sample nor the curated crypto CSV is included;
the numbers and sample hashes below are evidence of local validation, not artifact delivery.

## Dataset and acceptance evidence

| Table | Lake rows | Sample rows | Sample SHA-256 |
| --- | ---: | ---: | --- |
| filing | 9005 | 9005 | 0900dcfe43b8cb679bcf9771ef3584523b66c2f0ed28593de6e534c25a9ff219 |
| filing_text | 2155 | 319 | a0f0d164e2249a93a901a0b2f0868b0280f56edc6281e89575d119fd38738538 |
| fundamental_fact | 250968 | 250968 | d8cf56b2f32202457de653d2582480eb67a83b2ae322e568159973c77e575204 |
| macro_point | 564 | 564 | 72d10533719c2cba924899e05d70a1ea901314f5c88e6feace4d8bfa749a23a1 |
| pageview | 463068 | 463068 | 2a6050a6e83e10e7c7e165e8bfbd9d88f422e517c771de66fe840af1d6581fca |
| price_bar | 342804 | 342804 | 774c8f324cb88d06ab4b5ec8bdc32e4ed979d1f1d013b2ae7c3de2ae987a0c2e |
| universe_member | 616 | 616 | 425c56c532945e3652652eb562f0a7153cca35e31297632f7d24e2f9d1f3c4be |

Sample total: 15309037 bytes (14.599835 MiB); below both 25 MB and 25 MiB.

| Pool | Members | Article/pageview members | Members meeting >=95% price coverage |
| --- | ---: | ---: | ---: |
| us_equity | 523 | 517 (98.8528%) | 523/523 |
| eu_equity | 55 | 50 (90.9091%) | 55/55 |
| crypto | 38 | 35 (92.1053%) | 38/38 |

All US rows have CIKs. All five required reference symbols are present. Earnings filings
cover 513 companies; diluted EPS facts cover 511 companies. Text hashes have zero mismatches.
Every earnings text exceeds 500 characters. All seven lake and sample tables validate against
existing contracts with as_of=2026-10-23. All 616 member coverage ratios were independently
recomputed from the real bars and benchmark calendars and match the stored report.

Audit: **31/32 pass, exit 1**. The only failed check is strict
`texts.earnings_complete`: 35 missing exhibits. All 35 have explicitly approved source exceptions,
and the separate accounted-with-exceptions check passes with zero unresolved requests. The
strict acceptance flag remains false; the exception-qualified flag is true. These flags do not
constitute team-lead merge approval. Task A5 requires an explicit exception disposition.

## Approved normalization provenance

199 canonical EX-99.1 rows were normalized only after index type and body evidence checks:
175 original EX-99 and 24 original EX-99.01. Original types and URLs remain in the ignored
local filing_text_normalization.csv. This PR does not change the shared enum.

## Three index Accepted comparisons

The following persisted timestamps were rechecked against actual cached SEC index bodies;
no fresh SEC request was needed. Index Eastern times convert back to the saved UTC values.

| Symbol | Accession | Saved UTC | Index Accepted Eastern | Match |
| --- | --- | --- | --- | --- |
| TDY | 0001094285-26-000059 | 2026-10-23T21:19:18+00:00 | 2026-10-23T17:19:18-04:00 | yes |
| DRI | 0000940944-26-000060 | 2026-10-23T20:55:12+00:00 | 2026-10-23T16:55:12-04:00 | yes |
| BAC | 0001193125-26-430566 | 2026-10-23T20:41:47+00:00 | 2026-10-23T16:41:47-04:00 | yes |

The original raw submissions interpretation was disproved during live collection. The user
approved index Accepted as canonical. The pure legacy parser and existing assertions remain
unchanged; the shared policy description needs a lead-reviewed follow-up.

## Explicit source exceptions

| Symbol | Accession | Source index |
| --- | --- | --- |
| EQT | 0000033213-26-000005 | [SEC index](https://www.sec.gov/Archives/edgar/data/33213/000003321326000005/0000033213-26-000005-index.htm) |
| EQT | 0000033213-26-000022 | [SEC index](https://www.sec.gov/Archives/edgar/data/33213/000003321326000022/0000033213-26-000022-index.htm) |
| EQT | 0000033213-26-000035 | [SEC index](https://www.sec.gov/Archives/edgar/data/33213/000003321326000035/0000033213-26-000035-index.htm) |
| EQT | 0000033213-26-000046 | [SEC index](https://www.sec.gov/Archives/edgar/data/33213/000003321326000046/0000033213-26-000046-index.htm) |
| CVX | 0000093410-26-000108 | [SEC index](https://www.sec.gov/Archives/edgar/data/93410/000009341026000108/0000093410-26-000108-index.htm) |
| NEE | 0000753308-26-000004 | [SEC index](https://www.sec.gov/Archives/edgar/data/753308/000075330826000004/0000753308-26-000004-index.htm) |
| WEC | 0000783325-26-000006 | [SEC index](https://www.sec.gov/Archives/edgar/data/783325/000078332526000006/0000783325-26-000006-index.htm) |
| EOG | 0000821189-26-000012 | [SEC index](https://www.sec.gov/Archives/edgar/data/821189/000082118926000012/0000821189-26-000012-index.htm) |
| EOG | 0000821189-26-000078 | [SEC index](https://www.sec.gov/Archives/edgar/data/821189/000082118926000078/0000821189-26-000078-index.htm) |
| EOG | 0000821189-26-000140 | [SEC index](https://www.sec.gov/Archives/edgar/data/821189/000082118926000140/0000821189-26-000140-index.htm) |
| EOG | 0000821189-26-000202 | [SEC index](https://www.sec.gov/Archives/edgar/data/821189/000082118926000202/0000821189-26-000202-index.htm) |
| REGN | 0001104659-26-040661 | [SEC index](https://www.sec.gov/Archives/edgar/data/872589/000110465926040661/0001104659-26-040661-index.htm) |
| REGN | 0001104659-26-080562 | [SEC index](https://www.sec.gov/Archives/edgar/data/872589/000110465926080562/0001104659-26-080562-index.htm) |
| REGN | 0001104659-26-113895 | [SEC index](https://www.sec.gov/Archives/edgar/data/872589/000110465926113895/0001104659-26-113895-index.htm) |
| BIIB | 0000875045-26-000003 | [SEC index](https://www.sec.gov/Archives/edgar/data/875045/000087504526000003/0000875045-26-000003-index.htm) |
| BIIB | 0000875045-26-000039 | [SEC index](https://www.sec.gov/Archives/edgar/data/875045/000087504526000039/0000875045-26-000039-index.htm) |
| BIIB | 0000875045-26-000068 | [SEC index](https://www.sec.gov/Archives/edgar/data/875045/000087504526000068/0000875045-26-000068-index.htm) |
| GS | 0000886982-26-000004 | [SEC index](https://www.sec.gov/Archives/edgar/data/886982/000088698226000004/0000886982-26-000004-index.htm) |
| EBAY | 0001065088-26-000205 | [SEC index](https://www.sec.gov/Archives/edgar/data/1065088/000106508826000205/0001065088-26-000205-index.htm) |
| CRL | 0001628280-26-001905 | [SEC index](https://www.sec.gov/Archives/edgar/data/1100682/000162828026001905/0001628280-26-001905-index.htm) |
| PRU | 0001137774-26-000005 | [SEC index](https://www.sec.gov/Archives/edgar/data/1137774/000113777426000005/0001137774-26-000005-index.htm) |
| PRU | 0001137774-26-000157 | [SEC index](https://www.sec.gov/Archives/edgar/data/1137774/000113777426000157/0001137774-26-000157-index.htm) |
| ARES | 0001628280-26-047830 | [SEC index](https://www.sec.gov/Archives/edgar/data/1176948/000162828026047830/0001628280-26-047830-index.htm) |
| TDG | 0001260221-26-000033 | [SEC index](https://www.sec.gov/Archives/edgar/data/1260221/000126022126000033/0001260221-26-000033-index.htm) |
| WDAY | 0001327811-26-000004 | [SEC index](https://www.sec.gov/Archives/edgar/data/1327811/000132781126000004/0001327811-26-000004-index.htm) |
| WDAY | 0001327811-26-000048 | [SEC index](https://www.sec.gov/Archives/edgar/data/1327811/000132781126000048/0001327811-26-000048-index.htm) |
| MPC | 0001510295-26-000029 | [SEC index](https://www.sec.gov/Archives/edgar/data/1510295/000151029526000029/0001510295-26-000029-index.htm) |
| FANG | 0001539838-26-000003 | [SEC index](https://www.sec.gov/Archives/edgar/data/1539838/000153983826000003/0001539838-26-000003-index.htm) |
| FANG | 0001539838-26-000070 | [SEC index](https://www.sec.gov/Archives/edgar/data/1539838/000153983826000070/0001539838-26-000070-index.htm) |
| FANG | 0001539838-26-000134 | [SEC index](https://www.sec.gov/Archives/edgar/data/1539838/000153983826000134/0001539838-26-000134-index.htm) |
| FANG | 0001539838-26-000177 | [SEC index](https://www.sec.gov/Archives/edgar/data/1539838/000153983826000177/0001539838-26-000177-index.htm) |
| APO | 0001858681-26-000004 | [SEC index](https://www.sec.gov/Archives/edgar/data/1858681/000185868126000004/0001858681-26-000004-index.htm) |
| APO | 0001858681-26-000016 | [SEC index](https://www.sec.gov/Archives/edgar/data/1858681/000185868126000016/0001858681-26-000016-index.htm) |
| APO | 0001858681-26-000033 | [SEC index](https://www.sec.gov/Archives/edgar/data/1858681/000185868126000033/0001858681-26-000033-index.htm) |
| APO | 0001858681-26-000054 | [SEC index](https://www.sec.gov/Archives/edgar/data/1858681/000185868126000054/0001858681-26-000054-index.htm) |

All exception index pages were checked during collection and have no permitted exhibit
candidate. A source exception is not a successful text download.

Missing pageview titles: CLSK, FN, MARA, PODD, RIOT, TSM, ASM.AS, BESI.AS, STMPA.PA, SOI.PA, AIXA.DE, HYPE32196-USD, PEPE24478-USD, ICP-USD.

The three crypto assets without verified articles are Hyperliquid, Pepe and Internet Computer.
Other crypto titles can represent issuer/platform attention proxies; the curated pool is not
an exact top-40 market-cap index. Stable/wrapped/staked exclusion relies on curated source
review, not merely a symbol-name heuristic. The stored audit verifies review structure, not
an independent taxonomy certification.

## Limits requiring review

- A1 remains partial against the task-level all-crypto-titles wording, despite passing the
  acceptance threshold of 90% per pool.
- A5 has the 35 source exceptions above and 19 showcase 10-Ks; TSM has no selected 10-K.
  Foreign forms such as 20-F/6-K require a separately reviewed shared-contract decision.
- A8 upload is pending a private destination/access method from Member D; no upload occurred.
- GDELT returned 345 daily observations each for NVDA and COHR, with 20 missing calendar days
  each. AMD remained HTTP 429 after bounded requests/cooldown; see GDELT_PROBE.md.
- Current membership was collected on 2026-10-24, not reconstructed historically. The shared
  validator exempts snapshot/fetch bookkeeping dates. Schema/as_of validation therefore does
  not certify historical membership, original FRED vintages or market-close availability.
- Latest FRED CSV can include revisions; no historical vintage reconstruction is claimed.
- Full product SAMPLE_MODE with networking disabled and hosted sponsor acceptance were not
  newly executed in this review. Passing the sample table tests alone does not prove that flow.

## Security and delivery scope

Configured private contact strings occur zero times across lake and sample string columns.
No .env, credentials, production lake, cache, logs or backup archives are proposed for the PR.
The sample and curated crypto CSV also remain local under the ingest-only submission scope.
A separate authorized delivery is needed before consumers can reproduce artifact-dependent
tests from a clean checkout. The sample hashes document the excluded local artifact.
No existing tests, shared contracts or other members' modules were changed. The production
lake, caches and local settings are excluded from the proposed Git submission.

## Current implementation checks, kept separate from real artifact checks

| Check | Actual result |
| --- | --- |
| Full offline repository suite after review fixes | 329 passed, 10 existing warnings, 0 skipped |
| Ingest tests excluding the lake/sample file | 81 passed |
| Shared contract unit tests | 17 passed |
| Real-lake cases | 7 passed, 82 deselected, 0 skipped |
| Exact real-sample case from ACCEPTANCE.md | 1 passed, 0 skipped |
| Ruff on implementation and both added tests | Pass |
| Dependency consistency | No broken requirements found |

The full-suite total includes the separately listed subsets. Initial collection failed before
optional agent/API dependencies were installed; it passed after installation. Broad-ingest
Ruff reports two import-order findings and six files needing formatting in unchanged upstream
tests. Those tests remain byte-identical to origin/main and were not edited.

Three small implementation review fixes restored finite/maximum retry settings, disabled and
restored Yahoo's configurable extra retry budget, and retained showcase_symbols(root). Ten
invalid retry configurations were manually rejected before I/O; the root-local helper was
checked. Existing unit tests were not changed. The proposed PR description records exact commands/output.

## Ingest-only submission verification

An independent clean export of the exact staged tree (no .env, lake, sample or local crypto CSV)
was tested before submission: **321 passed, 8 skipped, 10 warnings in 14.75s**. The eight skips
are seven lake cases plus the sample case, reflecting excluded artifacts rather than weakened
assertions. The source checkout with local real artifacts still reports **329 passed**. These
are distinct environments; this ingest-only PR does not deliver the missing artifact acceptance.
