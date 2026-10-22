# Acceptance — Member D (`integrations/`)

The team lead merges a PR only when every item that applies is true. Paste command output into the
PR, with secrets redacted.

## Automated (must pass)

```
py -3 -m pytest integrations -q                  # offline tests: 0 failed
py -3 -m pytest integrations -q -m network       # live tests (parity, runtime, NIM): 0 failed — run where the services are reachable
cd integrations/engines && npm test && npm run conformance   # both exit 0
```

## Evidence checklist

- [ ] D0: `DEPLOY.md` explains where Zetaris runs and how lake files reach it. Preflight and verify
  output is pasted. Budget alert set (AWS). No secrets anywhere.
- [ ] D1: the registration CLI ran twice; the second run reports `exists`, not errors. A GUI
  screenshot shows all 7 lake tables plus the EDGAR REST table.
- [ ] D2: every template renders, passes the injection tests and runs on DuckDB over `data/sample`.
- [ ] D3: `test_parity.py` shows equal `rows_sha256` on both back ends for every template. The
  recorded response fixture contains no token or org id. The on-demand EDGAR lookup works for one
  ticker outside the universe.
- [ ] D4: `runtime_status` returns `online` on the Nightshift machine.
  - [ ] One extractor call ran through Meterless and one analyst call through NIM; trace excerpts
    are pasted.
  - [ ] The cassette replays the sample inputs with the network disabled.
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
