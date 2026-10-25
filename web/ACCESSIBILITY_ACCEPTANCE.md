# Independent research-guide acceptance — 25 October 2026

Scope: Ticker Detail on the SYNTHETIC fixture, including the localized guide, original
claims/evidence and expanded chart tables. This is measured acceptance of the recorded build,
not certification of the whole application or its real backend.

The [portable evidence](accessibility/2026-10-25/summary.json) records source/report hashes,
versions, individual cases and remaining limitations.

| Check | Actual result | Scope |
| --- | --- | --- |
| Lighthouse 13.5.0 accessibility | 100 desktop; 100 at 320 px | Initial Ticker Detail navigation; both reports have no failed audits or run warnings. |
| axe-core 4.14.0 | 28 cases; zero critical, serious, moderate or minor violations | Simple/Pro, all eleven guide languages at 320 px, English/Chinese/Arabic at 1440 px; disclosures and available chart tables expanded. No rule exclusions. |
| Native Chrome zoom | 18 cases passed | Simple/Pro and English/Chinese/Arabic at 100% and 200%, including 320 CSS px at 200%. |
| Keyboard/reduced motion and page regression | 15/15 guide, 17/17 original browser and 18/18 redesign groups passed after the shell correction | Unchanged scripts/assertions, including keyboard controls, reduced motion, 320 px and text enlargement. |
| NVDA/VoiceOver | Not run for the new guide | Windows desktop control cannot connect; no NVDA executable was discovered in the checked install locations. Actual reader interaction is still required. |

Reports: [desktop HTML](accessibility/2026-10-25/ticker-desktop-after.report.html),
[desktop JSON](accessibility/2026-10-25/ticker-desktop-after.report.json),
[320 px HTML](accessibility/2026-10-25/ticker-mobile-320-after.report.html),
[320 px JSON](accessibility/2026-10-25/ticker-mobile-320-after.report.json).

The first axe run found a serious visible-label/accessibility-name mismatch on the brand
link and a moderate landmark omission around the data banner/run information. The link now
uses its visible text as its name; a named Run context region contains those disclosures.
Both findings disappeared on the full repeat scan. No rule was disabled to obtain the pass.

The axe DevTools extension UI was not used: these are direct axe-core results. Its incomplete
color-contrast items were reviewed separately. Two glyphs are decorative and aria-hidden,
with adjacent text carrying the meaning. Three table values were clipped by their horizontal
scroll container; after scrolling, their computed foreground/background contrast was
12.37:1. The original incomplete results and the review remain in the evidence.

Native zoom used Chrome's real per-host zoom preference in isolated test profiles, with
viewport emulation disabled. At the same 1440 px outer window width, innerWidth changed from
1418 to 709 and devicePixelRatio from 1 to 2; the root font stayed 16 px and visualViewport
scale stayed 1. A 662 px outer window produced 320 CSS px at 200%. All tested guide/page
widths fit without page-level horizontal overflow. This was not CSS font enlargement or
DevTools pinch/page-scale emulation. Screenshots and full intermediate output remain local
under `D:/AI_Models/hackson/.work/accessibility-acceptance-20261025/`.

## Remaining native screen-reader spot check

Use an actual NVDA installation on Windows or VoiceOver on macOS. Browser SpeechSynthesis
playback and ARIA snapshots do not replace this check.

1. Start the reader and open `/ticker/us_equity/SYN369` on the fixture build.
2. Confirm the page title, instrument heading, SYNTHETIC banner and Run context are announced.
3. Navigate to the four guide question summaries. Expand/collapse them and confirm the state
   is announced; inspect original claims, the explanation verdict and the source summary.
4. Tab to the language selector and speech controls. Confirm labels, unavailable-voice state,
   enabled/disabled states and read-aloud status are understandable. Check one localized guide.
5. Read one original evidence table and one contribution/chart data table, including headers.
6. Record reader/browser versions, the route/actions, actual announcements and any defects.
   Leave this item pending until that walkthrough has really happened.

Native-speaker translation review, audible voice/pronunciation quality and broader browser
coverage remain separate. No complete WCAG 2.2 AA certification is claimed.
