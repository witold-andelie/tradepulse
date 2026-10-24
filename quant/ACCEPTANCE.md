# Acceptance — Member C (`quant/`)

The team lead merges a PR only when every item that applies is true.

C1–C7 are implemented. Apply this checklist to C9 and math changes. For B7–B9 review, retain
Huyin's existing pages and use `../web/ACCEPTANCE.md` as well. See `../docs/STATUS.md` for owners.

## Automated (must pass)

```
py -3 -m pytest quant -q                     # 0 failed, 0 skipped for the modules in this PR
py -3 -m ruff check quant                     # no errors
```

## Code checks

- [ ] No function name, argument or default value differs from the stub.
- [ ] No test under `quant/tests/` was changed or deleted.
- [ ] No look-ahead: only `forward_returns` uses negative shifts. Search for `shift(-`; it may
  appear only there.
- [ ] No I/O: no `open(`, `read_parquet`, `requests`, `print(` or environment variables in
  `quant/`.
- [ ] Inputs are not mutated. Functions work on copies, or build new objects.
- [ ] Each function body matches its docstring. When the code needed a decision the docstring did
  not cover, the decision is written into the docstring and called out in the PR description.
- [ ] Performance: a 520 × 520 random panel runs each function within the limits in `TASK.md`.
  Paste the timings into the PR.
- [ ] Everything is in English.

## PR checklist (copy into the PR description)

```
- [ ] module(s): C?
- [ ] tests: <paste pytest summary line>
- [ ] ruff: clean
- [ ] timings on 520x520: <function: seconds>
- [ ] decisions not covered by docstrings: <list or "none">
```
