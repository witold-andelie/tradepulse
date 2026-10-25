# Member B — Web app (`web/`)

Huyin's detailed current assignment is [HUYIN_NEXT_STEPS.md](HUYIN_NEXT_STEPS.md).
It supersedes the earlier message asking for three new placeholder implementations.

Lead QA update, 25 October: fresh real-sample API and container journeys now pass nine browser
groups in Simple/Pro at 1440/320 px. Frontend tests: 89 passed; original tests unchanged.
REPLAY is an execution mode, not proof that model recordings exist. The UI keeps this
distinction explicit. See `../docs/validation/README.md`; the new guide's actual screen-reader
and audible voice checks remain pending. No page rebuild is required.

> **Main baseline (2026-10-24): Huyin has already implemented B1–B10.** Integration `aaf3b5f`
> preserves her original commits, six business pages, Discover, Simple/Pro presentation,
> keyboard interactions, numeric chart alternatives and accessibility work. The pages are
> no longer placeholders. See `INTEGRATION.md` for provenance, and `docs/STATUS.md` for current
> project dependencies and acceptance. Continue from main rather than the older UI branches.
> - **Huyin:** review the integrated visual design and interactions; address specific review
>   findings and help attach existing evidence. Do not rebuild B4–B6 or another shared base.
> - **Tanhao:** review and improve the existing B7–B9 pages; do not build competing copies.
> - **Lead:** owns baseline integration, backend compatibility and final acceptance.
>
> The agreed `*Page` exports and props remain available as adapters to Huyin's implementations.
> The application shell owns the single main landmark, provenance, Run notes and footer.
> Existing pages use `PageTitle`; new page content can use `<Page title="...">` without
> duplicating the shell. Both use the same heading and focus implementation.
> **Every chart uses `src/components/ChartFigure.jsx`**; Huyin's `Chart` import delegates to it.
> New figures support these props:
> - `title`
> - `summary`: a sentence computed from the data
> - `option`: the ECharts option
> - `columns` and `rows`: the table view
> - `height` and `onEvents`, optional
>
> Existing figures retain their adjacent numeric tables/disclosures and keyboard filters.
> Shared rendering provides ARIA defaults and reduced motion; independent accessibility
> acceptance is still required.
> Run `npm install` once. On this team's machines, set `npm_config_cache` to a folder on D:.

You build what customers and judges actually **see**: a ranked list of hundreds of stocks and coins,
an explanation for each one, and the evidence that the engine is honest. The whole app is built
against the **contract fixtures**. You do not need the engine running; the data has the same
shape either way.

- Architecture view: `docs/architecture/opm/svg/SD3_browsing.svg` (the green boxes are yours).
- Data contract: `contracts/api/tradepulse.schema.json`, explained in `contracts/README.md`.
- Example data: `contracts/fixtures/run_output.fixture.json` (620 rows) and `trace.fixture.jsonl`.
  Import them as `@contracts/fixtures/...`.

## Stack (already decided — do not add frameworks)

| need | use |
|---|---|
| UI | React 18, **plain JavaScript (.jsx / .js)**, function components and hooks |
| build/dev | Vite |
| routing | React Router 7 (`createBrowserRouter`); the existing v7-ready routes are preserved |
| styling | Tailwind CSS (utility classes; no other CSS framework) |
| tables | TanStack Table v8 (sorting, filtering, pagination) |
| charts | Apache ECharts via `echarts-for-react` |
| tests | Vitest |

The lead's 25 October security maintenance upgraded existing libraries to fixed releases;
it did not add a UI framework or change API/table schemas. Use Node 22.12+ within the 22 LTS
line, Node 24+, or the supported Node 20.19+ line. See [dependency policy](DEPENDENCIES.md).

## Setup

```
cd web
npm install
npm run dev               # http://localhost:5173
npm test                  # existing unit/regression tests
npm run check:contracts   # validates the fixtures against the schema
```

