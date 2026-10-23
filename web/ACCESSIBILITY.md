# Accessibility implementation and verification

TradePulse targets WCAG 2.2 AA. This document records implementation and observed checks, not certification or a claim of complete AA conformance.

## Implemented structure and interaction

- English document language; one main landmark; named navigation regions; meaningful document titles and heading levels.
- A keyboard-visible Skip to main content link. Route focus is handled once in PageTitle; initial document focus is left alone, active inputs/buttons are not interrupted, and view changes do not move focus.
- Native buttons with aria-pressed identify Simple/Pro selection. Both modes use the same original recommendation, explanation, provenance and risk records. Storage failures fall back to an in-memory preference.
- Native search, select, checkbox, details/summary, links and tables. Controls have visible labels; table columns and row headers identify their relationships.
- The mobile menu is an inline disclosure, not a modal or focus trap. Escape closes it and restores focus to its button. Closed navigation is removed from the normal tab sequence.
- Search, sector/tier filters, sorting and pagination are preserved in the URL; instrument return links preserve the market context. No view-specific ranking engine exists.
- All essential charts have named figures, descriptions and exact numeric alternatives. Treemap selection also works through a sector dropdown and keyboard-operable sector buttons. The canvas itself is hidden from the accessibility tree to avoid repeating its generated label.
- Original verified/rejected/abstained outcomes remain visible in both modes. Contrary evidence is not hidden by the Simple presentation. Missing data stays unavailable.
- Synthetic/replay disclosure and the source run disclaimer remain readable and non-dismissable. Coverage is explicitly distinguished from confidence; expected values are distinguished from realized results.

## Relevant WCAG criteria and evidence

| Area | Relevant criteria | Evidence and scope |
| --- | --- | --- |
| Structure and names | 1.3.1, 2.4.2, 2.4.6, 3.1.1, 3.3.2, 4.1.2 | Native semantics, explicit labels, headers, named groups, Chromium ARIA snapshot and name checks |
| Keyboard and focus | 2.1.1, 2.1.2, 2.4.1, 2.4.3, 2.4.7, 2.4.11 | Real Chromium keyboard events cover skip link, guide, journeys, claims, view switch and menu Escape; focus rings visually inspected |
| Color and contrast | 1.4.1, 1.4.3, 1.4.11 | Signed values and text outcomes; computed rendered text contrast and sampled control borders; chart colors and labels visually inspected |
| Resize and reflow | 1.4.4, 1.4.10 | Both modes at 1440, 768, 390 and 320 CSS pixels, plus 200% root text enlargement at a narrow viewport; ordinary content does not depend on page-level horizontal scrolling |
| Target size | 2.5.8 | Important buttons generally have a 44 CSS pixel minimum height; rendered target sizes checked against 24px, with checkbox labels treated as their click targets |
| Charts and alternatives | 1.1.1, 1.3.1 | Contribution, sector, factor IC, regime history, calibration, composite IC and paired trace timing tables/disclosures |
| Feedback and status | 3.3.1, 4.1.3 | Named loading/error states and Retry; one result-count announcement per screen; original limitations preserved |
| Motion | 2.3.1; reduced-motion preference support | No flashing or fake thinking; chart animations disabled including treemap durations; static skeletons; prefers-reduced-motion CSS |

## Actual test environment and methods

- Linux Chromium through the existing Playwright runtime; no browser or accessibility dependency was added to the application.
- The original browser acceptance script is unchanged. Its table-based assertions run with Pro View selected before document load. Separate redesign checks exercise the fresh Simple default, storage-disabled behavior, view parity and mode switching.
- `scripts/redesign-acceptance.cjs` tests the guided flow, preserved market context, keyboard operation, numeric equivalents, both-view reflow, 200% text enlargement and reduced motion. It captures real screenshots and a Chromium ARIA snapshot.
- `scripts/accessibility-check.cjs` computes text contrast from rendered foreground/background colors for visible text nodes in both views, checks accessible control names and inspects targets. Disabled targets are excluded and checkbox labels are the effective click target. This is a focused check, not an automated WCAG scanner.
- The 320 CSS pixel test represents the reflow width of a 1280px browser at 400% zoom. It does not establish that native browser-zoom controls or every operating-system scaling setting were tested.
- Visual checks use genuine browser captures and inspect cards, disclosures, charts, banners, mobile navigation and focus indication. Tests and screenshots do not establish an assistive-technology audit.

## Manual review procedure

1. Open Discover in a fresh browser. Press Tab to reach the skip link, then Enter. Confirm focus enters main content and the synthetic banner remains visible.
2. Use Tab/Shift+Tab and Enter/Space to operate Simple/Pro, open the guide, follow an actual explanation and expand its rejected claim. Confirm no mouse is required and focus stays predictable.
3. In Pro View, combine search, sector and tier filters, sort numeric columns, move to another page and open an instrument. Return and confirm context. Switch modes without losing the selected record or filters.
4. At a narrow viewport, open the menu, enter its links and press Escape. Confirm focus returns to the menu button and closed links cannot receive focus.
5. Open every chart's numeric disclosure using the keyboard. Compare counts, units, nulls, dates, signed values and source discrepancies. Do not rely on chart color or hover tooltips alone.
6. Repeat the main journey at 200% text size and at a 320 CSS pixel reflow width. Tables may scroll independently; normal text, filters, disclaimers and navigation must remain available.
7. With reduced motion enabled, verify there is no chart animation or pulsing placeholder. Test missing instruments, missing explanations, blocked storage, malformed data and unavailable API with Retry.
8. Before claiming full AA conformance, complete an independent audit with actual NVDA/Narrator and VoiceOver, native zoom controls and additional browsers.

## Known gaps and limitations

- NVDA, Windows Narrator and macOS VoiceOver were not available or tested. Chromium accessible names/ARIA snapshots are not substitutes for these tests.
- Only Chromium was exercised; Safari, Firefox and native Windows/macOS behavior need independent testing.
- Native 400% browser zoom, OS text scaling, forced-colors/high-contrast modes and a complete non-text-contrast audit remain unverified.
- No axe-core installation was available. No third-party automated accessibility certification is claimed.
- The contrast helper does not inspect every canvas pixel, pseudo-element, transient state or every combination of user style overrides. Chart equivalents preserve essential information if a graphical label is unsuitable.
- View preference persistence depends on storage availability. With blocked storage the active selection works during navigation, but a full reload can return to Simple View.
- The work is awaiting independent team accessibility and visual review. No claim of legal compliance or WCAG certification is made.

## Recorded final results

Chromium 154.0.8037.57 was used. The unchanged Pro regression suite passed 17/17 groups; the redesign suite passed 18/18 groups. Computed checks covered 14 route/view combinations and 5,428 visible text nodes, with an observed minimum text contrast of 5.66:1 and sampled view-control border contrast of 3.35:1. No unnamed inspected controls or effective targets below 24px were reported. The 100 final captures include keyboard focus, rejected evidence and both presentation modes. These results do not close the native assistive-technology and complete audit gaps above.
