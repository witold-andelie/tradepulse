# Security, lint and timestamp maintenance — 25 October 2026

The three maintenance items are complete. This evidence does not change hosted sponsor,
model-recording or native screen-reader acceptance status.

## Dependency audit and compatibility

The official npm registry audit fell from **15 findings** (two critical, five high, eight
moderate) to **zero across the full dependency graph**. The reports retain the original
advisories and final result: [before](npm-before.json), [after](npm-after.json).
No dependency class was omitted and no advisory ignore list was added. The selected existing
libraries, selector-parser override and Node support are documented in
[the dependency policy](../../../web/DEPENDENCIES.md).

The final source passes 89 frontend tests, fixture/trace contract validation and the production
build. The largest chunk is 672.22 kB. A clean `npm ci` and production build also completed in
the Node 22 frontend container. Original browser suites were not edited:

| Check | Result | Report |
| --- | --- | --- |
| Original professional-view journeys | 17/17 groups | [Legacy](browser-legacy.json) |
| Simple/Pro, navigation, numeric alternatives and responsive journeys | 18/18 groups | [Redesign](browser-redesign.json) |
| Research guide, eleven locales and speech-control behavior | 15/15 groups | [Guide](browser-guide.json) |
| Actual container API journeys, including honest REPLAY and intentional 503 | 9/9 groups | [Real API](browser-real-api.json) |
| Seven routes in both views: text contrast, control names and target sizes | 14 route/view cases; no failures | [Focused contrast](contrast-targets.json) |

The reduced-motion, 320 px and text-enlargement checks retain their original scope; no new
native NVDA or audible-speech certification is claimed. The deliberate 503 has its own expected
network error; normal real API journeys have no console errors or synthetic fixture requests.

Six chart families were inspected visually. One rendering issue was corrected: global decal
patterns must not make the timeline's transparent positioning bars look like durations.
Only the offset series suppresses its decal; actual duration patterns, data and timing-source
alternatives remain. [Chart captures](charts/manifest.json) are labelled as SYNTHETIC-fixture
rendering evidence, not real market results.

## Ruff policy

The development extra pins Ruff 0.17.2. Both that binary and the collector's 0.15.20 pass:

```powershell
py -3 -m ruff check ingest quant integrations tradepulse run.py scripts serve.py --no-cache
```

Ruff 0.16 expanded its defaults and removed E731 from the default set. The project now explicitly
selects its original `E4`, `E7`, `E9`, `F` policy plus `RUF100`, preventing an accidental lint
policy change between machines. The original quant test and its valid E731 suppression remain
unchanged. Four non-enabled BLE001 suppressions in ingestion became ordinary explanatory
comments. No lint-ignore list, test edit or runtime behavior change was introduced.

The complete Python suite passed **609 tests, zero skipped**, with 19 existing lxml warnings.
The [summary](summary.json) records actual suite counts and build identities.

## SEC documentation and preserved data

The filing contract changes only `acceptance_datetime.description`; names, types, nullability,
keys and all other schema properties remain unchanged. Source-policy documentation now states:

- Live persistence reads the SEC index page's Accepted clock, localizes to America/New_York
  with daylight saving and stores UTC.
- The old raw-JSON Eastern-clock hypothesis was disproved. The original synthetic helper and
  tests remain for compatibility and do not define persisted live timestamps.
- The ingestion bound is strictly before next-day 00:00 UTC. A 16:00 New York market-close
  decision or automatic next-session reassignment is not implemented.

All seven sample table hashes are unchanged. The three saved source-index comparisons match
their actual parquet records again. [SEC verification receipt](sec-timestamps.json) records the
comparison, 9,005 checked filing records and the exclusive UTC cutoff. This was a local
revalidation of delivered evidence, not a claim of a new network collection or full historical
point-in-time certification.
