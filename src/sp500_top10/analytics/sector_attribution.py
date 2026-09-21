"""Analytics: sector attribution."""

from __future__ import annotations

import numpy as np

from ..config import AnalyticsConfig


def calculate_sector_attribution(
    attribution_daily_components, quarterly_portfolio_meta, *, config: AnalyticsConfig
):
    """Calculate sector attribution with explicit inputs; preserve legacy conventions."""
    ATTRIBUTION_TOLERANCE = config.attribution_tolerance
    daily_sector_weights = attribution_daily_components.groupby(
        ["_quarter", "date", "sector"], as_index=False
    ).agg(
        beginning_sector_weight=("beginning_weight", "sum"),
        ending_sector_weight=("ending_weight", "sum"),
    )
    sector_weight_summary = (
        daily_sector_weights.sort_values(["_quarter", "sector", "date"])
        .groupby(["_quarter", "sector"], as_index=False)
        .agg(
            start_sector_weight=("beginning_sector_weight", "first"),
            average_sector_weight=("beginning_sector_weight", "mean"),
            end_sector_weight=("ending_sector_weight", "last"),
        )
    )
    sector_contributions = attribution_daily_components.groupby(
        ["_quarter", "sector"], as_index=False
    ).agg(
        component_count=("ticker", "nunique"),
        exact_contribution=("linked_contribution", "sum"),
    )
    quarterly_sector_attribution = sector_contributions.merge(
        sector_weight_summary,
        on=["_quarter", "sector"],
        how="left",
        validate="one_to_one",
    ).merge(
        quarterly_portfolio_meta[
            [
                "_quarter",
                "quarter",
                "quarter_start",
                "quarter_end",
                "portfolio_total_return",
            ]
        ],
        on="_quarter",
        how="left",
        validate="many_to_one",
    )
    quarterly_sector_attribution["sector_contribution_rank"] = (
        quarterly_sector_attribution.groupby("_quarter")["exact_contribution"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    quarterly_sector_attribution["share_of_portfolio_return_pct"] = np.where(
        quarterly_sector_attribution["portfolio_total_return"].abs() > ATTRIBUTION_TOLERANCE,
        quarterly_sector_attribution["exact_contribution"]
        / quarterly_sector_attribution["portfolio_total_return"]
        * 100,
        np.nan,
    )
    quarterly_sector_attribution["start_sector_weight_pct"] = (
        quarterly_sector_attribution["start_sector_weight"] * 100
    )
    quarterly_sector_attribution["average_sector_weight_pct"] = (
        quarterly_sector_attribution["average_sector_weight"] * 100
    )
    quarterly_sector_attribution["end_sector_weight_pct"] = (
        quarterly_sector_attribution["end_sector_weight"] * 100
    )
    quarterly_sector_attribution["exact_contribution_pp"] = (
        quarterly_sector_attribution["exact_contribution"] * 100
    )
    quarterly_sector_attribution["portfolio_total_return_pct"] = (
        quarterly_sector_attribution["portfolio_total_return"] * 100
    )
    quarterly_sector_attribution = (
        quarterly_sector_attribution[
            [
                "quarter",
                "quarter_start",
                "quarter_end",
                "sector",
                "component_count",
                "start_sector_weight_pct",
                "average_sector_weight_pct",
                "end_sector_weight_pct",
                "exact_contribution_pp",
                "sector_contribution_rank",
                "share_of_portfolio_return_pct",
                "portfolio_total_return_pct",
            ]
        ]
        .sort_values(["quarter_end", "sector_contribution_rank"])
        .reset_index(drop=True)
    )
    return (quarterly_sector_attribution,)
