# Instructions for AI coding agents working in `quant/`

You are helping Member C implement the quantitative library of TradePulse.

C1–C7 already exist. Current work is C9 property coverage and review of Huyin's existing B7–B9
pages; read `docs/STATUS.md`. Do not build a competing frontend implementation.

1. Read `quant/TASK.md` and `quant/ACCEPTANCE.md`, then the docstring of the function you are
   implementing. The docstring is the specification.
2. Quant work stays under `quant/`; never change a given test. The assigned web review may edit
   existing Regime, TrackRecord and Trace page files and their `*Page` adapters under `web/`,
   after reading its TASK/ACCEPTANCE/AGENTS files. Coordinate shared UI changes with B and the
   lead. No contracts, core, ingestion or integration changes. If a test seems wrong, say so.
3. Keep every function name, argument and default exactly as in the stub.
4. Quant functions are pure: pandas and numpy in, pandas and numpy out. No file, network, print, global
   state or environment access.
5. No look-ahead. Row t may only use rows <= t. Never use `shift(-n)` outside
   `evaluation.forward_returns`.
6. Rolling windows use `min_periods=window`. Never fill missing data unless the docstring says so.
7. Return Python `bool` and `float` where the docstring says so.
8. Use `py -3` for Python. Run `py -3 -m pytest quant -q` for quant changes; web changes require
   `npm test`, `npm run check:contracts`, `npm run build` and applicable browser checks in `web/`.
9. Write code, comments and messages in English.
