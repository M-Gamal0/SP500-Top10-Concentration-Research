"""Analytics: sector allocation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def normalize_holdings_dates(quarterly_mc_holdings_input, *, config: AnalyticsConfig):
    """Calculate sector allocation with explicit inputs; preserve legacy conventions."""
    quarterly_mc_holdings = quarterly_mc_holdings_input
    quarterly_mc_holdings["selection_date"] = pd.to_datetime(
        quarterly_mc_holdings["selection_date"]
    )
    return (quarterly_mc_holdings,)


def calculate_sector_allocation(
    quarterly_mc_holdings, sector_metadata_input, *, config: AnalyticsConfig
):
    """Calculate sector allocation with explicit inputs; preserve legacy conventions."""
    TOLERANCE = config.tolerance
    sector_metadata = sector_metadata_input
    sector_metadata["lastupdated"] = pd.to_datetime(sector_metadata["lastupdated"])
    sector_metadata = sector_metadata.sort_values(["ticker", "lastupdated"]).drop_duplicates(
        subset="ticker", keep="last"
    )[["ticker", "sector", "lastupdated"]]
    quarterly_mc_sector_holdings = quarterly_mc_holdings.merge(
        sector_metadata, on="ticker", how="left", validate="many_to_one"
    )
    quarterly_mc_sector_holdings["sector"] = quarterly_mc_sector_holdings["sector"].fillna(
        "Unknown"
    )
    quarterly_sector_allocation = quarterly_mc_sector_holdings.groupby(
        ["selection_date", "sector"], as_index=False
    ).agg(sector_weight=("target_weight", "sum"))
    quarterly_sector_allocation["sector_weight_pct"] = (
        quarterly_sector_allocation["sector_weight"] * 100
    )
    holdings_per_date = quarterly_mc_holdings.groupby("selection_date").size()
    if not holdings_per_date.eq(10).all():
        raise ValueError("Not every quarterly MC portfolio contains exactly 10 holdings.")
    portfolio_weight_sums = quarterly_mc_holdings.groupby("selection_date")["target_weight"].sum()
    if not np.allclose(portfolio_weight_sums, 1.0, atol=TOLERANCE, rtol=0):
        raise ValueError("Quarterly MC target weights do not sum to 100%.")
    sector_weight_sums = quarterly_sector_allocation.groupby("selection_date")[
        "sector_weight"
    ].sum()
    if not np.allclose(sector_weight_sums, 1.0, atol=TOLERANCE, rtol=0):
        raise ValueError("Quarterly sector weights do not sum to 100%.")
    quarterly_sector_allocation_chart = (
        quarterly_sector_allocation.pivot(
            index="selection_date", columns="sector", values="sector_weight_pct"
        )
        .fillna(0)
        .reset_index()
        .rename(columns={"selection_date": "Date"})
    )
    unknown_weight = (
        quarterly_sector_allocation.loc[quarterly_sector_allocation["sector"].eq("Unknown")]
        .groupby("selection_date")["sector_weight_pct"]
        .sum()
    )
    unknown_weight.max() if not unknown_weight.empty else 0.0
    return (quarterly_sector_allocation, quarterly_sector_allocation_chart)