## Global rules

1. **Every number comes from data.** Never type a number, ticker or sentence into a component as if
   it were a result. Hard-coded outputs disqualify the project.
2. **Show the data mode, always.**
   - When `data_mode` is `SYNTHETIC`, a non-dismissable banner from `dataModeBanner()` appears at
     the top of **every** page.
   - When it is `REPLAY`, an info banner appears.
   - The run's `disclaimer` text is shown in the footer of every page.
3. **Tiers are stances, not orders.** Never write "Buy", "Sell" or "Trade now". Use `tierLabel()`.
4. **Colour is never the only signal.** Each tier badge shows its label text, and gate results show
   ✓ / ✗ / – plus text.
5. **No secrets, no tracking scripts, no external fonts or CDNs.** Everything is bundled.
6. **English only**, except localized labels in the Ticker Detail research guide approved by
   the lead on 2026-10-25. Its original source narratives, financial values and enums stay
   unchanged; this is not application-wide localization. See `AGENT_ACCESSIBILITY_DEMO.md`.

## Accessibility (WCAG 2.2 AA) — applies to every page

Accessibility is a first-class requirement, proposed by Huyin. The shared components (`Page`,
`Badge`, `State`) and the layout provide the site-wide parts. Every page adds the page-level parts.

**Site-wide (base):**
- `<html lang="en">`.
- A "Skip to main content" link as the first focusable element.
- Landmarks: `<header>`, `<nav aria-label="Primary">`, `<main id="main">`, `<footer>`.
- One `<h1>` per page, and headings that never skip a level.
- A visible focus ring on every interactive element; never use `outline: none` without a
  replacement.
- Loading and error states are announced: `<Loading>` uses `role="status"` and
  `aria-live="polite"`; `<ErrorState>` uses `role="alert"`.
- Respect `prefers-reduced-motion`: no chart or panel animation when it is set
  (`animation: false` for ECharts).
- The data-mode banner and the Run notes toggle are reachable and readable by keyboard and screen
  reader. The toggle uses `aria-expanded`.
- Route changes move focus to the new page's `<h1>` and update `document.title`
  ("Leaderboard · TradePulse").

**Every page:**
- **Colour is never the only signal:**
  - tiers, gates, regime states and verified/rejected badges always carry text or an icon with a
    text alternative
  - positive and negative numbers carry a sign (+ / −)
- **Contrast:** text at least 4.5:1, large text and UI parts at least 3:1, in both colours of every
  badge.
- **Keyboard:**
  - everything works without a mouse: tabs, filters, table sorting, row opening (Enter), the
    treemap filter, expanding claims, pagination
  - no keyboard traps
  - targets are at least 24×24 px
- **Tables:**
  - real `<table>` markup with `<th scope="col">` and a `<caption>` (can be visually hidden)
  - sortable headers are `<button>`s with `aria-sort` on the `<th>`
  - pagination states "Page X of Y"
- **Charts (ECharts):**
  - set `aria: { enabled: true, decal: { show: true } }`, so series also differ by pattern
  - every chart has a text alternative: a one-sentence `aria-label` summary computed from the data
    (e.g. "Composite IC, US equities: mean 0.031 over 52 dates"), plus a "Show data as table"
    toggle that renders the same numbers as an accessible table
  - the sector treemap's table view doubles as its keyboard-operable filter
- **Forms:** every input, select and multi-select has a visible `<label>`. Search results announce
  their count through an `aria-live="polite"` region ("37 results").
- **Text and zoom:** the layout works at 200% zoom and at 320 px width without losing content. Use
  `rem` units for text. Numbers use tabular figures.
- **Abbreviations:** IC, bp, SUE, OAS and VIX use `<abbr title="…">` on their first use per page.

## Shared interfaces (Member B and Member C build to these)

