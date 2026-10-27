# Global internationalization V2 acceptance

**READY FOR REVIEW. NOT READY FOR MERGE.** Technical browser acceptance is separate from
native-language financial editorial, real screen-reader and audible speech sign-off.

Tested implementation: `4e61b5009777985096a81b195e3371fa7616e5b1`. Verified main baseline:
`eee913ad7b310e277b8b334ab6649e5cb0877bc4`. The later evidence commit changes documentation/images only. Its exact final PR HEAD SHA
is recorded in the Draft PR description and engineering handoff, avoiding a self-referential
commit hash in this file. The final implementation
was tested locally before its publication; evidence packaging followed remote SHA verification.
Only `b/global-i18n-accessibility-v2-20261026` is authorized as a new remote branch.
No historical branch, main, contracts, shared fixtures, dependencies, lockfile or CI workflow
is changed by this proposal. No merge, deployment or trade execution is included.

## Execution and evidence

The tests below ran locally before the final implementation push, against immutable production builds of the exact
implementation above. [commands.json](commands.json) records the command, working directory,
explicit environment, tested commit and exit status. Corresponding actual text output is in
`commands/`; full generated result records are in `results/`. Workspace and external-runtime paths are made
portable with `${REPO}`, `${QA_ROOT}`, `${PLAYWRIGHT_RUNTIME}` and `${CHROMIUM}`. Original/published byte hashes are recorded in
[evidence-manifest.json](evidence-manifest.json). No earlier repair-commit pass count is reused.

Node 24.19.0, npm 11.9.0, Vite 7.3.7, system Chromium 154, axe-core 4.14.0 and Lighthouse
13.5.0 were used. Browser/Lighthouse/axe tooling is external to the frozen application
package graph. This is Linux headless Chromium evidence, not Windows Edge evidence.

| Area | Result | Evidence |
| --- | --- | --- |
| Frozen `npm ci` | PASS, exit 0 | [output](commands/install.txt) |
| Unit tests | PASS, 130/130, 18 files; exit 0 | [actual JSON](results/unit.json) |
| API contracts | PASS, RunOutput and all 19 trace lines; exit 0 | [output](commands/contracts.txt) |
| Locale keys/placeholders | PASS, 614 application keys in 11 locales, 528 authored sites; exit 0 | [output](commands/i18n.txt) |
| Production / API builds | PASS, exit 0, no oversized chunk warning | [fixture build](commands/build.txt) · [API build](commands/api-build.txt) |
| npm audit | PASS, 0 info/low/moderate/high/critical; exit 0 | [actual JSON](results/audit.json) |
| Git whitespace | PASS, exit 0 | [output](commands/diff.txt) |
| Main preservation | PASS for protected files and full source scope | [hashes](preservation.json) · [scope](scope.json) |
| 462-case matrix | PASS, 11 locales × 7 routes × 3 widths × 2 views | [CSV](matrix.csv) |
| Additional matrix checks | PASS, 14 CSS-text and console groups, outside the 462 | [three complete runs](results/matrix-a.json) |

| Browser suite | Result | Actual coverage | Evidence |
| --- | --- | --- | --- |
| original | PASS | 17 groups; 0 failed | [records](results/original.json) |
| redesign | PASS | 18 groups; 0 failed | [records](results/redesign.json) |
| global | PASS | 84 groups; 0 failed | [records](results/global.json) |
| agent | PASS | 15 groups; 0 failed | [records](results/agent.json) |
| contrast | PASS | 14 groups; 0 failed | [records](results/contrast.json) |
| loader | PASS | 12 groups; 0 failed | [records](results/loader.json) |
| api | PASS | 5 groups; 0 failed | [records](results/api.json) |
| mainline | PASS | 33 groups; 0 failed | [records](results/mainline.json) |
| states | PASS | 176 groups; 0 failed | [records](results/states.json) |
| data | PASS | 57 groups; 0 failed | [records](results/data.json) |
| tooltips | PASS | 67 groups; 0 failed | [records](results/tooltips.json) |
| reproductions | PASS | 12 groups; 0 failed | [records](results/reproductions.json) |
| axe | PASS | 154 groups; 0 failed | [records](results/axe.json) |
| lighthouse | PASS | 22 groups; 0 failed | [records](results/lighthouse.json) |
| native-zoom | PASS | 308 groups; 0 failed | [records](results/native-zoom.json) |

