"""Analytics: component attribution."""

from __future__ import annotations

import numpy as np

from ..config import AnalyticsConfig


def calculate_component_attribution(
    attribution_daily_components, quarterly_portfolio_meta, *, config: AnalyticsConfig
):
    """Calculate component attribution with explicit inputs; preserve legacy conventions."""
    ATTRIBUTION_TOLERANCE = config.attribution_tolerance
    quarterly_component_returns = (
        attribution_daily_components.sort_values(["_quarter", "ticker", "date"])
        .groupby(["_quarter", "ticker", "company", "sector"], as_index=False)
        .agg(
            held_days=("date", "size"),
            start_weight=("beginning_weight", "first"),
            average_weight=("beginning_weight", "mean"),
            end_weight=("ending_weight", "last"),
            component_total_return=("total_return", lambda x: (1 + x).prod() - 1),
        )
    )
    quarterly_component_returns = quarterly_component_returns.merge(
        quarterly_portfolio_meta[
            [
                "_quarter",
                "quarter",
                "quarter_start",
                "quarter_end",
                "quarter_trading_days",
                "portfolio_total_return",
            ]
        ],
        on="_quarter",
        how="left",
        validate="many_to_one",
    )
    quarterly_component_returns["return_rank"] = (
        quarterly_component_returns.groupby("_quarter")["component_total_return"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    quarterly_component_returns["start_weight_pct"] = (
        quarterly_component_returns["start_weight"] * 100
    )
    quarterly_component_returns["average_weight_pct"] = (
        quarterly_component_returns["average_weight"] * 100
    )
    quarterly_component_returns["end_weight_pct"] = quarterly_component_returns["end_weight"] * 100
    quarterly_component_returns["component_total_return_pct"] = (
        quarterly_component_returns["component_total_return"] * 100
    )
    quarterly_component_returns["portfolio_total_return_pct"] = (
        quarterly_component_returns["portfolio_total_return"] * 100
    )
    quarterly_component_returns = (
        quarterly_component_returns[
            [
                "quarter",
                "quarter_start",
                "quarter_end",
                "ticker",
                "company",
                "sector",
                "held_days",
                "quarter_trading_days",
                "start_weight_pct",
                "average_weight_pct",
                "end_weight_pct",
                "component_total_return_pct",
                "return_rank",
                "portfolio_total_return_pct",
            ]
        ]
        .sort_values(["quarter_end", "return_rank"])
        .reset_index(drop=True)
    )
    quarterly_component_attribution = attribution_daily_components.groupby(
        ["_quarter", "ticker", "company", "sector"], as_index=False
    ).agg(
        exact_contribution=("linked_contribution", "sum"),
        start_weight=("beginning_weight", "first"),
        average_weight=("beginning_weight", "mean"),
        end_weight=("ending_weight", "last"),
        component_total_return=("total_return", lambda x: (1 + x).prod() - 1),
    )
    quarterly_component_attribution = quarterly_component_attribution.merge(
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
    quarterly_component_attribution["contribution_rank"] = (
        quarterly_component_attribution.groupby("_quarter")["exact_contribution"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    quarterly_component_attribution["share_of_portfolio_return_pct"] = np.where(
        quarterly_component_attribution["portfolio_total_return"].abs() > ATTRIBUTION_TOLERANCE,
        quarterly_component_attribution["exact_contribution"]
        / quarterly_component_attribution["portfolio_total_return"]
        * 100,
        np.nan,
    )
    quarterly_component_attribution["start_weight_pct"] = (
        quarterly_component_attribution["start_weight"] * 100
    )
    quarterly_component_attribution["average_weight_pct"] = (
        quarterly_component_attribution["average_weight"] * 100
    )
    quarterly_component_attribution["end_weight_pct"] = (
        quarterly_component_attribution["end_weight"] * 100
    )
    quarterly_component_attribution["component_total_return_pct"] = (
        quarterly_component_attribution["component_total_return"] * 100
    )
    quarterly_component_attribution["exact_contribution_pp"] = (
        quarterly_component_attribution["exact_contribution"] * 100
    )
    quarterly_component_attribution["portfolio_total_return_pct"] = (
        quarterly_component_attribution["portfolio_total_return"] * 100
    )
    quarterly_component_attribution = (
        quarterly_component_attribution[
            [
                "quarter",
                "quarter_start",
                "quarter_end",
                "ticker",
                "company",
                "sector",
                "start_weight_pct",
                "average_weight_pct",
                "end_weight_pct",
                "component_total_return_pct",
                "exact_contribution_pp",
                "contribution_rank",
                "share_of_portfolio_return_pct",
                "portfolio_total_return_pct",
            ]
        ]
        .sort_values(["quarter_end", "contribution_rank"])
        .reset_index(drop=True)
    )
    return (quarterly_component_attribution, quarterly_component_returns)
