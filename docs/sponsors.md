# Sponsor integration and evidence status

Status: 24 October 2026. This is an evidence-tracking draft, not a claim that all sponsor
requirements are complete. See [project status](STATUS.md) and
[Member D's acceptance checklist](../integrations/ACCEPTANCE.md).

## Zetaris

Intended load: the live federated query layer over the lake and on-demand EDGAR data.
It supports acquisition/registration and evidence queries in the target OPM model.

Implemented code: typed SQL templates, registration runner, result hashing, dtype coercion
and the offline DuckDB adapter in `integrations/zetaris/`. The live client and adapter remain
unimplemented. DuckDB tests are evidence for the offline path, not proof of Zetaris use.

Required evidence: AWS deployment and Europe smoke test, table registration, a sanitized
real response, every-template hash parity, pagination, and one out-of-universe EDGAR lookup.
D owns these items. No deployment endpoint or credential is published here.

## Meterless

Intended load: World Model maintains validated relations/events and as-of snapshots; H-MEM
maintains recommendations, matured feedback and conflicts. These correspond to Extracting &
Linking, Settling and the evidence/memory parts of the target recommending flow.

Implemented code: the Python HTTP client and contract checks in
`integrations/meterless/engines_client.py`, plus the target HTTP specification.
The official engines, TypeScript sidecar, persistence, conformance output and core wiring are
still pending. A mocked HTTP client test does not establish actual engine execution.

Required evidence: vendor commit/LICENSE/NOTICE, unchanged official engine implementations,
conformance suites, sidecar smoke/persistence/as-of/conflict tests, local Compose operation,
and secured shared hosting. D delivers the sidecar; the lead connects it to the pipeline.

## NVIDIA NIM

D18 routes every configured LLM role to hosted NIM by default. The extractor/guard route uses
`NIM_EXTRACTOR_MODEL`, analyst uses `NIM_ANALYST_MODEL`, and skeptic uses
`NIM_SKEPTIC_MODEL`. The current request guard itself is deterministic.

Implemented code: OpenAI-compatible hosted routes, bounded calls and hash-keyed record/replay.
Actual model choices, live grounding/JSON smoke tests and a recorded sample cassette remain
pending. Analyst and skeptic must use different model families.

Required evidence: agreed model IDs, live smoke output, and a matching cassette/cache for A's
snapshot. An offline replay of the same decision date must not report unavailable answers.

## Runtime and disclosure

Meterless Nightshift/local GGUF routing is optional and off by default. It is not the primary
LLM path and is not the claimed Meterless load. No local-first inference credit is claimed.

Offline frontend and Python checks establish code behavior on fixtures/test inputs.
They do not substitute for the sponsor evidence above. Attach only genuine command outputs,
screenshots and trace excerpts after the corresponding services have actually run.
