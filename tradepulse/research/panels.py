"""SD1.4 steps 1-3: raw factor panels -> standardised -> residualised on the price-volume baseline.
Formulas: docs/architecture/factors.md (Factor catalogue). All math comes from quant/."""

from __future__ import annotations

import pandas as pd

from quant import crosssection, indicators

PV_FACTORS = ("pv_mom_12_1", "pv_mom_1m", "pv_rev_5d", "pv_lowvol_20d", "pv_volume_z", "pv_dist_52w_high")


def price_volume_factors(prices: pd.DataFrame, volume: pd.DataFrame, rows_per_year: int,
                         rows_per_month: int) -> dict[str, pd.DataFrame]:
    """Raw baseline panels keyed by PV_FACTORS (each oriented so higher = higher expected return):
    pv_mom_12_1 = momentum(prices, rows_per_year, skip=rows_per_month)
    pv_mom_1m = momentum(prices, rows_per_month)
    pv_rev_5d = reversal(prices, 5)
    pv_lowvol_20d = -realized_vol(prices, 20, rows_per_year)
    pv_volume_z = volume_zscore(volume aligned to prices, 60)
    pv_dist_52w_high = distance_to_high(prices, rows_per_year)
    """
    return {
        "pv_mom_12_1": indicators.momentum(prices, rows_per_year, skip=rows_per_month),
        "pv_mom_1m": indicators.momentum(prices, rows_per_month),
        "pv_rev_5d": indicators.reversal(prices, 5),
        "pv_lowvol_20d": -indicators.realized_vol(prices, 20, rows_per_year),
        "pv_volume_z": indicators.volume_zscore(volume.reindex_like(prices), 60),
        "pv_dist_52w_high": indicators.distance_to_high(prices, rows_per_year),
    }


def attention_factor(views: pd.DataFrame, prices: pd.DataFrame, volume_z: pd.DataFrame,
                     lowvol: pd.DataFrame) -> pd.DataFrame:
    """att_pageviews: attention_change(views aligned to prices, short=7, long=83, lag=1), then
    residualize_cs on {"abs_ret_5d": abs(momentum(prices, 5)), "volume_z": volume_z,
    "lowvol": lowvol}. Returns the residual panel (index/columns of prices)."""
    raw = indicators.attention_change(views.reindex_like(prices), short=7, long=83, lag=1)
    return crosssection.residualize_cs(raw, {
        "abs_ret_5d": indicators.momentum(prices, 5).abs(),
        "volume_z": volume_z,
        "lowvol": lowvol,
    })


def standardize(raw: pd.DataFrame, groups: pd.Series | None, n_sigma: float) -> pd.DataFrame:
    """winsorize_cs(n_sigma) -> zscore_cs -> neutralize_groups(groups) when groups is not None."""
    z = crosssection.zscore_cs(crosssection.winsorize_cs(raw, n_sigma))
    return crosssection.neutralize_groups(z, groups) if groups is not None else z


def build_pool_panels(prices: pd.DataFrame, volume: pd.DataFrame, views: pd.DataFrame | None,
                      groups: pd.Series | None, pool_cfg: dict, factors_cfg: dict,
                      extra: dict[str, pd.DataFrame] | None = None) -> dict[str, pd.DataFrame]:
    """Standardised factor panels for one pool, all aligned to prices.index x prices.columns.

    - Baseline: every PV_FACTORS panel -> standardize(groups if pool_cfg["sector_neutral"] else None).
    - att_pageviews (only when views is given) and every panel in `extra` (raw panels such as
      earn_sue or rel_spillover, reindexed to prices) -> standardize -> residualize_cs on the six
      standardised baseline panels -> zscore_cs again.
    - rows_per_year / rows_per_month come from pool_cfg (keys rows_per_year, rows_per_month).
    - n_sigma = factors_cfg["winsor_sigma"].
    Never mutates inputs.
    """
    raw = price_volume_factors(prices, volume, pool_cfg["rows_per_year"],
                               pool_cfg["rows_per_month"])
    sector_groups = groups if pool_cfg["sector_neutral"] else None
    n_sigma = factors_cfg["winsor_sigma"]
    baseline = {name: standardize(panel, sector_groups, n_sigma) for name, panel in raw.items()}
    additional = {}
    if views is not None:
        additional["att_pageviews"] = attention_factor(
            views, prices, raw["pv_volume_z"], raw["pv_lowvol_20d"])
    if extra is not None:
        additional.update(extra)
    panels = dict(baseline)
    for name, panel in additional.items():
        z = standardize(panel.reindex_like(prices), sector_groups, n_sigma)
        panels[name] = crosssection.zscore_cs(crosssection.residualize_cs(z, baseline))
    return panels
