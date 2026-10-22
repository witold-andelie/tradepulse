# Instructions for AI coding agents working in `quant/`

You are helping Member C implement the quantitative library of TradePulse.

1. Read `quant/TASK.md` and `quant/ACCEPTANCE.md`, then the docstring of the function you are
   implementing. The docstring is the specification.
2. Edit only files under `quant/`, except `quant/tests/test_*.py` files that already exist. Never
   change a given test. If a test seems wrong, stop and explain why.
3. Keep every function name, argument and default exactly as in the stub.
4. Functions are pure: pandas and numpy in, pandas and numpy out. No file, network, print, global
   state or environment access.
5. No look-ahead. Row t may only use rows <= t. Never use `shift(-n)` outside
   `evaluation.forward_returns`.
6. Rolling windows use `min_periods=window`. Never fill missing data unless the docstring says so.
7. Return Python `bool` and `float` where the docstring says so.
8. Use `py -3` to run Python on this machine. Run `py -3 -m pytest quant -q` after every change.
9. Write code, comments and messages in English.
