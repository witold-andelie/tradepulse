# Agent research accessibility experiment

Baseline: `origin/main` at `8a2aa1cd797cc56d22cbf44b4b76a46ed8ebf95a`, independently
matched to the remote main ref before creating `b/agent-accessibility-demo-20261025`.
The original `b/agent-accessible-ui` checkout is preserved in its own worktree.

## Proposed exception and merge boundary

This branch proposes an exception to the English-only UI rule **only for the new research
guide**. The lead must approve that exception before a merge. Main's instructions are
unchanged. Code comments, documentation, original page copy and source narratives stay
in English or their supplied original language. This is not full-application localization.

Only `web/` changes. No dependency, contract, fixture, backend, score, ranking or verifier
changes. No changes to App, shell, providers, global navigation, API client, global CSS,
Discover, ResearchGuide, Factor Lab or Member C's pages. No existing test assertions change.
There is no push, PR, merge or deployment in this delivery.

Exact changed files:

```text
web/AGENT_ACCESSIBILITY_DEMO.md
web/scripts/agent-research-acceptance.cjs
web/src/components/agentResearch/GuidedResearch.jsx
web/src/components/agentResearch/GuidedResearch.module.css
web/src/components/agentResearch/agentResearch.test.js
web/src/components/agentResearch/messages.js
web/src/components/agentResearch/speech.js
web/src/components/agentResearch/summary.js
web/src/components/agentResearch/useReadAloud.js
web/src/pages/Detail.jsx
```

## Implemented behavior

Ticker Detail adds four native, keyboard-operable question disclosures before the original
research panels. They show source-backed rank, score, tier, largest absolute factor
contribution, explanation verdict, claim counts, original narratives, recorded failed checks,
counter-case, invalidation and what-to-watch records. A missing explanation stays missing;
its verification counts are not filled with zeros. Unknown instruments retain the existing
not-found state.

Simple and Pro use the same record selector and the same guide component. Neither translates,
recalculates or replaces financial data. Original claims/checks/evidence remain fully
inspectable through the existing detail disclosures in both presentations. The guide links
to those disclosures rather than introducing a second evidence renderer.

Synthetic statuses and hashes are identified as generated demonstration records. A
`cause_before_move` check is presented as a recorded outcome: the current contract payload
does not supply the compared event and market-move timestamps. Its temporal comparison
cannot be independently reproduced, and `as_of`/`created_at` are never substituted.
Original evidence labels, IDs and hashes are preserved, including the known synthetic
supplier/factor-source mismatch. The original evidence panel now explicitly labels an absent
source link and calls its checks recorded checks. Its synthetic caveat remains visible when
opening the original explanation directly.

## Locale coverage

The guide has 52 required keys for each of: `en`, `zh-CN`, `zh-TW`, `es`, `fr`, `de`,
`pt-BR`, `ja`, `ko`, `cs`, `ar`. All eleven dictionaries are structurally complete and
checked by tests. Native-speaker editorial acceptance is still pending; structural completeness
does not certify translation quality.

English is the default. The selector uses native names and advertises only complete
dictionaries. A missing-key lookup falls back to English with its language metadata; an
incomplete/unknown persisted locale falls back to the complete English guide. Local storage
is optional and failures do not prevent language selection. A further locale needs a complete
dictionary and a registry entry, not a financial-data or backend change.

Arbitrary source narratives are verbatim, clearly marked as untranslated, outside the localized
text's language inheritance (`lang=""`, `dir="auto"`). Structured labels are translated;
symbols, enum values and B1 financial formatting remain unchanged. Raw verdicts are quoted
as source enum strings; the original overall verdict badge remains distinct. Arabic uses
local RTL direction with isolated LTR identifiers. The document stays `lang="en"`.

## Read aloud

Native browser SpeechSynthesis is optional and never starts automatically. Play, Pause,
Resume and Stop use a suitable explicitly displayed voice. Generic languages may use a
voice of the same language with a regional tag; explicit regional locales are not silently
replaced. A missing voice disables playback, explains the limitation and offers voice refresh
or an explicit guide-language change. There is no automatic English-voice fallback.

