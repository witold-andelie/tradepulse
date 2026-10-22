# Instructions for AI coding agents working in `web/`

You are helping Member B build the TradePulse web app.

1. Read `web/TASK.md` and `web/ACCEPTANCE.md` first. The data shape is defined by
   `contracts/api/tradepulse.schema.json`. Never invent fields; if a field you need is missing,
   stop and say so.
2. Edit only files under `web/`. Never edit `contracts/`, Python code, or the given tests
   `web/src/lib/*.test.js`.
3. Use only the stack in `TASK.md`: React 18 with plain JavaScript (.jsx and .js, no TypeScript),
   Vite, React Router 6, Tailwind CSS, TanStack Table v8, ECharts via echarts-for-react, Vitest.
   Do not add dependencies without the team lead's approval.
4. Every number, ticker and sentence that describes a result must come from the run data. Never
   hard-code results.
5. Always render the data-mode banner from `dataModeBanner()` and the run's disclaimer. Never use
   "Buy"/"Sell" wording; use `tierLabel()`.
6. Pages get data only through `src/api/client.js`.
7. Run `npm test` and `npm run build` after every change. Fix every console error.
8. Write code, comments and UI text in English.
