# TradePulse — eleven-language acceptance evidence

This branch publishes **documentation only** for independent second QA review.
It does not publish, merge, or approve the multilingual implementation.

- Actual tested implementation: `cd2b610049424fd6b3b7c8c169a9e2e426acc1b1`.
- Implementation audit baseline: `3d2ae4ff1a74837b9dd41bfe8d505ca2f0861584`.
- Documentation branch: `b/i18n-qa-evidence-20261026`.
- Documentation parent: `c69e3d7642295b609f7db22c2079769d5d2e4b82` (the remote main observed before publication).
- The tested repair commit remains local; this documentation publication does not make that implementation commit remotely accessible.
- No application test was rerun for this documentation-only publication. Results below are recorded results from the completed audit.
- User authorization explicitly covers publishing the original Chinese reports verbatim. It does not grant release approval for application-wide localization.

## Read the complete original reports

All twelve Markdown reports below are byte-identical to the completed audit originals, unabridged and untranslated.
Their SHA-256 hashes are recorded in [ORIGINAL_REPORTS_SHA256.txt](ORIGINAL_REPORTS_SHA256.txt) and the [test evidence manifest](TEST_EVIDENCE_MANIFEST.json).

| Report | Link |
|---|---|
| MASTER_QA_ZH | [MASTER_QA_ZH](MASTER_QA_ZH.md) |
| QA_en | [QA_en](QA_en.md) |
| QA_zh-CN | [QA_zh-CN](QA_zh-CN.md) |
| QA_zh-TW | [QA_zh-TW](QA_zh-TW.md) |
| QA_es | [QA_es](QA_es.md) |
| QA_fr | [QA_fr](QA_fr.md) |
| QA_de | [QA_de](QA_de.md) |
| QA_pt-BR | [QA_pt-BR](QA_pt-BR.md) |
| QA_ja | [QA_ja](QA_ja.md) |
| QA_ko | [QA_ko](QA_ko.md) |
| QA_cs | [QA_cs](QA_cs.md) |
| QA_ar | [QA_ar](QA_ar.md) |

## Verification, findings, and evidence

- [I1–I4 findings, reproduction steps, repairs, and verification references](I1-I4_FINDINGS_AND_REPRODUCTION.md).
- [Five unresolved pluralization findings: exact keys, current translations, and recommended corrections](UNRESOLVED_PLURALIZATION_EXACT_KEYS.json). Singular templates are suggestions for the one-day case, not replacements for every count; no translation was changed during publication.
- [Twelve-file latest-main conflict inventory](LATEST_MAIN_CONFLICTS.json). This describes the audit-time main versus the tested repair commit. No actual merge was performed.
- [Speech availability and outstanding device limitations](SPEECH_AND_DEVICE_LIMITATIONS.md).
- [Test evidence manifest, result counts, per-locale state coverage, report hashes, and local-artifact hashes](TEST_EVIDENCE_MANIFEST.json).
- [462-case coverage matrix](COVERAGE_MATRIX.csv).
- [Actual tested commit and recorded commands](TESTED_COMMIT_AND_COMMANDS.json).

## Acceptance boundaries

All eleven locales received 42 standard matrix cases and 16 state groups each. The recorded technical suites passed, but **no overall release approval was issued**. Native financial editorial review remains pending for every locale. The five confirmed pluralization issues remain unresolved, and affected reports explicitly mark their grammar dimension FAIL. Real audible speech, native screen-reader acceptance, and native browser 200% zoom are not established by API mocks, DOM checks, or CSS text enlargement.

SYN369 remains an abstention; fixture values and evidence identifiers/hashes were preserved. The synthetic supplier claim lacks actual event and market-movement dates, and generic fixture provenance cannot prove real-world causality. The twelve implementation/main integration conflicts require separate lead review.

## Local evidence and preserved links

The original reports contain absolute cloud-workspace links and original evidence-relative paths. They are intentionally unchanged to preserve the reports exactly. Those links are **not GitHub attachments**, and screenshots, logs, ZIPs, caches, and application source have deliberately not been uploaded to this documentation branch.

No requested original report or listed supporting small-text document was missing at publication. Raw screenshots, logs, accessible-tree snapshots, intermediate test runs, and the source ZIP exist in the original task but are **unavailable through this branch**. The manifest records hashes for selected structured evidence without pretending those raw artifacts are attached. A second reviewer can read all report prose, reproduction steps, exact keys, limitations, commands, and coverage here, but cannot independently replay screenshots or inspect the unpublished repair source from this branch alone.

For repository-relative source paths quoted in the reports, the authoritative reviewed version is the tested commit above. Application files inherited from this branch's main parent are not represented as the tested multilingual build.
