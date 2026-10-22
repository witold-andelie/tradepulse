# Acceptance — Member A (`ingest/`)

The team lead merges a PR only when every item that applies is true. Paste the command output
into the PR description.

## Automated (must pass)

```
py -3 -m pytest ingest -q                    # offline unit tests: 0 failed
py -3 -m ingest all --as-of 2026-10-21       # live run; ends with "all tables valid"
py -3 -m pytest ingest -q -m lake            # lake tests run (not skipped) and pass
py -3 -m pytest ingest/tests/test_sample.py  # sample snapshot exists and passes (must NOT skip)
```

## Data checks (paste numbers in the PR)

- [ ] `universe_member`:
  - us_equity has 500–530 rows, eu_equity 50–65, crypto 35–45
  - no stablecoins
  - every US row has a CIK
- [ ] `wikipedia_title` is non-null for at least 90% of rows in each pool.
- [ ] `price_bar`: at least 95% of members per pool have at least 95% coverage of the pool's trading
  days (from the coverage report). Every exception is listed and explained.
- [ ] `price_bar`: all reference symbols are present (SPY, ^VIX, ^VIX3M, ^STOXX50E, BTC-USD).
- [ ] `pageview`: rows exist for at least 90% of members, and the missing titles are listed.
- [ ] `filing`: at least 450 US members have at least one 8-K with item 2.02 in the window.
- [ ] `fundamental_fact`: at least 450 US members have `EarningsPerShareDiluted` facts.
- [ ] `filing_text`: every EX-99.1 row has a sha256 that matches its text, and `char_count > 500`.
- [ ] `acceptanceDateTime` timezone check is done and its result recorded (3 filings compared with
  their index pages).
- [ ] Nothing dated after `as_of` (validated with `as_of`).
- [ ] `data/sample/` is below 25 MB and validates.

## Code checks

- [ ] No function signature in the stubs was changed, and no test was weakened or deleted.
- [ ] Every request uses `build_session()` and a `RateLimiter`; SEC requests ≤ 8/s.
- [ ] Retries are limited (3 attempts with backoff). There are no infinite loops.
- [ ] No API key, e-mail address or token appears in code, tests, data or logs. `.env` is not
  committed.
- [ ] `data/lake/` is not committed; `data/sample/` is.
- [ ] Everything is in English.

## PR checklist (copy into the PR description)

```
- [ ] tests: <paste pytest summary line>
- [ ] live run: <paste last lines of `py -3 -m ingest all`>
- [ ] coverage exceptions: <list or "none">
- [ ] EDGAR timezone check: <result>
- [ ] sample size: <MB>
```
