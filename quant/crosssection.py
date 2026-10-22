"""Cross-sectional transforms applied date by date (task C2).

Input and output are wide panels (index = dates, columns = symbols). Each row is processed
independently, so no information crosses dates.
"""

from __future__ import annotations

import pandas as pd


def winsorize_cs(df: pd.DataFrame, n_sigma: float = 3.0) -> pd.DataFrame:
    """Clip each row to [mean - n_sigma*std, mean + n_sigma*std] (row mean, std ddof=1).
    Rows with fewer than 2 values are returned unchanged."""
    raise NotImplementedError("C2")


def zscore_cs(df: pd.DataFrame) -> pd.DataFrame:
    """(x - row mean) / row std (ddof=1). Rows with fewer than 2 values or zero std become NaN."""
    raise NotImplementedError("C2")


def rank_pct_cs(df: pd.DataFrame) -> pd.DataFrame:
    """Percentile rank within each row, ties averaged, values in (0, 1]."""
    raise NotImplementedError("C2")


def neutralize_groups(df: pd.DataFrame, groups: pd.Series) -> pd.DataFrame:
    """Subtract the row mean of each group from its members.

    groups maps symbol -> group label (for example a GICS sector). Symbols not in `groups` form
    one shared group named "__none__".
    """
    raise NotImplementedError("C2")


def residualize_cs(y: pd.DataFrame, X: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """For every date, regress y on the X panels (with an intercept) across symbols and return the
    residuals. Only symbols where y and every X are present are used. A date with fewer than
    len(X) + 2 such symbols gives an all-NaN row. Symbols that were excluded are NaN."""
    raise NotImplementedError("C2")