Huyin's existing implementation supplies B1–B10. Member C (Tanhao) reviews and maintains B7–B9.
Use the compatibility interfaces below when extending it; preserve existing functionality.

| piece | file | contract |
|---|---|---|
| run data hook | `src/api/useRunOutput.js` | `useRunOutput()` → `{ data, error, loading, reload }` (named export; needs `RunOutputProvider`, already in `App.jsx`). `data` is a RunOutput. |
| trace hook | `src/api/useTrace.js` | `useTrace(runId)` → `{ events, error, loading }`. `events` is a list of TraceEvent. |
| page wrapper | `src/components/Page.jsx` | `<Page title>` renders the shared heading and `children`. `App.jsx` owns provenance, Run notes, footer and the single main landmark. Existing pages use the same heading via `PageTitle`. |
| badge | `src/components/Badge.jsx` | `<Badge tone label />`. `tone` is one of the values `tierTone()` returns, plus `"info"` and `"warning"`. It always shows the text label. |
| card | `src/components/Card.jsx` | `<Card title>` → a white rounded panel. |
| empty or error state | `src/components/State.jsx` | `<Loading />` and `<ErrorState message onRetry />`. |
| pages | `src/pages/*Page.jsx` | The agreed prop signatures delegate to Huyin's existing pages. A page can use supplied props or the shared run provider. Keep these entry points for collaborators. |
| chart | `src/components/ChartFigure.jsx` | `<ChartFigure title summary option columns rows />`: data-derived summary, ECharts ARIA and decal patterns, reduced motion, "Show data as table". |

The shared base and all pages already exist. Extend them after reviewing the integration;
do not replace the client, shell or design system with another implementation.

**Run notes:** `run.warnings` lists the honest limitations of each run, for example in-sample
statistics and excluded factors. The application shell shows them as a collapsible Run
limitations panel with their count. Never hide them.

## Existing functionality and review checklist

The B1–B10 sections below define the behavior to preserve and review, not a request to implement
the same pages again. Work on a specific acceptance finding; the lead handles baseline issues.

### B1 · Helpers (`src/lib/`) — make the given tests green first

Maintain the existing `format.js`, `tiers.js` and `data.js` according to their comments. Tests:
`src/lib/*.test.js`.

### B2 · Data access (`src/api/client.js`)

The transport functions, strict `createClient`, validated UI entry points and shared hooks exist.
Keep schema validation at the UI boundary and cancellation/timeout behavior. Both hook import
paths use one provider. Loading shows a status; failures show a readable message and Retry.

### B3 · Layout and routing

- Existing shell: product name, pool tabs (US equities · European equities · Crypto), navigation
  to Discover, Factor Lab, Regime, Track Record and Run Trace, plus Simple/Pro presentation.
- Run info line: as_of, run_id, horizon, data mode.
- Routes:

  | path | page |
  |---|---|
  | `/` | redirect to `/pool/us_equity` |
  | `/pool/:pool` | Leaderboard |
  | `/ticker/:pool/:symbol` | Ticker Detail |
  | `/factors` | Factor Lab |
  | `/regime` | Regime |
  | `/track-record` | Track Record |
  | `/trace` | Run Trace |
  | anything else | Not Found page with a link home |

### B4 · Leaderboard (`/pool/:pool`)

- Pool header: label, benchmark, `n_ranked` of `n_members`, composite IC, and a **regime badge**
  (normal / elevated / stressed, with text).
- **Table** with TanStack Table, showing the pool's recommendations:
  - columns: rank, symbol, name, sector, tier badge, score, net edge (bp), expected alpha (bp),
    coverage, 1-day return
  - sortable on every numeric column
  - search box (symbol or name), sector dropdown, tier multi-select
  - pagination at 50 rows per page; it must stay smooth with 520 rows
- A row click opens Ticker Detail.
- **Sector heatmap:** an ECharts treemap with one block per sector (from `sectorSummary`). Size is
  the count; colour is the mean score on a diverging scale with a legend. Clicking a block filters
  the table.
