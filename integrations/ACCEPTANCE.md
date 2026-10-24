# Acceptance — Member D (`integrations/`)

The team lead merges a PR only when every item that applies is true. Paste command output into the
PR, with secrets redacted.

Offline helper/client tests are already implemented. They do not establish hosted Zetaris,
actual Meterless engine use or NIM live acceptance. The current evidence draft is
`../docs/sponsors.md`; missing evidence remains unchecked. See `../docs/STATUS.md`.

## Automated (must pass)

```
py -3 -m pytest integrations -q                  # offline tests: 0 failed
py -3 -m pytest integrations -q -m network       # live tests (parity, runtime, NIM): 0 failed — run where the services are reachable
cd integrations/engines && npm test && npm run conformance   # both exit 0
```

## Evidence checklist

- [ ] D0: Zetaris and the engines sidecar run on **AWS** (EU region unless documented otherwise).
  - [ ] `DEPLOY.md` explains the setup and how lake files reach Zetaris (private S3). Preflight and
    verify output is pasted. A budget alert is set.
  - [ ] Both endpoints are HTTPS only, IP allow-listed and token protected. No plain-HTTP port, and
    the GUI is not public.
  - [ ] `ACCESS.md` is complete, and **the lead has run its smoke test successfully from Europe**.
  - [ ] Member A has write access to the S3 lake prefix only.
  - [ ] No secrets anywhere in the repository.
- [ ] D1: the registration CLI ran twice; the second run reports `exists`, not errors. A GUI
  screenshot shows all 7 lake tables plus the EDGAR REST table.
- [ ] D2: every template renders, passes the injection tests and runs on DuckDB over `data/sample`.
- [ ] D3: `test_parity.py` shows equal `rows_sha256` on both back ends for every template. The
  recorded response fixture contains no token or org id. The on-demand EDGAR lookup works for one
  ticker outside the universe.
- [ ] D4: the three NIM models were agreed with the lead (the skeptic is from a different family
  than the analyst).
  - [ ] `test_live_llm.py` passes for extractor, analyst and skeptic; the output is pasted.
  - [ ] `data/sample/llm_cassette.jsonl` and `extraction_cache.jsonl` are committed. With the
    network disabled, a SAMPLE_MODE run of the same `--as-of` prints no "model answer was
    unavailable" warning.
- [ ] D5:
  - [ ] the conformance suites for World Model and H-MEM are green against the vendored engines
  - [ ] the smoke test is green
  - [ ] `vendor/` has LICENSE and NOTICE, and our code never edits it
- [ ] D6: `docs/sponsors.md` draft exists. Every claim in it points to evidence from the items
  above.

## Code checks

- [ ] No secret, token, org id, AWS key or personal e-mail in code, tests, fixtures, cassette, logs
  or screenshots.
- [ ] Every Zetaris call sends one statement, with a timeout and a fresh `X-Request-ID`.
- [ ] No free-form SQL path exists. The only path is template, then `render()`, then the adapter.
- [ ] SAMPLE_MODE never opens a network connection. Prove it with a run that has the network
  disabled.
- [ ] Every retry and loop is bounded.
- [ ] No signature in the stubs changed; no given test was weakened.
- [ ] Everything is in English.

## PR checklist (copy into the PR description)

```
- [ ] task(s): D?
- [ ] offline tests: <summary>
- [ ] network tests: <summary or "not applicable">
- [ ] conformance: <summary or "not applicable">
- [ ] evidence links/screenshots: <list>
- [ ] secrets check: grep for key/token patterns done, none found
```
