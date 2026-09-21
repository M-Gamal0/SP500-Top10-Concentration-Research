"""Analytics: attribution inputs."""

from __future__ import annotations

import pandas as pd

from ..config import AnalyticsConfig


def add_quarter_linking_factor(group):
    group = group.sort_values("date").copy()
    gross_returns = 1 + group["total_return"]
    if (gross_returns <= 0).any():
        raise ValueError(
            "Portfolio gross return is non-positive; geometric attribution cannot be calculated."
        )
    cumulative_to_end = gross_returns.iloc[::-1].cumprod().iloc[::-1]
    group["linking_factor"] = cumulative_to_end / gross_returns
    return group


def prepare_attribution_index(attribution_daily_index_input, *, config: AnalyticsConfig):
    """Calculate attribution inputs with explicit inputs; preserve legacy conventions."""
    attribution_daily_index = attribution_daily_index_input
    attribution_daily_index["date"] = pd.to_datetime(attribution_daily_index["date"])
    attribution_daily_index = (
        attribution_daily_index.loc[~attribution_daily_index["rebalance_type"].eq("initial_base")]
        .copy()
        .reset_index(drop=True)
    )
    return (attribution_daily_index,)


def prepare_attribution_weights(attribution_daily_weights_input, *, config: AnalyticsConfig):
    """Calculate attribution inputs with explicit inputs; preserve legacy conventions."""
    attribution_daily_weights = attribution_daily_weights_input
    attribution_daily_weights["date"] = pd.to_datetime(attribution_daily_weights["date"])
    attribution_daily_weights = (
        attribution_daily_weights.loc[
            ~attribution_daily_weights["rebalance_type"].eq("initial_base")
        ]
        .copy()
        .reset_index(drop=True)
    )
    return (attribution_daily_weights,)


def prepare_component_names(component_names_input, *, config: AnalyticsConfig):
    """Calculate attribution inputs with explicit inputs; preserve legacy conventions."""
    component_names = component_names_input
    return (component_names,)


def prepare_linked_contributions(
    attribution_daily_index,
    attribution_daily_weights,
    component_names,
    component_sectors_input,
    *,
    config: AnalyticsConfig,
):
    """Calculate attribution inputs with explicit inputs; preserve legacy conventions."""
    ATTRIBUTION_TOLERANCE = config.attribution_tolerance
    component_sectors = component_sectors_input
    component_metadata = component_names.merge(
        component_sectors, on="ticker", how="left", validate="one_to_one"
    )
    component_metadata["company"] = component_metadata["company"].fillna(
        component_metadata["ticker"]
    )
    component_metadata["sector"] = component_metadata["sector"].fillna("Unknown")
    attribution_daily_index["_quarter"] = attribution_daily_index["date"].dt.to_period("Q")
    attribution_daily_weights["_quarter"] = attribution_daily_weights["date"].dt.to_period("Q")
    daily_component_sum = attribution_daily_weights.groupby("date")[
        "total_return_contribution"
    ].sum()
    daily_portfolio_return = attribution_daily_index.set_index("date")["total_return"]
    daily_reconciliation = daily_component_sum - daily_portfolio_return
    if daily_reconciliation.abs().max() > ATTRIBUTION_TOLERANCE:
        raise ValueError("Daily component contributions do not reconcile to portfolio returns.")
    attribution_daily_index = (
        attribution_daily_index.groupby("_quarter", group_keys=False)
        .apply(add_quarter_linking_factor, include_groups=False)
        .reset_index(drop=True)
    )
    attribution_daily_index["_quarter"] = attribution_daily_index["date"].dt.to_period("Q")
    quarterly_portfolio_meta = attribution_daily_index.groupby("_quarter", as_index=False).agg(
        quarter_start=("date", "min"),
        quarter_end=("date", "max"),
        quarter_trading_days=("date", "size"),
        portfolio_total_return=("total_return", lambda x: (1 + x).prod() - 1),
    )
    quarterly_portfolio_meta["quarter"] = quarterly_portfolio_meta["_quarter"].astype(str)
    attribution_daily_components = attribution_daily_weights.merge(
        attribution_daily_index[["date", "linking_factor"]],
        on="date",
        how="left",
        validate="many_to_one",
    ).merge(component_metadata, on="ticker", how="left", validate="many_to_one")
    attribution_daily_components["company"] = attribution_daily_components["company"].fillna(
        attribution_daily_components["ticker"]
    )
    attribution_daily_components["sector"] = attribution_daily_components["sector"].fillna(
        "Unknown"
    )
    attribution_daily_components["linked_contribution"] = (
        attribution_daily_components["total_return_contribution"]
        * attribution_daily_components["linking_factor"]
    )
    return (attribution_daily_components, quarterly_portfolio_meta)
