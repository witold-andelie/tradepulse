# Member B — Web app (`web/`)

> **Status (2026-10-23): the base is done and merged** (B1 helpers, B2 data access and hooks,
> B3 layout and routes, shared components, site-wide accessibility). Every route already renders
> an honest placeholder page wired to real data. Replace the placeholders:
> - **Huyin:** `LeaderboardPage({ run, pool })`, `TickerPage({ run, pool, symbol })`,
>   `FactorLabPage({ factorCards })` (B4–B6), then B10.
> - **Tanhao:** `RegimePage({ regimes })`, `TrackRecordPage({ trackRecord })`,
>   `RunTracePage({ events })` (B7–B9).
>
> Wrap each page in `<Page title="...">`. It already renders the data-mode banner, the `<h1>`
> (focused on navigation), the Run notes and the footer, so pages only add their own content.
> **Every chart uses `src/components/ChartFigure.jsx`**, with these props:
> - `title`
> - `summary`: a sentence computed from the data
> - `option`: the ECharts option
> - `columns` and `rows`: the table view
> - `height` and `onEvents`, optional
>
> That gives you the accessibility requirements for charts for free.
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
| routing | React Router 6 (`createBrowserRouter`) |
| styling | Tailwind CSS (utility classes; no other CSS framework) |
| tables | TanStack Table v8 (sorting, filtering, pagination) |
| charts | Apache ECharts via `echarts-for-react` |
| tests | Vitest |

## Setup

```
cd web
npm install
npm run dev               # http://localhost:5173
npm test                  # unit tests (red until B1 is done)
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
6. **English only.**

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

Member B (Huyin) owns the base: B1–B6 and B10. Member C (Tanhao) owns pages B7–B9. Both build
against the names below, so neither has to wait for the other.

| piece | file | contract |
|---|---|---|
| run data hook | `src/api/useRunOutput.js` | `useRunOutput()` → `{ data, error, loading, reload }` (named export; needs `RunOutputProvider`, already in `App.jsx`). `data` is a RunOutput. |
| trace hook | `src/api/useTrace.js` | `useTrace(runId)` → `{ events, error, loading }`. `events` is a list of TraceEvent. |
| page wrapper | `src/components/Page.jsx` | `<Page title>` renders the data-mode banner, the title, `children`, the run notes and the disclaimer footer. |
| badge | `src/components/Badge.jsx` | `<Badge tone label />`. `tone` is one of the values `tierTone()` returns, plus `"info"` and `"warning"`. It always shows the text label. |
| card | `src/components/Card.jsx` | `<Card title>` → a white rounded panel. |
| empty or error state | `src/components/State.jsx` | `<Loading />` and `<ErrorState message onRetry />`. |
| pages | `src/pages/*.jsx` | Each page is a component that takes its data as props (signatures in the status box above). The router in `App.jsx` wraps it with the hook. |
| chart | `src/components/ChartFigure.jsx` | `<ChartFigure title summary option columns rows />`: data-derived summary, ECharts ARIA and decal patterns, reduced motion, "Show data as table". |

B merges B1, B2, B3 and these shared components **first**. Until then, C may develop with the
fixture imported directly and switch to the hook when it lands.

**Run notes:** `run.warnings` lists the honest limitations of each run, for example in-sample
statistics and excluded factors. `Page` shows them as a collapsible "Run notes" panel above the
footer, collapsed by default and showing the count. Never hide them.

## Tasks

### B1 · Helpers (`src/lib/`) — make the given tests green first

Implement `format.js`, `tiers.js` and `data.js` exactly as their comments say. Tests:
`src/lib/*.test.js`.

### B2 · Data access (`src/api/client.js`)

Implement `loadRunOutput`, `loadTrace` and `requestRun` as described in the file. Add the
`useRunOutput()` and `useTrace()` hooks from "Shared interfaces". Every page uses them. Loading shows a
skeleton; an error shows the message and a Retry button.

### B3 · Layout and routing

- Top bar: product name, pool tabs (US equities · European equities · Crypto), links to Factor Lab,
  Regime, Track Record and Run Trace.
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

### B7 · Regime (`/regime`) — owned by Member C

- One panel per pool with the state badge and points of 5.
- An indicator table: name, value, threshold, triggered ✓ / ✗ / –, note.
- A history line chart of points over time, with background bands for normal / elevated /
  stressed.
- The lift numbers, with the sentence: "Fragility is measured, not predicted. Lift is reported with
  its sample size."

### B8 · Track Record (`/track-record`) — owned by Member C

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

### B9 · Run Trace (`/trace`) — owned by Member C

- A timeline (Gantt-style) of `node_start` / `node_end` pairs from `loadTrace()`, using ECharts
  custom series or stacked bars.
- An event list: seq, time, node, kind, status, model, tokens, message. Highlight `retry` and
  `error` rows. Filter by node and by kind.
- Totals: duration, LLM calls, tokens in and out.

### B10 · Polish (after B1–B9)

- Responsive down to 320 px width and 200% zoom (see Accessibility). The leaderboard table scrolls horizontally inside its card,
  never the page.
- Keyboard navigation: table rows are focusable, and Enter opens the detail page.
- `npm run build` has no warnings about chunks over 1 MB. Lazy-load ECharts pages if needed.

## Definition of done

See `ACCEPTANCE.md`. Open one PR per task, or per pair of small tasks. Branch names are `b/<task>`,
for example `b/b4-leaderboard`.
