# Sponsor integration: actual role and evidence

The accepted Crypto case is 2026-10-23-87de33aa. Its original input/output/trace are committed
and verified through docs/review/crypto-evidence.json. The lead's local Mac performed the
original real execution and API/UI checks; the read-only judge server makes no fresh calls.

| Technology | Evidence and role |
| --- | --- |
| Zetaris | Live data/evidence through allow-listed SQL templates; original full-template parity was separately measured 12/12. Saved Crypto is not a new parity run. |
| Meterless World Model / H-MEM | Real snapshot, recall and remember in the accepted trace. Official reference engines are upstream components with retained licenses/commit attribution. |
| Nightshift | Real provider connection/smoke and earlier Analyst/Skeptic calls. The earlier Crypto run abstained and failed full acceptance; separate late-runtime completion is not rewritten as a client success. |
| GLM-5.3-Flash | Six real model calls in the accepted Crypto trace. These calls are labelled glm, not Nightshift. |
| NVIDIA NIM | Nine real hosted calls to NVIDIA Nemotron 3.5 models (analyst and skeptic) in Crypto run 2026-10-23-b8637c6c on the committed sample snapshot; three explanations passed the verifier. That run used DuckDB and made no Zetaris or engine calls; the accepted Zetaris + Meterless case remains the GLM run. See [NIM evidence](../runs/nvidia-nim-crypto-1/README.md). |
| spacexsi, Cursor | No completed sponsor-use claim for this delivery. Historical plans or placeholders do not establish usage. |

## Organizer wording and honest disclosure

The latest reminder supplied by the lead explicitly lists Zetaris, a Meterless Engine in a
working feature, and Nightshift as an AI provider. The record above distinguishes completed
connections from the provider used by the accepted demonstrated request. The saved GLM case
alone does not prove that Nightshift generated that request. An internal engineering
acceptance profile is not a guarantee of organizer eligibility decisions.

## Actual deployment

Member D supplied no project code, working service or reviewable sponsor deliverable.
Wentao Ma completed all TradePulse-specific sponsor integration and deployment. The accepted
deployment runs locally on the lead's Mac:
Zetaris Docker, a separate official-engine sidecar, and the configured provider. No shared
AWS HTTPS endpoint or S3 upload is claimed.

Zetaris registered the unchanged seven-table real sample. The official helper and TradePulse
client executed real queries. Spark-compatible microsecond Parquet copies were registered
without overwriting source files. Earlier row-limit/timezone mismatches were diagnosed and
corrected; the original failed reports remain failed.

The engine sidecar uses official Meterless reference/conformance code at
1742dec56a66e58eef9dda2d2b865823758ca8cd. Its upstream LICENSE and NOTICE are retained.
H-MEM context is explicitly unverified historical context, not new claim evidence or a
record of profitable trading. World Model observations do not bypass research gates.

Nightshift M1-M4 Edition accepted actual provider requests. Its local small-model trials
had JSON, timing and evidence-quality problems. The team preserved these records and used
GLM for the accepted Crypto demonstration. We do not repair old responses, invent inference
receipts or relabel unavailable calls as passed.

## Reproduction

- No keys: use the exact saved artifact through scripts.review_demo.
- Offline math: recompute with SAMPLE_MODE=true and RECORD_LLM=false; missing models abstain.
- Fresh services: use the separate integration checkout and private settings in RUNNING.md.
  A fresh run is new evidence and may differ; never demand identical generated prose.
- Original sponsor source and notices: [integration checkout](https://github.com/witold-andelie/tradepulse/tree/194033a1d7f78d96e60ec16f28e633f8c81ebf29/integrations).

Do not publish environment files, proxy tokens, keys or personal contact data. Use your own
authorized service accounts. No raw credentials are needed for the public reviewer path.
