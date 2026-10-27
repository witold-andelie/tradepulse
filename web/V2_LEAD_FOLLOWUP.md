# Global UI V2: lead acceptance and remaining scope

Updated 27 October 2026. The lead explicitly authorized merging Huyin's V2 before remaining
native acceptance and took over follow-up. PR #8 is merged as `a4d49a72e85712375aa1a38a46f009b805844168`.
Original contributor commits and original QA evidence are retained. No further V2 delivery
is assigned to Huyin. This authorization supersedes the earlier guide-only UI boundary and
proposal-stage instructions to leave the PR in Draft.

## Approved implementation

Eleven authored UI catalogs, English by default, with lazy non-English and guide resources.
Source narratives, financial values, canonical codes, identifiers and evidence remain original.
No new application dependency, contract change or trading capability was introduced.

Independent lead review checked head `90794af`, whose application tree is identical to the
merged version: 130 frontend tests, contract checks including all 19 trace lines, 614 keys in
11 locales and a production build passed. Entry JS was 563.19 kB raw; largest non-fixture
chunk was 672.25 kB raw, below the existing 1 MB limit. A Windows Chrome fixture spot check
passed 21 English/Chinese/Arabic routes at 320 CSS pixels, including source-summary preservation,
single headings, named tables and no page exceptions. These are browser/software observations,
not native screen-reader or live sponsor acceptance.

## Time-bounded follow-up

| Item | Owner | Result / scope |
| --- | --- | --- |
| Align rules and ownership | Lead | Complete in this follow-up; global authored UI scope is approved. |
| Focused contrast review | Lead | Complete for the sampled controls, badges, charts and scrolled tables; [measurements and screenshots](qa-reports/lead-v2/README.md). Not a full eleven-language audit. |
| Short native screen-reader check | Lead | NOT TESTED. NVDA was not found at the checked standard Windows installation paths; Computer Use could not connect its native pipe. No native reading output was observed. |
| Actual audible speech, cross-browser voice inventory and pronunciation | Lead | DEFERRED explicitly; outside the remaining submission work. |
| Human financial-language editorial for all eleven locales | Lead | DEFERRED explicitly; outside the remaining submission work. |

Do not relabel automated semantics, screenshots or speech mocks as a native reading or audio
pass. The merge is implementation acceptance with disclosed residual checks, not complete
WCAG certification. The read-aloud feature remains optional and device-dependent.

## Brief Mac VoiceOver check when available

Use the updated actual frontend in the existing Mac environment; no new tool or voice
installation is required. This is a short native reading check, not pronunciation or voice
catalog certification. Keep the existing GLM/Zetaris acceptance running independently.

1. Turn on the Mac's built-in VoiceOver. Open Discover and check the title, language selector
   and the actual data-mode banner. Keep REAL, REPLAY and SYNTHETIC labels truthful.
2. Open an instrument in English, then Chinese if a suitable installed reading voice is
   available. Read its heading, explanation verdict and one claim. Expand a claim and confirm
   the control state and evidence/table labels are announced. Original English source text
   remains original; do not claim translated model narratives.
3. On Regime or Track Record, expand one Show data as table control and confirm its state,
   table caption and headers are navigable. Confirm keyboard focus is visible and no trap occurs.
4. Record the actual commit, browser, reader, locale, routes and observations. If a voice or
   reader is unavailable, record that limitation. Turn VoiceOver off after the check.

Do not delay the US end-to-end/API/UI and submission work to install a reader or test every
language. Preserve the pending native status until real observations are recorded.
