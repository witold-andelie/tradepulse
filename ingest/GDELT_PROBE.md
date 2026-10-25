# GDELT one-year daily-tone probe

Fresh lead verification for decision date 2026-10-23. Requested period: 2025-10-23 through 2026-10-22.

All three queries returned year-spanning daily observations after a later permitted retry. Initial HTTP 429 failures were not treated as data. Successful responses still have explicit gaps, which were not filled.

| Ticker | Status | Observed days | Missing calendar days | Calendar-day coverage |
| --- | --- | ---: | ---: | ---: |
| NVDA | YES | 345 | 20 | 94.52% |
| AMD | YES | 345 | 20 | 94.52% |
| COHR | YES | 345 | 20 | 94.52% |

`YES` means year-spanning daily resolution with explicit gaps. It does not mean every calendar day exists or that an absent day means zero articles.

## Exact queries

### NVDA

```text
https://api.gdeltproject.org/api/v2/doc/doc?query=%28NVDA+OR+NVIDIA%29&mode=timelinetone&format=json&timelinesmooth=0&startdatetime=20251023000000&enddatetime=20261022235959
```

### AMD

```text
https://api.gdeltproject.org/api/v2/doc/doc?query=%28AMD+OR+%22Advanced+Micro+Devices%22%29&mode=timelinetone&format=json&timelinesmooth=0&startdatetime=20251023000000&enddatetime=20261022235959
```

### COHR

```text
https://api.gdeltproject.org/api/v2/doc/doc?query=%28COHR+OR+Coherent%29&mode=timelinetone&format=json&timelinesmooth=0&startdatetime=20251023000000&enddatetime=20261022235959
```

## Evidence and limits

- Computed source report is delivered in `data/sample/provenance/gdelt_probe.csv`.
- Successful JSON and response bodies remain in ignored `data/cache/gdelt/`.
- Requests used the configured contact identity, five-second minimum spacing, bounded attempts and cooldowns. No alternate identity or proxy was introduced.
- Missing dates remain missing. No complete calendar series, validated news factor, new shared table or predictive result is claimed.
