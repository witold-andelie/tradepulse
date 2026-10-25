# Computed real-snapshot examples

These three independent requests were executed against the frozen 2026-10-23 real sample,
with all socket connection/DNS calls blocked. Zero network attempts occurred. Inputs and
financial outputs were computed, not typed into fixtures or substituted in the UI.

| Pool | Recommendation records | Factor cards | Explanation verdicts |
| --- | ---: | ---: | --- |
| US equities | 523 | 11 | 3 abstained |
| European equities | 55 | 11 | 3 abstained |
| Crypto | 38 | 11 | 3 abstained |

Every record in these runs is NO_CALL. No factor passes all gates, and no matching model
cassette is present. These examples therefore establish offline data processing, contract
validity and honest abstention, not successful model inference, hosted sponsor acceptance
or predictive performance. All source limitations in the sample manifest still apply.

Each pool folder contains `input.json`, `output.json` and `trace.jsonl`:

- [US input](us_equity/input.json), [output](us_equity/output.json), [trace](us_equity/trace.jsonl)
- [European input](eu_equity/input.json), [output](eu_equity/output.json), [trace](eu_equity/trace.jsonl)
- [Crypto input](crypto/input.json), [output](crypto/output.json), [trace](crypto/trace.jsonl)

[manifest.json](manifest.json) records hashes, sizes, run identities and measured counts.
Trace bytes are unchanged. Only each output's `trace_path` was relocated to the packaged
trace, making the reference portable. The original path is retained in the manifest.

Recompute to a new destination from the repository root:

```powershell
$env:SAMPLE_MODE = "true"
$env:RECORD_LLM = "false"
py -3 -m scripts.generate_examples --offline-check --output examples-refreshed
```

The command refuses to overwrite an existing destination. It validates the frozen sample,
RunRequest, RunOutput and each TraceEvent, scans for source contact addresses, and fails if
any network connection is attempted. New run IDs, creation times and trace durations will
differ; do not compare those fields as deterministic financial results. Refresh examples
after D supplies a genuine cassette and repeat the offline acceptance.
