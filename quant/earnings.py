"""Earnings surprise (SUE) and event panels (task C5). See docs/architecture/factors.md."""

from __future__ import annotations

import pandas as pd


def first_reported(facts: pd.DataFrame) -> pd.DataFrame:
    """Keep the earliest-filed row for each (period_start, period_end); this is what the market
    saw first. Input columns include period_start, period_end, value, filed. Sorted by period_end,
    fresh index."""
    raise NotImplementedError("C5")


def quarterly_eps(facts: pd.DataFrame) -> pd.DataFrame:
    """Quarterly diluted EPS from first-reported facts. Returns columns period_end, value, filed.

    - Quarterly rows have a duration (period_end - period_start) of 80 to 100 days.
    - Q4 is derived from an annual row (350 to 380 days) when exactly 3 quarterly rows lie inside
      it (start >= annual start, end < annual end) and no quarterly row already ends on the annual
      end date: value = annual - sum(3 quarters), period_end = annual end, filed = annual filed.
    - Sorted by period_end.
    """
    raise NotImplementedError("C5")


def sue(eps: pd.DataFrame) -> pd.DataFrame:
    """Add columns `diff` and `sue` to a quarterly_eps frame (rows assumed consecutive quarters).

    diff[q] = value[q] - value[q-4]. sue[q] = diff[q] / std(previous diffs, ddof=1), where the
    previous diffs are the up to 8 diffs before q. Fewer than 4 previous diffs, or a zero std,
    gives NaN.
    """
    raise NotImplementedError("C5")


def event_panel(events: pd.DataFrame, index: pd.DatetimeIndex, symbols: list[str],
                hold: int = 60) -> pd.DataFrame:
    """Spread point-in-time event values into a daily wide panel.

    events columns: symbol, available_date, value. An event becomes visible on the first index
    date strictly after available_date, stays for `hold` rows, then disappears (NaN). A newer
    event for the same symbol replaces an older one from its own start row.
    """
    raise NotImplementedError("C5")
