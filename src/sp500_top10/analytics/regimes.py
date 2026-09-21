"""Analytics: regimes."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def prepare_benchmark_months(growth_1000_wide, *, config: AnalyticsConfig):
    """Calculate regimes with explicit inputs; preserve legacy conventions."""
    sp500_monthly = growth_1000_wide[["date", "S&P 500"]].set_index("date").resample("ME").last()
    sp500_monthly["sp500_return"] = sp500_monthly["S&P 500"].pct_change()
    sp500_monthly = (
        sp500_monthly.dropna(subset=["sp500_return"])
        .reset_index()
        .rename(columns={"date": "month_end"})
    )
    sp500_monthly["month"] = sp500_monthly["month_end"].dt.to_period("M")
    return (sp500_monthly,)


def classify_market_style_regimes(sp500_monthly, style_monthly_input, *, config: AnalyticsConfig):
    """Calculate regimes with explicit inputs; preserve legacy conventions."""
    MARKET_DOWN_THRESHOLD = config.market_down_threshold
    MARKET_STATE_ORDER = config.market_state_order
    MARKET_UP_THRESHOLD = config.market_up_threshold
    STYLE_GROWTH_THRESHOLD = config.style_growth_threshold
    STYLE_STATE_ORDER = config.style_state_order
    STYLE_VALUE_THRESHOLD = config.style_value_threshold
    style_monthly = style_monthly_input
    style_monthly["month_end"] = pd.to_datetime(style_monthly["month_end"])
    style_monthly["month"] = style_monthly["month_end"].dt.to_period("M")
    monthly_market_style_states = (
        sp500_monthly[["month", "sp500_return"]]
        .merge(
            style_monthly[["month", "big_growth_return", "big_value_return"]],
            on="month",
            how="inner",
            validate="one_to_one",
        )
        .sort_values("month")
        .reset_index(drop=True)
    )
    monthly_market_style_states["month_end"] = monthly_market_style_states["month"].dt.to_timestamp(
        "M"
    )
    monthly_market_style_states["style_spread"] = (
        monthly_market_style_states["big_growth_return"]
        - monthly_market_style_states["big_value_return"]
    )
    monthly_market_style_states["style_spread_pp"] = (
        monthly_market_style_states["style_spread"] * 100
    )
    monthly_market_style_states["market_state"] = np.select(
        [
            monthly_market_style_states["sp500_return"] < MARKET_DOWN_THRESHOLD,
            monthly_market_style_states["sp500_return"] > MARKET_UP_THRESHOLD,
        ],
        ["Market Down", "Market Up"],
        default="Market Neutral",
    )
    monthly_market_style_states["style_state"] = np.select(
        [
            monthly_market_style_states["style_spread"] < STYLE_VALUE_THRESHOLD,
            monthly_market_style_states["style_spread"] > STYLE_GROWTH_THRESHOLD,
        ],
        ["Value-Led", "Growth-Led"],
        default="Neutral Style",
    )
    monthly_market_style_states["combined_state"] = (
        monthly_market_style_states["market_state"]
        + " / "
        + monthly_market_style_states["style_state"]
    )
    monthly_market_style_states = monthly_market_style_states[
        [
            "month_end",
            "sp500_return",
            "big_growth_return",
            "big_value_return",
            "style_spread_pp",
            "market_state",
            "style_state",
            "combined_state",
        ]
    ].copy()
    market_style_state_counts = (
        monthly_market_style_states.groupby(["market_state", "style_state"], as_index=False)
        .size()
        .rename(columns={"size": "n_months"})
    )
    all_states = pd.MultiIndex.from_product(
        [MARKET_STATE_ORDER, STYLE_STATE_ORDER], names=["market_state", "style_state"]
    ).to_frame(index=False)
    market_style_state_counts = all_states.merge(
        market_style_state_counts, on=["market_state", "style_state"], how="left"
    )
    market_style_state_counts["n_months"] = (
        market_style_state_counts["n_months"].fillna(0).astype(int)
    )
    market_style_state_matrix = (
        market_style_state_counts.pivot(
            index="market_state", columns="style_state", values="n_months"
        )
        .reindex(index=MARKET_STATE_ORDER, columns=STYLE_STATE_ORDER)
        .reset_index()
        .rename(columns={"market_state": "Market State"})
    )
    if monthly_market_style_states["month_end"].duplicated().any():
        raise ValueError("Duplicate months detected in market/style states.")
    if (
        monthly_market_style_states[
            ["sp500_return", "big_growth_return", "big_value_return", "style_spread_pp"]
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("Missing values detected in market/style state inputs.")
    if len(market_style_state_counts) != 9:
        raise ValueError("Expected exactly 9 market/style states.")
    if market_style_state_counts["n_months"].sum() != len(monthly_market_style_states):
        raise ValueError("Market/style state counts do not reconcile to the monthly common sample.")
    return (
        market_style_state_counts,
        market_style_state_matrix,
        monthly_market_style_states,
    )
