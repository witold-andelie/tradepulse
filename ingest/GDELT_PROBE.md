# GDELT one-year daily-tone probe

Run date: 2026-10-24. Requested period: 2025-10-23 through 2026-10-22 (365 calendar days).

**Result: partially confirmed.** NVDA and COHR returned daily observations spanning the requested year. AMD remains unverified because the service returned HTTP 429.

The successful responses have 345 observed days each (94.52% calendar-day coverage), with 20 dates absent. Missing dates were not filled with zero or carried forward. The responses alone do not establish whether every absent date represents no articles or unavailable data.

| Ticker | Year-spanning daily observations | Observed days | Missing days | Result |
| --- | --- | ---: | ---: | --- |
| NVDA | Yes | 345 | 20 | YES |
| COHR | Yes | 345 | 20 | YES |
| AMD | Not verified | 0 | unknown | BLOCKED |

## Exact queries

### NVDA

```text
https://api.gdeltproject.org/api/v2/doc/doc?query=%28NVDA+OR+NVIDIA%29&mode=timelinetone&format=json&timelinesmooth=0&startdatetime=20251023000000&enddatetime=20261022235959
```

Observed response: year_spanning_daily_observations_with_explicit_gaps.

### COHR

```text
https://api.gdeltproject.org/api/v2/doc/doc?query=%28COHR+OR+Coherent%29&mode=timelinetone&format=json&timelinesmooth=0&startdatetime=20251023000000&enddatetime=20261022235959
```

Observed response: year_spanning_daily_observations_with_explicit_gaps.

### AMD

```text
https://api.gdeltproject.org/api/v2/doc/doc?query=%28AMD+OR+%22Advanced+Micro+Devices%22%29&mode=timelinetone&format=json&timelinesmooth=0&startdatetime=20251023000000&enddatetime=20261022235959
```

Observed response: GET api.gdeltproject.org/api/v2/doc/doc failed: 429.

## Evidence and limits

- Computed results: `data/lake/_reports/gdelt_probe.csv`.
- Actual successful JSON and response bodies: `data/cache/gdelt/` (ignored production artifacts).
- Requests used the real configured contact identity, a five-second minimum spacing, bounded attempts and a cooldown before the final AMD retry. No alternate identity or proxy was used.
- No claim is made that GDELT satisfies a complete daily series for all three names. AMD requires a later permitted request or provider clarification.
- This is a history-availability probe, not a validated news factor. No shared table or API schema was added.
- No PR comment has been posted and no PR has been created. This file supplies reviewable probe evidence.
