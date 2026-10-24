# Factor and gate specification

This is the contract between research (team lead) and the `quant/` library (Member C).
Parameters live in `config/tradepulse.toml`. Code reads them from there.

## Implementation status

See [project status](../STATUS.md) and [limitations](../honest-limitations.md). Factor cards
show in-sample diagnostics; current ranking uses walk-forward weights and out-of-sample
composite IC. Event drift and relational spillover are excluded from walk-forward because
their priors/edges are fitted in-sample. The valuation constraint below is a target rule
that the current pipeline does not apply. Unsupported filing inputs stay visibly insufficient.

TrackRecord's `calibration` field holds mean score percentile (`predicted`) and the share of
names beating the benchmark (`observed`). The UI uses a horizontal 50% reference and omits
zero-observation buckets from the plot. These are not predicted probabilities or a probability
calibration result; the schema field names are retained for compatibility.

## Principle: measuring ≠ predicting ≠ earning

A signal can describe today's market well and still predict nothing. A factor can predict and still
lose its edge to costs. A strategy can make money for a reason other than the one in its name.
Every factor therefore answers four questions on its **factor card**:

1. **What exactly does it measure?** (definition, source, point-in-time availability)
2. **Does it add information beyond ordinary price-volume factors?** (residual IC)
3. **Does it predict the future, or explain a move that already happened?** (IC with execution
   lag vs same-day IC, and the IC decay curve)
4. **What is left after realistic costs?** (net long-short)

## Conventions

- A panel is a wide `pandas.DataFrame`: the index is a sorted `DatetimeIndex` (one row per trading
  day of the pool) and the columns are symbols.
- `rows_per_year` is 252 for equities and 365 for crypto; `rows_per_month` is 21 or 30.
- Each factor is **oriented so that higher means higher expected return**.
- A value at row `t` may only use information **available at the close of `t`**. A source that is
  published after the close (for example the pageviews of day `t`) is lagged by one row.
- `fwd_h(t) = P[t+L+h] / P[t+L] - 1` with execution lag `L = 1`. `quant.evaluation` constructs
  forward targets; `tradepulse.backtest` reads realized outcomes after fixing each simulated
  decision. Neither path may feed future outcomes into that decision's features or weights.

## Factor catalogue (P0)

| id | pools | measures | definition (row t) | availability |
|---|---|---|---|---|
| `pv_mom_12_1` | all | 12-month trend, skipping the last month | `P[t-m]/P[t-y] - 1` (m = month rows, y = year rows) | close t |
| `pv_mom_1m` | all | 1-month trend | `P[t]/P[t-m] - 1` | close t |
| `pv_rev_5d` | all | short-term reversal | `-(P[t]/P[t-5] - 1)` | close t |
| `pv_lowvol_20d` | all | low-volatility premium | `-std(r[t-19..t], ddof=1) * sqrt(rows_per_year)` | close t |
| `pv_volume_z` | all | abnormal trading activity | `(log V[t] - mean(log V[t-60..t-1])) / std(log V[t-60..t-1], ddof=1)` | close t |
| `pv_dist_52w_high` | all | anchoring to the 52-week high | `P[t]/max(P[t-y+1..t]) - 1` | close t |
| `att_pageviews` | all | abnormal public attention | `log1p(mean views over [t-7..t-1]) - log1p(mean views over the 83 rows before that)`, then residualised on `abs(5d return)`, `pv_volume_z`, `pv_lowvol_20d` | day t-1 |
| `earn_sue` | us_equity | earnings surprise | seasonal random-walk SUE from diluted EPS (see below), held for 60 rows after filing | filing acceptance + 1 row |
| `earn_demand_language` | us_equity | management says demand > supply | signed intensity in [-1, 1] from the extractor on 8-K Item 2.02 exhibit 99.1, held for 60 rows | acceptance + 1 row |
| `evt_drift` | us_equity | post-event drift | `Σ_e prior(type_e) · dir_e · exp(-(t-d_e)/10)` over events with `1 <= t-d_e <= 20` | acceptance + 1 row |
| `rel_spillover` | all (cross-pool edges allowed) | shocks at linked companies not yet priced | `Σ_j w_ij · shock_j[t-1] / Σ_j abs(w_ij)`; `shock_j` = sum of beta-adjusted residual returns over `[t-5, t-1]`, z-scored; only edges with `validated` and `valid_from <= t` | close t-1 |

Control variables (not alpha, used only for residualising and neutralising): `pv_beta_252`, sector
dummies (US: GICS sector; EU: industry; crypto: no sector neutralising).

Valuation constraint (US only, not a factor): `val_ps_pctile` is the cross-sectional percentile of
market cap / TTM revenue. Market cap = `dei:EntityCommonStockSharesOutstanding` × price.

P1, shown as `MEASURED_ONLY` until history exists: `soc_stocktwits` (bull/bear ratio of recent
messages) and `news_tone`. Free social APIs return only the most recent messages, so these factors
cannot be back-tested within a one-year window. Their cards say so.

### SUE detail