Speech covers the guide's readable structured answers and limitations. Arbitrary original
narratives stay readable and are not spoken under a guessed language. Hashes and original
evidence remain in the existing visual disclosures. Locale/voice changes, route changes,
instrument changes and unmount cancel owned speech. Browser errors, interrupted playback,
late callbacks and delayed starts are handled without breaking research; a bounded 12-second
start watchdog does not count intentional pause time. Native pause/resume events are handled.

Application code sends no text to a translation or speech service. Browser/OS voices may
use online services; no promise of offline operation is made.

The available Linux Chromium reports SpeechSynthesis support but **zero installed voices**.
Native no-voice behavior was inspected. Playback and cancellation were tested using an
injected browser API double and unit tests, not audible native speech. Real voice quality,
pronunciation, pause behavior and platform differences need independent desktop/mobile review.

## Local validation

- Baseline `npm test`: 68/68 passed before implementation.
- Feature `npm test`: 80/80 passed across 13 files, including 12 new focused tests; exit 0.
- `npm run check:contracts`: RunOutput and all 19 trace lines passed; exit 0.
- `npm run build`: passed without chunk warnings; exit 0. Largest chunk remains 627.84 kB.
- `git diff --check`: exit 0.
- New `agent-research-acceptance.cjs`: 15/15 groups passed in Chromium 154.0.8037.57.
- Unchanged original browser suite with its existing Pro preload: 17/17 groups passed.
- Unchanged redesign suite: 18/18 groups passed.
- Existing focused contrast/target check: 14 route/view combinations, 5,550 inspected text
  nodes, minimum measured text contrast 5.66:1; no reported contrast failures, unnamed
  inspected controls or inspected targets below 24px. This is not an axe or WCAG audit.

One parallel legacy run observed 11 rather than 2 cards immediately after selecting the
Factor Lab ACTIVE filter. A subsequent standalone run passed all 17 groups without changing
the page, fixture or original script. This is a likely asynchronous assertion timing flake;
the failed run is preserved under `release-legacy`, and the passing standalone run under
`release-legacy-sequential`. No assertion was weakened to obtain the pass.

The focused browser suite covers all eleven locale switches, exact financial/evidence parity,
explained/abstained/absent/unknown states, Arabic direction, optional storage, speech lifecycle,
unsupported APIs, absent voices, keyboard controls and labels. Genuine guide captures cover
1440px, 768px and 320px in English, Simplified Chinese and Arabic. Reduced-motion emulation,
ARIA snapshots and 200% text enlargement were checked. Text enlargement is not native zoom.

Evidence and command logs are kept outside the source tree under
`/workspace/work/agent-demo-20261025/`. These are internal workspace artifacts, not uploaded
attachments or evidence published to GitHub. The reproducible scripts are committed.

Run the focused browser suite with an existing Playwright tooling runtime and system Chromium:

```sh
npm run build
npm run preview -- --host 127.0.0.1 --port 5184
# From the repository root in a second terminal:
TRADEPULSE_QA_DIR=/tmp/tradepulse-agent-review node web/scripts/agent-research-acceptance.cjs
```

## Remaining acceptance and merge attention

Ready for independent review as an experiment, not cleared for merge. Pending: lead approval
of the scoped multilingual exception, native-speaker review, audible native speech in browsers
with installed voices, NVDA/VoiceOver, native browser zoom and cross-browser checks. Lighthouse
and axe are not installed in this environment and were not run. No accessibility certification
or production backend acceptance is claimed. Existing synthetic provenance gaps remain.

Only `Detail.jsx` touches existing application source. Review that small integration carefully
if another contributor changes the original evidence panel. New CSS is a component module
using existing tokens; the speech hook and dictionaries are local to this feature, not shared
providers. No teammate needs to implement an API or translate generated Agent prose.