The group totals overlap and must not be added as unique user journeys. The data suite
compares all 620 loaded recommendations and all 30 explanations per locale (6,820 rows and
330 explanations total), plus 770 expanded route/view/width reflow checks. It reports exact
source parity, original narratives, enums, hashes, dates, warnings and measurement meanings.
The standard matrix uses 1440, 768 and 320 CSS pixels. Separate native zoom cases use CSS
widths 720 and 320 at 200%, not a substituted CSS text-size test.

## Eleven independent locale assessments

Each locale independently executes every route family in Simple and Pro, initial/persisted
language navigation, filters, failure states, Agent/evidence parity, speech mocks, keyboard,
reduced motion, semantic naming, axe, Lighthouse and native zoom. Each JSON contains its own
terminology observations, counts, source checks and editorial risks. No locale is certified
solely by dictionary coverage or another locale's results.

| Locale | Technical | Matrix | States | axe | Lighthouse | Native 200% | Native editorial | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| en | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_en.json) · [images](evidence/en-review.jpg) |
| zh-CN | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_zh-CN.json) · [images](evidence/zh-CN-review.jpg) |
| zh-TW | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_zh-TW.json) · [images](evidence/zh-TW-review.jpg) |
| es | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_es.json) · [images](evidence/es-review.jpg) |
| fr | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_fr.json) · [images](evidence/fr-review.jpg) |
| de | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_de.json) · [images](evidence/de-review.jpg) |
| pt-BR | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_pt-BR.json) · [images](evidence/pt-BR-review.jpg) |
| ja | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_ja.json) · [images](evidence/ja-review.jpg) |
| ko | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_ko.json) · [images](evidence/ko-review.jpg) |
| cs | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_cs.json) · [images](evidence/cs-review.jpg) |
| ar | PASS | 42/42 | 16/16 | 14 checks | 2 checks | 28/28 | NEEDS HUMAN REVIEW | [assessment](locales/QA_ar.json) · [images](evidence/ar-review.jpg) |

[locales.csv](locales.csv) provides a compact comparison. Technical PASS does not certify
naturalness, grammar, regional preference, financial suitability or pronunciation.

AI inspected 77 prepublication route contact sheets (six business viewport crops each),
then final-commit contact sheets for all eleven locales showing Discover at 1440, detail Pro
at 768 and Factor Lab Pro at 320. The full final matrix captures and checks all 462 cases;
this is not a claim that a human inspected every full page pixel by pixel. Selected authentic
captures cover every locale, all three widths and all seven routes; fingerprints for every
matrix capture are retained in the CSV. Only selected images are published to keep the PR
compact. Capture paths inside raw results are collection identifiers, not download links;
only artifacts listed in the committed manifest are published. Long pages require scrolling, and wide research tables intentionally scroll within
named regions. Small treemap labels can truncate; tooltips and numeric alternatives expose
full values. No required information was hidden to obtain reflow results.

## Mainline preservation and twelve repairs

[V2_INTEGRATION.md](../../V2_INTEGRATION.md) records the inspected patch ancestry, the four
resolved conflicts (App, ResearchGuide, Trace, TrackRecord), duplicate Agent-guide skip and
per-file behavior preservation for all twelve shared files. [preservation.json](preservation.json)
records baseline/implementation hashes. Current main's full-run provenance, REPLAY cautions,
source-only abstention summary, paused speech recovery, failed/retry trace order, timing
comparisons, evaluation boundaries and newer security/dependency/CI state remain retained.

[Historical reproduction results](results/reproductions.json) cover FIX01–FIX12 against
saved `3d2ae4f` source/build and the final V2 implementation. The reproduction probe itself
does not modify historical branches, original fixtures or recorded values.

| Fix | Final behavior and verification |
| --- | --- |
| 01 | Arabic signed values remain LTR-isolated within RTL; real browser Range positions verify sign-before-digit. |
| 02 | Regime tone uses raw enum, across all three source pool states and all locales. |
| 03 | Actual business tables receive one caption, preserving column/row header relationships. |
| 04 | Original Agent assertions use global preferences and page-aware asynchronous catalog waits. |
| 05 | Visible Listen entry focuses the existing controller; it never auto-plays. |
| 06 | Voice events, bounded polling, manual refresh, strict region/script selection and no silent substitution. |
| 07 | Rapid Factor Lab changes preserve both canonical pool/status query parameters. |
| 08 | Enlarged pt-BR actions wrap without widening the page. |
| 09 | Recorded summary survives missing failed-check details, without inventing a missing reason. |
| 10 | Japanese/Korean risk elevation, German abstention and Arabic evaluation terminology preserve research semantics. |
| 11 | Locale-aware day units, including Czech integer/fraction forms; actual rendered tooltips checked. |
| 12 | Rich badge fragments retain inline spacing. |