- "Top 5" and "Bottom 5" cards above the table, each linking to its detail page.

### B5 · Ticker Detail (`/ticker/:pool/:symbol`)

- Header: symbol, name, sector, tier badge (and "adjusted by regime" when `regime_adjusted`),
  rank of n, score, expected alpha, cost, net edge, horizon.
- **Contributions chart:** horizontal bars from `contributionsSorted()`, positive and negative in
  different colours and labelled with factor names. A caption states that contributions sum to the
  score.
- **Explanation panel**, shown when `explanation_id` is set:
  - verdict (explained / abstained)
  - summary
  - each claim with a ✓ verified / ✗ rejected badge; expanding a claim shows its checks and its
    evidence (query template, params, rows sha256, source table, link if any)
  - counter-case list
  - ruled-out list
  - the models used
  - retries
- **Invalidation** and **What to watch** lists.
- An unknown symbol shows a friendly not-found message.

### B6 · Factor Lab (`/factors`)

- A pool selector and a card grid with one card per factor:
  - title and factor id
  - status badge (ACTIVE / MEASURED_ONLY / INSUFFICIENT_DATA)
  - weight and coverage
  - **five gate chips G1–G5**, each with name, ✓ / ✗ / – and value vs threshold
  - an IC decay bar chart (horizon 1/5/20, mean IC)
  - same-day IC, and a "mostly descriptive" warning when set
  - the long-short numbers
- A short intro at the top explains *measure ≠ predict ≠ earn*. Take the text from
  `docs/architecture/factors.md`, and mark it as explanatory text, not a result.
- The cards state "In-sample research window: start – end".

### B7 · Regime (`/regime`) — existing Huyin page, reviewed/extended by Member C

- One panel per pool with the state badge and points of 5.
- An indicator table: name, value, threshold, triggered ✓ / ✗ / –, note.
- A history line chart of points over time, with background bands for normal / elevated /
  stressed.
- The lift numbers, with the sentence: "Fragility is measured, not predicted. Lift is reported with
  its sample size."

### B8 · Track Record (`/track-record`) — existing Huyin page, reviewed/extended by Member C

- Window and settled/pending counts.
- A table by pool × tier: n, hit rate, mean excess (bp).
- A "score vs outcome" chart from `calibration`, with one bubble per bucket.
  - `predicted` is the mean **score percentile** of the bucket (x axis).
  - `observed` is the **share of names that beat the benchmark** (y axis).
  - Bubble size is `n`.
  - Draw a dashed 50% line; it marks what a coin flip would give.
  - Label the axes exactly like that. It is not a probability calibration, so do not call it one.
  - Skip buckets with `n = 0`.
- A composite IC line chart per pool.
- A label at the top: "Walk-forward: each decision used only data available at that time."

### B9 · Run Trace (`/trace`) — existing Huyin page, reviewed/extended by Member C

- A timeline (Gantt-style) of `node_start` / `node_end` pairs from `loadTrace()`, using ECharts
  custom series or stacked bars.
- An event list: seq, time, node, kind, status, model, tokens, message. Highlight `retry` and
  `error` rows. Filter by node and by kind.
- Totals: duration, LLM calls, tokens in and out.

### B10 · Review and polish the existing B1–B9 implementation

- Responsive down to 320 px width and 200% zoom (see Accessibility). The leaderboard table scrolls horizontally inside its card,
  never the page.
- Keyboard navigation: table rows are focusable, and Enter opens the detail page.
- `npm run build` has no warnings about chunks over 1 MB. Lazy-load ECharts pages if needed.

## Definition of done

See `ACCEPTANCE.md`. Open focused review/fix PRs, for example `b/ui-review` or
`c/b8-evaluation-review`. Preserve the integrated contributor history; do not re-split or
reimplement already delivered pages just to recreate the old task sequence.
