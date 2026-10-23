"""Earnings surprise (SUE) and event panels (task C5). See docs/architecture/factors.md."""

from __future__ import annotations

import numpy as np
import pandas as pd


def first_reported(facts: pd.DataFrame) -> pd.DataFrame:
    """Keep the earliest-filed row for each (period_start, period_end); this is what the market
    saw first. Input columns include period_start, period_end, value, filed. Sorted by period_end,
    fresh index. Filing ties keep the first input row."""
    return (
        facts.sort_values("filed", kind="stable")
        .drop_duplicates(["period_start", "period_end"], keep="first")
        .sort_values("period_end", kind="stable")
        .reset_index(drop=True)
    )


def quarterly_eps(facts: pd.DataFrame) -> pd.DataFrame:
    """Quarterly diluted EPS from first-reported facts. Returns columns period_end, value, filed.

    - Quarterly rows have a duration (period_end - period_start) of 80 to 100 days.
    - Q4 is derived from an annual row (350 to 380 days) when exactly 3 quarterly rows lie inside
      it (start >= annual start, end < annual end) and no quarterly row already ends on the annual
      end date: value = annual - sum(3 quarters), period_end = annual end, filed = annual filed.
    - Sorted by period_end.
    - Derivation requires all three quarters to have been filed by the annual filing date;
      missing quarterly values leave the derived value missing.
    """
    reported = first_reported(facts)
    duration = (reported["period_end"] - reported["period_start"]).dt.days
    quarters = reported.loc[duration.between(80, 100)]
    annuals = reported.loc[duration.between(350, 380)]
    columns = ["period_end", "value", "filed"]
    derived = []
    for annual in annuals.itertuples(index=False):
        inside = quarters.loc[
            (quarters["period_start"] >= annual.period_start)
            & (quarters["period_end"] < annual.period_end)
        ]
        if (
            len(inside) == 3
            and not quarters["period_end"].eq(annual.period_end).any()
            and inside["filed"].le(annual.filed).all()
        ):
            derived.append({
                "period_end": annual.period_end,
                "value": annual.value - inside["value"].sum(min_count=3),
                "filed": annual.filed,
            })
    result = quarters[columns].copy()
    if derived:
        result = pd.concat([result, pd.DataFrame(derived, columns=columns)], ignore_index=True)
    return result.sort_values("period_end", kind="stable").reset_index(drop=True)


def sue(eps: pd.DataFrame) -> pd.DataFrame:
    """Add columns `diff` and `sue` to a quarterly_eps frame (rows assumed consecutive quarters).

    diff[q] = value[q] - value[q-4]. sue[q] = diff[q] / std(previous diffs, ddof=1), where the
    previous diffs are the up to 8 diffs before q. Fewer than 4 previous diffs, or a zero std,
    gives NaN.
    """
    result = eps.copy()
    result["diff"] = result["value"].diff(4)
    scale = result["diff"].shift(1).rolling(8, min_periods=4).std(ddof=1)
    result["sue"] = result["diff"] / scale.where(scale.ne(0))
    return result


def event_panel(events: pd.DataFrame, index: pd.DatetimeIndex, symbols: list[str],
                hold: int = 60) -> pd.DataFrame:
    """Spread point-in-time event values into a daily wide panel.

    events columns: symbol, available_date, value. An event becomes visible on the first index
    date strictly after available_date, stays for `hold` rows, then disappears (NaN). A newer
    event for the same symbol replaces an older one from its own start row.
    Equal availability dates use the last input event. Unrequested symbols are ignored.
    `hold` must be positive. Replaced events never resume after the newer event expires.
    """
    if hold < 1:
        raise ValueError("hold must be positive")
    values = np.full((len(index), len(symbols)), np.nan)
    columns = {symbol: column for column, symbol in enumerate(symbols)}
    ordered = events.sort_values("available_date", kind="stable")
    starts = index.searchsorted(ordered["available_date"], side="right")
    for event, start in zip(ordered.itertuples(index=False), starts):
        column = columns.get(event.symbol)
        if column is not None and start < len(index):
            values[start:, column] = np.nan
            values[start:min(start + hold, len(index)), column] = event.value
    return pd.DataFrame(values, index=index, columns=symbols)
