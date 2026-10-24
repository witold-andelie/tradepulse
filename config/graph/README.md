# Seed edges

`seed_edges.csv` lists **hypotheses**, not established relationships or causal facts.
`tradepulse.research.signals.validate_edges` applies the lead-lag test from
`quant.evaluation.lead_lag_tstat`. The current pipeline fits seed edges on the research window
and discloses this as in-sample. Relational spillover is excluded from walk-forward ranking;
World Model persistence and point-in-time graph snapshots are still pending.
See [current status](../../docs/STATUS.md) and [limitations](../../docs/honest-limitations.md).

Reading an edge: **`dst` `relation` `src`**. Shocks flow from `src` (the leader) to `dst` (the
follower).

- `MSFT,NVDA,supplier_of` reads "NVDA is a supplier of MSFT". A capex shock at MSFT may reach NVDA.
- `BTC-USD,MSTR,holds_asset` reads "MSTR holds the asset BTC".

`weight` is a prior strength in [-1, 1]. The validation step may down-weight an edge or reject it.
Every symbol that appears here is a **showcase name**: `ingest/` downloads its latest 10-K text, and
the demo walks through its chain.
