# Instructions for AI coding agents working in `web/`

You are helping Member B maintain Huyin's implemented TradePulse web app, or Member C review
its existing B7–B9 pages. Read `docs/STATUS.md` and `web/INTEGRATION.md`; do not recreate the base.

1. Read `web/TASK.md` and `web/ACCEPTANCE.md` first. The data shape is defined by
   `contracts/api/tradepulse.schema.json`. Never invent fields; if a field you need is missing,
   stop and say so.
2. Edit only files under `web/`. Never edit `contracts/`, Python code, or the given tests
   `web/src/lib/*.test.js`.
3. Use only the stack in `TASK.md`: React 18 with plain JavaScript (.jsx and .js, no TypeScript),
   Vite, React Router 7, Tailwind CSS 3, TanStack Table v8, ECharts via echarts-for-react, Vitest.
   Security maintenance on 2026-10-25 upgraded existing libraries; see `DEPENDENCIES.md`.
   Do not add dependencies without the team lead's approval.
4. Every number, ticker and sentence that describes a result must come from the run data. Never
   hard-code results.
5. Always render the data-mode banner from `dataModeBanner()` and the run's disclaimer. Never use
   "Buy"/"Sell" wording; use `tierLabel()`.
6. Pages get data only through `src/api/client.js`. Use the shared provider and validated UI
   functions; legacy named transport functions remain for compatibility, not as a way to
   bypass schema validation. Keep the existing `*Page` adapters and both hook import paths.
7. Run `npm test` and `npm run build` after every change. Fix every console error.
8. Write code, comments and UI text in English. The lead-approved exception is localized labels
   inside `src/components/agentResearch/` only. Keep source narratives and financial values
   unchanged; the rest of the application stays in English. See `AGENT_ACCESSIBILITY_DEMO.md`.
9. Follow the "Accessibility (WCAG 2.2 AA)" section of `web/TASK.md` on every page: semantic
   markup, keyboard operability, visible focus, text alternatives for charts, no colour-only
   signals, sufficient contrast, reduced-motion support.
10. Preserve Huyin's pages, Simple/Pro, Discover and original test assertions. `App.jsx` owns
    the single main landmark and global disclosures. `Chart` delegates to `ChartFigure`;
    reuse the modular renderer and numeric alternatives rather than adding another UI base.