Local fault injection additionally fixed an obscured retry notice and rejected-ESM-cache
recovery. Actual axe found English/Korean visible-link/accessibility-name mismatches; names
now include the visible label. Visual inspection replaced a bidi-sensitive Arabic slash
fraction with explicit points-out-of-five wording, preserving the source numbers.
The real axe incomplete output also exposed generic gate containers with prohibited naming.
Factor Lab now uses explicit named groups. Final regression checks require a named group for
every factor card and zero unresolved `aria-prohibited-attr` entries, without disabling rules.

A final Agent suite initially failed because its catalog helper demanded a detail-only guide
on Discover. The page-aware wait was corrected without removing any cancellation assertions
or modifying application behavior. The first failed exact-commit result is retained as
[superseded Agent run](results/superseded-agent.json); all final evidence above belongs to the
subsequent V2 revisions. An additional fault-injection probe then reproduced a stale guide
failure overwriting a later pending language selection. The controller now ignores that
stale failure. Its unit regression failed before the fix and passes after it, and all twelve
loader browser groups include the real blocked-module scenario. The final complete suite
was rerun on the exact implementation identified above.

## Five historical pluralization findings

The old dynamic tooltip key was `Horizon: {value1} days\nMean IC: {value2}\nt-stat: {value3}\nn: {value4}`.
Its one-day values incorrectly inherited a fixed plural. The current key is
`Horizon: {days}\nMean IC: {value2}\nt-stat: {value3}\nn: {value4}`, with `Days (one)` / `Days (other)`
and other Intl.PluralRules categories. `Horizon: {days}` and the run horizon use the same
formatter. Numeric policy remains canonical; this is unit morphology, not a global string
replacement or financial-value conversion.

| Locale / catalog | Correct singular | Correct plural and additional forms |
| --- | --- | --- |
| `es`, `src/i18n/locales/es.json` | `Days (one)`: `{count} día` | `Days (other)`: `{count} días` |
| `fr`, `src/i18n/locales/fr.json` | `{count} jour` | `{count} jours` |
| `de`, `src/i18n/locales/de.json` | `{count} Tag` | `{count} Tage` |
| `pt-BR`, `src/i18n/locales/pt-BR.json` | `{count} dia` | `{count} dias` |
| `cs`, `src/i18n/locales/cs.json` | `{count} den` | `few`: `{count} dny`; `other`: `{count} dní`; `many` fractions: `{count} dne` |

All five historical findings are technically repaired. Unit tests cover 0/1/2/4/5/21/100 and
fractions; every locale also has an actual ECharts one-day tooltip capture. Native grammar
review remains separate, including Czech case/gender outside these unit forms.

## Lazy loading and bundle evidence

English application/guide resources and locale metadata stay eager. Ten non-English
application catalogs and ten separate guide catalogs are dynamically imported and cached.
Guide catalogs load only on Ticker Detail. Browser manifest/request tests verify the actual
built graph, cold/saved preferences, rapid switching, stale completion, deduplication,
failed imports, retry, offline recovery, reload and blocked storage. Mounted route, filters,
pagination, view and original data survive language changes. Retry fetches a validated,
versioned same-origin JSON fallback because browsers cache failed ESM requests; those assets
are not requested during successful normal navigation. No translation or TTS service is added.

| Measurement | Before eager candidate | Final lazy V2 |
| --- | --- | --- |
| Entry JS raw bytes | 1,124,843 | 563,185 |
| Entry JS gzip level 9 bytes | 361,362 | 171,315 |
| Largest non-fixture chunk bytes | 1,124,843 | 672,252 |
| Oversized-chunk warning | Present | Absent |

[startup-comparison.json](startup-comparison.json) separately records actual cold Discover
JavaScript request totals, including the fixture and route chunk, so entry size is not
misrepresented as all initial network JavaScript.

[bundle-comparison.json](bundle-comparison.json) lists all twenty locale/guide chunks and exact
compression methodology. Both builds used the actual frozen main dependency toolchain. The
before artifact is the integrated pre-optimization candidate before final repairs, not a
published baseline or a controlled one-variable benchmark. The unchanged limit is 1,000,000
bytes per non-fixture JS chunk; warning thresholds were not raised.

