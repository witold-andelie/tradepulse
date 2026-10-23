# Acceptance — Member B (`web/`)

The team lead merges a PR only when every item that applies is true. Attach screenshots of every
page you changed, at 1440 px and at 768 px width.

## Automated (must pass)

```
cd web
npm test                  # 0 failed (the given src/lib tests plus any you add)
npm run check:contracts   # all "ok"
npm run build             # succeeds, no errors
```

## Functional checks (the lead clicks through these)

- [ ] With the fixture, every page shows the yellow **SYNTHETIC FIXTURE** banner and the
  disclaimer footer.
- [ ] Leaderboard:
  - [ ] each of the 3 pools shows the right row count (520 / 60 / 40)
  - [ ] sorting, search, sector and tier filters work together
  - [ ] pagination works
  - [ ] clicking a treemap block filters the table
- [ ] Ticker detail opens from a row click and from a top/bottom card. The contributions sum
  caption is present. Explanations show verified and rejected claims distinctly.
- [ ] An abstained explanation in the fixture renders as "abstained" with its rejected claim
  visible.
- [ ] Factor Lab shows `INSUFFICIENT_DATA` cards for filing factors in the EU and crypto pools, and
  shows all five gate chips on every card.
- [ ] Regime shows normal / elevated / stressed for the three fixture pools, with the history
  chart.
- [ ] Track Record shows the calibration chart with a diagonal, and the by-tier table.
- [ ] Run Trace shows the timeline and highlights the `retry` event.
- [ ] An unknown route and an unknown ticker show friendly not-found pages.
- [ ] With `VITE_API_BASE=http://localhost:9` (nothing listening), the app shows a readable error
  and a Retry button. It must not render a blank page.

## Accessibility checks (every changed page; see "Accessibility" in TASK.md)

These need no extra packages. They use Chrome DevTools and the free axe DevTools browser extension.

- [ ] Lighthouse → Accessibility score **≥ 95**; paste the score in the PR.
- [ ] axe DevTools scan: **0 critical and 0 serious** issues; list any moderate ones with a reason.
- [ ] **Keyboard-only walkthrough:**
  - unplug or ignore the mouse
  - reach and use every control on the page
  - the focus ring is always visible, and there is no trap
  - describe the route in the PR, e.g. "Tab to search → type → Tab to table → Enter opens NVDA"
- [ ] **Screen reader spot check:** use NVDA on Windows (free) or VoiceOver on macOS. The page
  title, the banner, one table and one chart's text alternative are read sensibly.
- [ ] **Zoom and width:** the page works at 200% browser zoom and at 320 px width.
- [ ] **Reduced motion:** with "reduce motion" on in the OS, charts render without animation.
- [ ] Every chart has an `aria-label` summary computed from data and a "Show data as table"
  toggle.

## Code checks

- [ ] No result numbers, tickers or explanation text are hard-coded in components. Grep for
  `SYN0` and digits inside JSX text.
- [ ] No "Buy" / "Sell" wording anywhere in the UI.
- [ ] Tiers and gate results carry text or icons, not only colour.
- [ ] Only the dependencies in `package.json` are used. A new dependency needs the lead's approval
  in the PR.
- [ ] No `console.log` left in components. The browser console shows no errors or warnings on any
  page.
- [ ] No secrets, external fonts, analytics or CDN links.
- [ ] Everything is in English.

## PR checklist (copy into the PR description)

```
- [ ] task(s): B?
- [ ] npm test: <summary>
- [ ] check:contracts: ok
- [ ] build: ok, largest chunk <size>
- [ ] screenshots: 1440px + 768px for each changed page
```
