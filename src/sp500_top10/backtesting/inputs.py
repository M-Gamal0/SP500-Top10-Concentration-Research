"""Backtesting: inputs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import BacktestingConfig


def calculate_inputs(quarterly_weights_input, *, config: BacktestingConfig):
    """Calculate inputs with explicit inputs; preserve legacy conventions."""
    CORE_TOP_N = config.core_top_n
    CORE_WEIGHTING_METHODS = config.core_weighting_methods
    PORTFOLIO_SPECS = config.portfolio_specs
    ROBUSTNESS_TOP_N = config.robustness_top_n
    VALIDATION_TOLERANCE = config.validation_tolerance
    quarterly_weights = quarterly_weights_input
    quarterly_weights["selection_date"] = pd.to_datetime(
        quarterly_weights["selection_date"]
    ).dt.normalize()
    if quarterly_weights.empty:
        raise ValueError("No quarterly target weights found.")
    expected_portfolio_specs = set(PORTFOLIO_SPECS)
    actual_portfolio_specs = set(
        quarterly_weights[["top_n", "weighting_method"]].itertuples(index=False, name=None)
    )
    if actual_portfolio_specs != expected_portfolio_specs:
        raise ValueError(
            f"Unexpected portfolio specifications. Expected {expected_portfolio_specs}, found {actual_portfolio_specs}."
        )
    if quarterly_weights.duplicated(
        ["selection_date", "top_n", "weighting_method", "ticker"]
    ).any():
        raise ValueError("Duplicate quarterly target-weight rows detected.")
    portfolio_check = quarterly_weights.groupby(
        ["selection_date", "top_n", "weighting_method"], as_index=False
    ).agg(
        holdings=("ticker", "size"),
        unique_tickers=("ticker", "nunique"),
        weight_sum=("target_weight", "sum"),
    )
    if (portfolio_check["holdings"] != portfolio_check["top_n"]).any() or (
        portfolio_check["unique_tickers"] != portfolio_check["top_n"]
    ).any():
        raise ValueError(
            "At least one portfolio does not contain the configured number of constituents."
        )
    if not np.allclose(portfolio_check["weight_sum"], 1.0, atol=VALIDATION_TOLERANCE):
        raise ValueError("At least one quarterly target portfolio does not sum to 100%.")
    core_weights = quarterly_weights.loc[quarterly_weights["top_n"].eq(CORE_TOP_N)]
    constituent_consistency = core_weights.groupby(["selection_date", "ticker"]).agg(
        methods=("weighting_method", "nunique"), ranks=("rank", "nunique")
    )
    if (constituent_consistency["methods"] != len(CORE_WEIGHTING_METHODS)).any() or (
        constituent_consistency["ranks"] != 1
    ).any():
        raise ValueError(
            "Core Top 10 weighting methods do not share the same quarterly constituent set."
        )
    for selection_date in quarterly_weights["selection_date"].unique():
        top10_tickers = set(
            quarterly_weights.loc[
                quarterly_weights["selection_date"].eq(selection_date)
                & quarterly_weights["top_n"].eq(CORE_TOP_N)
                & quarterly_weights["weighting_method"].eq("market_cap"),
                "ticker",
            ]
        )
        top20_tickers = set(
            quarterly_weights.loc[
                quarterly_weights["selection_date"].eq(selection_date)
                & quarterly_weights["top_n"].eq(ROBUSTNESS_TOP_N)
                & quarterly_weights["weighting_method"].eq("market_cap"),
                "ticker",
            ]
        )
        if not top10_tickers.issubset(top20_tickers):
            raise ValueError(
                f"Top 10 is not nested inside Top 20 on {pd.Timestamp(selection_date).date()}."
            )
    return (quarterly_weights,)