## Financial and synthetic-data boundaries

SYN369 still has rank 4 of 520, displayed score +1.39, source tier `STRONG_OVERWEIGHT` and
explanation verdict `abstained`. Verified claim `exp-us_equity-syn369-c1` and rejected claim
`exp-us_equity-syn369-c2` retain their original text, checks, evidence IDs and SHA-256 hashes.
The largest contribution remains `pv_mom_1m`. Locale switches do not recompute a model,
create claims or perform backend mutations. NO_CALL, unavailable values and failed gates
retain their meaning. Real API data provenance tests use contract-valid **browser mocks**;
no new live production backend or complete model replay was exercised here.

The fixture reuses `factor_contributions` / `factor_value` for the supplier
claim as well as the factor claim, with different hashes. This does not semantically establish
a supplier event. The actual event date, movement date and underlying result rows are absent;
`as_of` is not a substitute. V2 preserves that mismatch and explicitly discloses that the
recorded `cause_before_move` failure cannot be independently reconstructed from this fixture.
See [source reference](syn369-source-reference.json). No timestamps were fabricated.

Other preserved fixture limitations include tier sample sum 1,808 versus reported settled
count 1,200, independently generated gate/regime measurements versus flags, mismatched
current/history regime points and all nine paired trace duration discrepancies. UI notices
preserve both source values. The trace does not prove executed orders or infer LLM calls
from model-bearing node records. Track Record does not claim realized portfolio performance.

## Accessibility, speech and remaining review gates

Actual axe scans cover 154 expanded route/view cases at 320px, with zero critical/serious
violations. All violation levels and **incomplete** rules remain in the full aggregate output;
canvas/decorative contrast checks requiring manual review are not silently discarded.
Lighthouse measures 22 detail navigations (all locales at 1440 and 320), all scoring 100;
these scores do not certify every route or WCAG conformance. Selected unabridged raw axe and
Lighthouse results are included under `results/raw/`. The named-gate issue has separate
Factor Lab before/after raw outputs; the before output is explicitly historical, not a
remaining final failure.

Actual Chrome native zoom is set through `chrome.settingsPrivate.setDefaultZoom(2)` in
isolated persistent profiles, with `viewport:null`. Outer 1440/640 becomes inner 720/320,
DPR changes from 1 to 2, root font stays 16px and visual viewport scale stays 1. All 308
route/view/locale cases pass. This is browser zoom, distinct from the separate CSS 200%
font-enlargement test. It is not a physical-device manual keyboard zoom assessment.

Speech API mocks verify Play/Pause/Resume/Stop, paused-engine recovery, explicit activation,
late/eventless enumeration, unavailable APIs, empty lists, Chinese-only lists, errors and
locale/route/instrument cancellation. Actual native Linux voice inventory is recorded, but
**no audible output was heard** and no pronunciation claim is made. Text remains available
when a matching voice is absent; zh-TW and pt-BR do not silently use another regional voice.

| Remaining item | Severity / status | Required acceptance |
| --- | --- | --- |
| Native financial editorial, every locale | Important / NEEDS HUMAN REVIEW | Review regional terminology, grammar, idiom and all risk/caveat language. |
| NVDA / VoiceOver and physical RTL reading order | Important / NOT TESTED | Native assistive-technology keyboard/reading acceptance. |
| Real audible speech, pronunciation, Windows Edge inventory | Important / NOT TESTED | Test installed voices and audible controls on real target devices. |
| axe incomplete/manual contrast groups | Important / MANUAL REVIEW | Inspect retained incomplete outputs; automated zero violations is not sufficient. |
| New live backend / full model replay | NOT TESTED in this V2 run | Integration acceptance beyond mocked transport states. |
| Long-word hyphenation, French spacing, Czech preposition breaks, CJK register | Optional editorial polish | Native editor and target-device typography review. |

No known final local automated blocker remains. Pending manual gates prevent a READY FOR
MERGE claim. The implementation PR remains a review proposal; CI results and team approval
must be considered separately. Never merge solely because a build or accessibility score passes.

## Publication verification

[publication.json](publication.json) records the exact implementation remote SHA and before/after branch heads. This task created only the V2 remote branch. A separate lead-owned sponsor-integration branch appeared independently after the original snapshot; it was already present before this publication and was not changed by this task. All twelve original remote heads, including main, remain unchanged.
