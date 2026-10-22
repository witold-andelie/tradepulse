# Seed edges

`seed_edges.csv` lists **hypotheses** for the relation graph. These edges are not facts. An edge
enters the graph with `status = validated` only when it passes the lead-lag test in
`quant.evaluation.lead_lag_tstat`. That test runs on the training part of the one-year window
(SD1.3).

Reading an edge: **`dst` `relation` `src`**. Shocks flow from `src` (the leader) to `dst` (the
follower).

- `MSFT,NVDA,supplier_of` reads "NVDA is a supplier of MSFT". A capex shock at MSFT may reach NVDA.
- `BTC-USD,MSTR,holds_asset` reads "MSTR holds the asset BTC".

`weight` is a prior strength in [-1, 1]. The validation step may down-weight an edge or reject it.
Every symbol that appears here is a **showcase name**: `ingest/` downloads its latest 10-K text, and
the demo walks through its chain.