- From the XBRL fact `us-gaap:EarningsPerShareDiluted`, keep quarterly durations (80–100 days).
- Derive Q4 as `FY - (Q1 + Q2 + Q3)` when the 10-K reports only the annual figure.
- When the same period is reported several times, keep the **first** filing. This is what the
  market saw; restated values would leak.
- `d_q = EPS_q - EPS_{q-4}`; `SUE_q = d_q / std(d over the previous 4–8 quarters, ddof=1)`.
  The result is NaN when fewer than 4 previous diffs exist or when the std is 0.

### Event priors

`prior(type)` is the mean beta-adjusted abnormal return over rows +1..+5 after events of that type
inside the **training part** of the window. The return on row 0 is excluded because it cannot be
captured. The mean is shrunk: `prior = n/(n+20) · mean`.

## Pipeline per factor and pool

`raw → winsorise (±3σ per date) → z-score per date → sector-neutralise (equity pools)
→ residualise on the price-volume baseline (for non-baseline factors) → evaluate → gate → weight`

## Gates

| gate | name | passes when |
|---|---|---|
| G1 | measure | the spec row above is complete, and coverage (non-null share of pool-days) >= `min_coverage` |
| G2 | incremental | the t-stat of the mean rank IC of the **residualised** factor at its best horizon is >= `min_incremental_ic_t`. Baseline factors are residualised on sector only. |
| G3 | predictive | the mean rank IC at `primary_horizon` (with the execution lag) is > 0. The card also shows same-day IC; when same-day IC exceeds 3× the predictive IC, it labels the factor "mostly descriptive". |
| G4 | net of cost | the annualised Sharpe of the net quintile long-short (equal weight, rebalanced every `primary_horizon` rows, cost = turnover × `cost_bps_one_way`) is >= `min_net_sharpe` |
| G5 | consistency | the mean IC has the same sign in the first and second half of the window |

The t-stat uses non-overlapping observations (every h-th date) for horizon h.

- Card status is `INSUFFICIENT_DATA` if G1 fails or fewer than 40 dates are valid.
- It is `MEASURED_ONLY` if any of G2–G5 fails.
- Otherwise it is `ACTIVE`.

**Weights:** `w_f ∝ max(0, IC_IR_f)` over ACTIVE factors. They are then shrunk halfway toward equal
weights (`ic_weight_shrinkage`). Inactive factors get weight 0, and their card is still shown.

**Two evaluation modes, labelled honestly:**

- *Research cards* use the full one-year window. They are in-sample and say so.
- *Track record / settlement* is walk-forward. Weights on date t use only data up to
  `t - h - L`, with an expanding window that starts after 120 rows.

## From score to recommendation

- `score_i = Σ_f w_f · z_f,i`. A missing factor contributes 0.
- `coverage_i = Σ_{f present} w_f`. When `coverage_i < 0.5` the tier is `NO_CALL`.
- `α_i (bps) = IC_comp · σ_i,daily · sqrt(h) · score_i · 1e4`, where `IC_comp` is the walk-forward
  rank IC of the composite (Grinold: α = IC · σ · z). If `IC_comp <= 0`, every name in the pool is
  `NO_CALL`.
- `net_edge_bps = sign(α) · (abs(α) - 2 · cost_bps_one_way)`.

Tiers are assigned by score percentile within the pool:

| tier | rule |
|---|---|
| `STRONG_OVERWEIGHT` | top 5% and net edge >= 2× round-trip cost; downgraded to OVERWEIGHT when US `val_ps_pctile > 0.90` |
| `OVERWEIGHT` | top 20% and net edge >= 1× round-trip cost |
| `UNDERWEIGHT` | bottom 20% and net edge <= -1× round-trip cost |
| `AVOID` | bottom 5% and net edge <= -2× round-trip cost |
| `NEUTRAL` | everything else |
| `NO_CALL` | coverage < 0.5, `IC_comp <= 0`, or a data/verification failure |

**Regime overlay:**

- *elevated*: STRONG_OVERWEIGHT → OVERWEIGHT.
- *stressed*: every overweight tier drops one notch, and the report adds a hedge note (benchmark
  exposure, cash).

Underweight tiers are unchanged. Tiers are research stances, **never orders**.

## Regime (fragility monitor, after Paul Tudor Jones)

Black swans cannot be timed. The monitor measures **fragility**: conditions in which large
drawdowns become more likely and more damaging. Each indicator that triggers adds 1 point.

| indicator | equity pools | crypto |
|---|---|---|
| trend | benchmark close < 200-day MA | BTC close < 200-day MA |
| volatility | VIX / VIX3M > 1.0 (term-structure inversion) | BTC 20d realised vol in the top 10% of its 1-year range |
| correlation | 20d mean pairwise correlation of the pool in the top 10% of its 1-year range | same |
| breadth | share of the pool above its 200-day MA < 40% | same |
| credit | 20-day change in US high-yield OAS > +75 bp | same (shared) |

States: 0–1 points is *normal*, 2–3 *elevated*, 4–5 *stressed*.

The monitor is evaluated only as **lift**: P(benchmark drawdown over the next 20 rows > X | state)
divided by the unconditional probability. X is 7% for equities and 20% for crypto. A one-year window
contains few stress episodes, so the lift is reported with its sample size and never as a forecast.
