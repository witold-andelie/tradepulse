# Member C — Quant library (`quant/`)

> **Status (2026-10-23): C1–C7 are implemented and merged.** Every module lies on the critical
> path of the pipeline, so the lead completed them with a coding agent against the acceptance tests
> in `quant/tests/` (54 passing). Read the code to learn how each formula was vectorised.
>
> **Your tasks now:**
> 1. **C9 · Property tests** (below). Add new test files only; do not edit the given ones.
> 2. **Web pages B7–B9** (Regime, Track Record, Run Trace). They are described in `web/TASK.md`.
>    Coordinate with Member B on shared components, and follow `web/ACCEPTANCE.md`. Use the branch
>    prefix `c/`, for example `c/b8-track-record`.

You write the **math** of TradePulse as small, pure, tested functions:

- indicators
- cross-sectional transforms
- factor evaluation
- costs
- earnings surprise
- regime indicators
- settlement scoring

The team lead wires them into the pipeline. You never touch files, the network, LLMs or
configuration. Data comes in as pandas objects, and results go out as pandas objects.

- Architecture view: the orange boxes in `docs/architecture/opm/svg/SD1.4_researching_factors.svg`,
  `SD1.5_regime_ranking.svg` and `SD1.2_settling.svg`.
- Formulas and the reasoning behind them: `docs/architecture/factors.md`. Read the
  "measuring ≠ predicting ≠ earning" section first.

## What you own

```
quant/
  indicators.py         C1  per-instrument time series
  crosssection.py       C2  per-date transforms
  evaluation.py         C3  forward returns, IC, IC decay, long-short, lead-lag
  costs.py              C4  cost model, expected alpha (Grinold)
  earnings.py           C5  first-reported EPS, quarterly EPS, SUE, event panels
  regime_indicators.py  C6  fragility indicators
  settlement.py         C7  hit, Brier score, calibration
  tests/                acceptance tests (given; do not weaken them)
```

Do **not** edit anything outside `quant/`. If a test looks wrong, tell the team lead. Do not change
the test.

## Setup

```
py -3 -m pip install -e ".[dev]"
py -3 -m pytest quant -q          # every test is red until you implement the functions
```

Work one module at a time, in the order C1 → C7. Run its test file after every change, for example
`py -3 -m pytest quant/tests/test_indicators.py -q`.

## Data shapes

- A **panel** is a `pandas.DataFrame` with a sorted `DatetimeIndex` (one row per trading day) and
  one column per symbol.
- A **series** is one column of a panel.
- Missing data is `NaN`. Never fill it with zeros or the last value, unless the docstring says so.

## Rules that every function must follow

1. **No look-ahead.** A value at row `t` may only use rows `<= t`. `test_no_look_ahead` checks this
   by changing the last row and asserting that nothing earlier moves. The only exception is
   `evaluation.forward_returns`, which builds the evaluation target.
2. **Full windows only:** rolling windows use `min_periods = window`.
3. **Pure functions:** never modify the inputs. Do not print, do not read files, do not use global
   state.
4. **Vectorise with pandas or numpy** where you can. The real panels have about 520 columns and
   about 520 rows. A function over a whole panel must finish in under 2 seconds, except
   `residualize_cs` and `rank_ic`, which have 10 seconds.
5. **Return types exactly as documented.** Use plain Python `bool` and `float` where the docstring
   says so; tests use `is True`.
6. **Docstrings are the spec.** If the docstring and a test disagree, ask the team lead.

## Tasks

| id | module | functions | notes |
|---|---|---|---|
| C1 | `indicators.py` | `simple_returns`, `momentum`, `reversal`, `realized_vol`, `volume_zscore`, `distance_to_high`, `moving_average`, `rolling_beta`, `attention_change` | `volume_zscore` excludes row t from its own baseline. `attention_change` lags by one row because pageviews of day t are not known at the close. |
| C2 | `crosssection.py` | `winsorize_cs`, `zscore_cs`, `rank_pct_cs`, `neutralize_groups`, `residualize_cs` | Work row by row (one date at a time). `residualize_cs` is an OLS with an intercept: use `numpy.linalg.lstsq`. |
| C3 | `evaluation.py` | `forward_returns`, `rank_ic`, `ic_summary`, `ic_decay`, `same_day_ic`, `quantile_long_short`, `half_split_sign_agreement`, `lead_lag_tstat` | `ic_summary` samples every h-th IC so overlapping returns do not inflate the t-stat. `quantile_long_short` charges cost on turnover. |
| C4 | `costs.py` | `round_trip_bps`, `turnover`, `cost_return`, `expected_alpha_bps`, `net_edge_bps` | Grinold: α = IC · σ · z. |
| C5 | `earnings.py` | `first_reported`, `quarterly_eps`, `sue`, `event_panel` | Use the first-reported value only; restated values leak the future. |
| C6 | `regime_indicators.py` | `below_ma`, `term_structure_ratio`, `avg_pairwise_corr`, `breadth_above_ma`, `rolling_percentile`, `change`, `regime_points`, `classify_regime` | These feed the Paul Tudor Jones–style fragility monitor. |
| C7 | `settlement.py` | `excess_return`, `hit`, `brier_score`, `calibration_table` | These score past recommendations for the track record. |

## Stretch (only after C1–C7 are merged)

- **C8 · Performance:** profile `rank_ic` and `residualize_cs` on a random panel of 520 × 520 and
  make each one run in under 3 s.
- **C9 · Property tests:** add your own tests, for example that `zscore_cs` output has row
  mean ≈ 0 and std ≈ 1. Put them in new files; do not edit the given ones.

## Definition of done

See `ACCEPTANCE.md`. Open one PR per module. Branch names are `c/<task>`, for example
`c/c1-indicators`.
