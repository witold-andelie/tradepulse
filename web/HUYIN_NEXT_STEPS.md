# Huyin — review the integrated frontend

Hi Huyin,

Your B1, B2–B10 and accessibility work is now part of the main frontend baseline. I integrated
your original commits and kept their author history, including the six business pages,
Discover, Simple/Pro, the design system, keyboard interactions and chart data alternatives.

The earlier message asking you to replace three placeholders was based on a different main
branch implementation and did not account for your submitted work. It is superseded by this
instruction. You do not need to redo B1–B10, migrate everything into another design system, or
resolve the old seven-file integration conflict. I have handled that integration.

Your remaining assignment is to review the integrated result, identify concrete problems, and
make focused fixes where needed. Your existing implementation remains credited regardless of
whether this review finds additional changes.

## 1. Start from the current main baseline

First run `git status` in your existing checkout.

- If you have uncommitted or unpublished work, preserve it and tell me before switching.
  Do not discard it or copy an older checkout over main.
- If your checkout is clean, update main and create one review branch:

```text
git switch main
git pull --ff-only origin main
git switch -c b/ui-review-20261024
cd web
npm ci
npm run dev
```

If that branch name already exists, choose a fresh suffix. If updating main reports a conflict
or unexpected divergence, send me the branch name and status; I will handle the baseline issue.
Do not spend hours rebasing the original B1/B2–B10/accessibility branches.

Open http://localhost:5173. For this first review, leave `VITE_API_BASE` unset so the app uses
the synthetic fixture. Local environment files stay uncommitted. On the team's Windows
machines, put the npm cache and temporary files on D:.

Read the updated status section in `web/TASK.md`, `web/AGENTS.md`, `web/ACCEPTANCE.md`, and
`web/INTEGRATION.md`. The wider dependency plan is in `docs/STATUS.md`.

## 2. Review your existing UI before changing it

The root still opens US equities; `/discover` is the guided entry. Simple and Pro use the same
records. Please check that the integration retained your intended visual hierarchy,
navigation, view switching, market context and evidence disclosures.

Keep the current layout and design unless a concrete problem requires a change. A review that
finds no regression is useful; there is no requirement to invent a redesign or open an empty PR.

## 3. Your primary page checks: B4–B6

### Leaderboard

- Check all three pools and compare displayed values/counts with the actual fixture records.
  Loaded row count and the source's reported ranked/member counts are different measurements.
- Combine search, sector and tier filters; sort numeric columns and move between pages.
- Switch Simple/Pro without losing the selected pool, filters, sorting or pagination.
- Open a record from the shortlist or a row/card, then return with its market context intact.
- Check sector filtering through the chart and its keyboard-operable alternative.

### Ticker Detail

- Check an explained record, an abstained record and an unknown symbol.
- Confirm that the same instrument, metrics and risk/evidence records survive view switching.
- Verify contribution signs, the contribution-sum caption and the numeric alternative.
- Open claims and inspect checks/evidence. Rejected claims and counter-evidence must remain
  available, including in Simple View.
- Check invalidation, what-to-watch, models and retries against the source records.

### Factor Lab

- Check pool/status selection, all five gates, weights, coverage, IC data and research windows.
- Keep unsupported filing-factor cards visible for EU and crypto, including insufficient-data
  states. Do not hide them to make a page look more complete.
- Present recorded gate outcomes as supplied. If a synthetic value appears inconsistent with
  a flag, report it; do not change fixtures or recalculate outcomes in the frontend.
- Keep the distinction between measuring, predicting and earning, and between in-sample
  diagnostics and the separate walk-forward evaluation.

Prioritize wrong data, lost evidence, broken controls, missing provenance and accessibility
barriers. Optional visual refinements come after those findings.

## 4. What the integration has already adapted

- Your pages remain the implementations. The agreed `LeaderboardPage`, `TickerPage`,
  `FactorLabPage` and B7–B9 entry points delegate to them.
- Both run-hook import paths share one provider; `retry` and `reload` are compatible aliases.
- UI data passes through the strict schema-validating client. Existing transport APIs remain
  for compatibility, and both original test suites are retained.
- `Chart` delegates to `ChartFigure`, retaining your modular lazy renderer and numeric
  alternatives. Existing figures do not need to be rewritten just to change their import name.
- The shell owns the single main landmark, provenance banner, Run notes and footer.
- Track Record now follows the current definition: mean score percentile versus the share
  beating the benchmark, with a horizontal 50% line. It is not probability calibration.

If an adapter or shared component causes a problem, report the concrete regression. Coordinate
changes to the shell, client, provider, global CSS or chart components with me and Tanhao.

## 5. Tanhao's work and my work

Tanhao reviews and extends your existing Regime, Track Record and Run Trace pages. They should
not create competing implementations. You do not need to rebuild those pages or take over C9.

I own integration conflicts, backend/service compatibility and final delivery coordination.
A is producing real data/sample artifacts; D is completing Zetaris, NIM recording and the
Meterless engines. Missing services, missing sample files or a missing cassette are not a
request for you to fabricate frontend results or implement a backend.

## 6. Verification and evidence

Before a fix PR, run:

```text
npm test
npm run check:contracts
npm run build
```

The integration baseline recorded 56 passing unit tests, successful contract/build checks,
17/17 original browser groups and 18/18 redesign groups. Those are baseline results, not a
claim about a later change you make. Preserve the existing assertions and report your own
actual command output.

For the pages you review or change:

- Walk through the main controls using the keyboard; confirm visible focus and no trap.
- Check 1440px, 768px and 320px layouts, with tables scrolling inside their containers.
- Check reduced motion and the chart data alternatives.
- Use Lighthouse and axe if available: the acceptance targets remain Accessibility >= 95
  and zero critical/serious axe findings. Report the real results and remaining issues.
- Tell me which native screen-reader and browser-zoom checks you can actually perform.
  I will coordinate coverage for unavailable tools. Chromium ARIA snapshots and text
  enlargement do not count as NVDA/VoiceOver or native browser-zoom evidence.

Reuse existing captures where they still describe the same source/build. Label older evidence
as baseline evidence; update captures for changed pages. Fresh integration captures also exist
on my machine. You do not need to recreate the entire earlier screenshot collection.

## 7. Delivery and timing

Target: Saturday 24 October evening. Hard limit: Sunday 25 October, 23:59 UTC. These are for the
remaining review and focused fixes, not for repeating completed development. Report a setup,
baseline or contract blocker as soon as you identify it.

Send a short review summary even if no code change is needed:

```text
Baseline commit reviewed:
Pages and interactions checked:
Regressions or findings:
Fix branch / PR, if any:
Commands actually run and results:
Evidence available:
Checks not run / help needed:
```

For code fixes, one focused review PR is enough; use the applicable acceptance checklist and
include screenshots for changed pages. There is no need to recreate the old four-PR sequence.
Use only existing application dependencies, keep repository text in English, preserve data
provenance, and raise contract changes with me.

The task is to finish and review the product you already built. We are continuing your work.
