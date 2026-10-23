"""Cross-sectional transforms applied date by date (task C2).

Input and output are wide panels (index = dates, columns = symbols). Each row is processed
independently, so no information crosses dates.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def winsorize_cs(df: pd.DataFrame, n_sigma: float = 3.0) -> pd.DataFrame:
    """Clip each row to [mean - n_sigma*std, mean + n_sigma*std] (row mean, std ddof=1).
    Rows with fewer than 2 values are returned unchanged."""
    mean = df.mean(axis=1)
    spread = n_sigma * df.std(axis=1, ddof=1)
    return df.clip(lower=mean - spread, upper=mean + spread, axis=0)


def zscore_cs(df: pd.DataFrame) -> pd.DataFrame:
    """(x - row mean) / row std (ddof=1). Rows with fewer than 2 values or zero std become NaN."""
    std = df.std(axis=1, ddof=1)
    return df.sub(df.mean(axis=1), axis=0).div(std.where(std != 0), axis=0)


def rank_pct_cs(df: pd.DataFrame) -> pd.DataFrame:
    """Percentile rank within each row, ties averaged, values in (0, 1]."""
    return df.rank(axis=1, method="average", pct=True)


def neutralize_groups(df: pd.DataFrame, groups: pd.Series) -> pd.DataFrame:
    """Subtract the row mean of each group from its members.

    groups maps symbol -> group label (for example a GICS sector). Symbols not in `groups` form
    one shared group named "__none__". Missing group labels also belong to "__none__".
    """
    labels = groups.reindex(df.columns).astype(object)
    labels = labels.where(labels.notna(), "__none__")
    means = df.T.groupby(labels, sort=False).transform("mean").T
    return df - means


def residualize_cs(y: pd.DataFrame, X: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """For every date, regress y on the X panels (with an intercept) across symbols and return the
    residuals. Only symbols where y and every X are present are used. A date with fewer than
    len(X) + 2 such symbols gives an all-NaN row. Symbols that were excluded are NaN.

    X panels are aligned to y's labels. Empty X fits only an intercept; rank-deficient designs
    use the minimum-norm least-squares solution.
    """
    values = y.to_numpy(dtype=float)
    design = np.ones((*y.shape, len(X) + 1), dtype=float)
    for column, panel in enumerate(X.values(), start=1):
        design[:, :, column] = panel.reindex(index=y.index, columns=y.columns).to_numpy(dtype=float)
    complete = ~np.isnan(values) & ~np.isnan(design).any(axis=2)
    residuals = np.full(y.shape, np.nan)
    for row in range(len(y)):
        valid = complete[row]
        if valid.sum() < len(X) + 2:
            continue
        predictors = design[row, valid]
        response = values[row, valid]
        coefficients = np.linalg.lstsq(predictors, response, rcond=None)[0]
        residuals[row, valid] = response - predictors @ coefficients
    return pd.DataFrame(residuals, index=y.index, columns=y.columns)
