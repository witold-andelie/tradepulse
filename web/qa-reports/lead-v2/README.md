# Lead V2 focused contrast review

Measured 27 October 2026 on Windows with installed Chrome in headless mode and axe-core
4.14.0. The application tree at merged main `a4d49a7` is identical to reviewed head `90794af`
and tested implementation `4e61b50`. These checks use the labelled SYNTHETIC fixture, not
hosted model outputs or a new live API journey. No application code was changed.

- [contrast.json](contrast.json): nine scans, English/Chinese/Arabic on Ticker Detail,
  Factor Lab and US Leaderboard. Zero color-contrast violations. Incomplete entries are
  retained, not removed or converted into passes.
- [color-samples.json](color-samples.json): 94 representative element-style observations
  across English/Arabic Leaderboard, Factor Lab, Regime and Ticker Detail. Computed sRGB
  colors include ancestor alpha compositing; every sampled style passed its applicable
  text threshold. Minimum observed ratio: 5.078266494563155:1. This is not a full text-node,
  focus-border, chart-pixel or eleven-language audit.

Incomplete scan reasons were decorative non-text symbols (`nonBmp`) and cells partly outside
the horizontally scrollable Leaderboard region (`elmPartiallyObscured`). The symbols have
visible adjacent labels; chart patterns/sign labels and numeric alternatives remain present.
The table was scrolled to expose the previously obscured cells, whose sampled text colors
passed. The screenshot review covered English guide text, Arabic chart labels and a scrolled
Arabic table. This supports the focused disposition, not removal of the original incomplete
records or a blanket accessibility certification.

Actual captures include:

- [English guide](en-detail-guide.png)
- [Chinese guide](zh-CN-detail-guide.png)
- [Arabic chart](ar-detail-chart.png)
- [Arabic scrolled table](ar-scrolled-table.png)
- [English scrolled table](en-scrolled-table.png)

Native screen-reader acceptance was attempted separately but could not run: the installed
Windows automation helper reported its native pipe unavailable, and NVDA was not found at
standard installation paths. No screen-reader pass is claimed. The lead's next short check
is described in [V2_LEAD_FOLLOWUP.md](../../V2_LEAD_FOLLOWUP.md). Actual speech/cross-browser
voices and eleven-language editorial are deferred by the lead.
