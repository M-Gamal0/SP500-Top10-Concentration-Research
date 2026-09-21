"""Factors: samples."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import FactorsConfig


def calculate_samples(strategy_levels_input, *, config: FactorsConfig):
    """Calculate samples with explicit inputs; preserve legacy conventions."""
    strategy_levels = strategy_levels_input
    strategy_levels["date"] = pd.to_datetime(strategy_levels["date"])
    return (strategy_levels,)


def prepare_monthly_portfolio_returns(
    sp500_levels_input, strategy_levels, *, config: FactorsConfig
):
    """Calculate samples with explicit inputs; preserve legacy conventions."""
    STRATEGY_METHOD_LABELS = config.strategy_method_labels
    sp500_levels = sp500_levels_input
    sp500_levels["date"] = pd.to_datetime(sp500_levels["date"])
    if strategy_levels.duplicated(["date", "weighting_method"]).any():
        raise ValueError("Duplicate Top 10 strategy index observations detected.")
    if sp500_levels["date"].duplicated().any():
        raise ValueError("Duplicate S&P 500 TR observations detected.")
    actual_methods = set(strategy_levels["weighting_method"].unique())
    expected_methods = set(STRATEGY_METHOD_LABELS)
    if actual_methods != expected_methods:
        raise ValueError(
            f"Unexpected Top 10 weighting methods. Expected {sorted(expected_methods)}, found {sorted(actual_methods)}."
        )
    strategy_dates = strategy_levels.groupby("weighting_method")["date"].apply(set)
    benchmark_dates = set(sp500_levels["date"])
    for method, dates in strategy_dates.items():
        if dates != benchmark_dates:
            raise ValueError(f"{method}: trading calendar does not match the S&P 500 TR benchmark.")
    strategy_levels["strategy"] = strategy_levels["weighting_method"].map(STRATEGY_METHOD_LABELS)
    strategy_wide = strategy_levels.pivot(
        index="date", columns="strategy", values="total_index_value"
    ).reset_index()
    daily_factor_levels = (
        strategy_wide.merge(
            sp500_levels[["date", "close"]].rename(columns={"close": "S&P 500"}),
            on="date",
            how="inner",
            validate="one_to_one",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )
    required_daily_level_columns = ["MC", "EW", "MC (UCITS)", "S&P 500"]
    if daily_factor_levels[required_daily_level_columns].isna().any().any():
        raise ValueError("Missing values detected in aligned daily strategy levels.")
    monthly_portfolio_returns = (
        daily_factor_levels.set_index("date")[required_daily_level_columns]
        .resample("ME")
        .last()
        .pct_change()
        .dropna()
        .reset_index()
        .rename(
            columns={
                "date": "month_end",
                "MC": "mc_return",
                "EW": "ew_return",
                "MC (UCITS)": "ucits_return",
                "S&P 500": "sp500_return",
            }
        )
    )
    monthly_portfolio_returns["month"] = monthly_portfolio_returns["month_end"].dt.to_period("M")
    monthly_portfolio_returns["active_return"] = (
        monthly_portfolio_returns["mc_return"] - monthly_portfolio_returns["sp500_return"]
    )
    monthly_portfolio_returns["ew_active_return"] = (
        monthly_portfolio_returns["ew_return"] - monthly_portfolio_returns["sp500_return"]
    )
    monthly_portfolio_returns["ucits_active_return"] = (
        monthly_portfolio_returns["ucits_return"] - monthly_portfolio_returns["sp500_return"]
    )
    return (monthly_portfolio_returns,)


def prepare_ff3_monthly(ff3_monthly_input, *, config: FactorsConfig):
    """Calculate samples with explicit inputs; preserve legacy conventions."""
    ff3_monthly = ff3_monthly_input
    ff3_monthly["month_end"] = pd.to_datetime(ff3_monthly["month_end"])
    ff3_monthly["month"] = ff3_monthly["month_end"].dt.to_period("M")
    return (ff3_monthly,)


def prepare_ff5_momentum_monthly(ff5_momentum_monthly_input, *, config: FactorsConfig):
    """Calculate samples with explicit inputs; preserve legacy conventions."""
    ff5_momentum_monthly = ff5_momentum_monthly_input
    ff5_momentum_monthly["month_end"] = pd.to_datetime(ff5_momentum_monthly["month_end"])
    ff5_momentum_monthly["month"] = ff5_momentum_monthly["month_end"].dt.to_period("M")
    return (ff5_momentum_monthly,)


def prepare_factor_monthly_data(
    ff3_monthly,
    ff5_momentum_monthly,
    monthly_portfolio_returns,
    style_monthly_input,
    *,
    config: FactorsConfig,
):
    """Calculate samples with explicit inputs; preserve legacy conventions."""
    RECENT_WINDOW_MONTHS = config.recent_window_months
    TOLERANCE = config.tolerance
    style_monthly = style_monthly_input
    style_monthly["month_end"] = pd.to_datetime(style_monthly["month_end"])
    style_monthly["month"] = style_monthly["month_end"].dt.to_period("M")
    for frame_name, frame in {
        "monthly_portfolio_returns": monthly_portfolio_returns,
        "ff3_monthly": ff3_monthly,
        "ff5_momentum_monthly": ff5_momentum_monthly,
        "style_monthly": style_monthly,
    }.items():
        if frame["month"].duplicated().any():
            raise ValueError(f"Duplicate months detected in {frame_name}.")
    factor_monthly_data = (
        monthly_portfolio_returns[
            [
                "month",
                "mc_return",
                "ew_return",
                "ucits_return",
                "sp500_return",
                "active_return",
                "ew_active_return",
                "ucits_active_return",
            ]
        ]
        .merge(
            ff3_monthly[["month", "mkt_rf", "smb", "hml", "rf"]],
            on="month",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            ff5_momentum_monthly[
                [
                    "month",
                    "ff5_mkt_rf",
                    "ff5_smb",
                    "ff5_hml",
                    "rmw",
                    "cma",
                    "mom",
                    "ff5_rf",
                ]
            ],
            on="month",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            style_monthly[["month", "big_growth_return", "big_value_return"]],
            on="month",
            how="inner",
            validate="one_to_one",
        )
        .sort_values("month")
        .reset_index(drop=True)
    )
    factor_monthly_data["month_end"] = factor_monthly_data["month"].dt.to_timestamp("M")
    factor_monthly_data["style_spread"] = (
        factor_monthly_data["big_growth_return"] - factor_monthly_data["big_value_return"]
    )
    if factor_monthly_data["month"].duplicated().any():
        raise ValueError("Duplicate months detected in factor-attribution dataset.")
    required_columns = [
        "mc_return",
        "ew_return",
        "ucits_return",
        "sp500_return",
        "active_return",
        "ew_active_return",
        "ucits_active_return",
        "mkt_rf",
        "smb",
        "hml",
        "rf",
        "ff5_mkt_rf",
        "ff5_smb",
        "ff5_hml",
        "rmw",
        "cma",
        "mom",
        "ff5_rf",
        "big_growth_return",
        "big_value_return",
        "style_spread",
    ]
    if factor_monthly_data[required_columns].isna().any().any():
        raise ValueError("Missing values detected in the common factor-attribution sample.")
    if len(factor_monthly_data) <= RECENT_WINDOW_MONTHS:
        raise ValueError(
            f"The common sample must contain more than the required {RECENT_WINDOW_MONTHS}-month recent window."
        )
    active_return_checks = {
        "MC": factor_monthly_data["mc_return"]
        - factor_monthly_data["sp500_return"]
        - factor_monthly_data["active_return"],
        "EW": factor_monthly_data["ew_return"]
        - factor_monthly_data["sp500_return"]
        - factor_monthly_data["ew_active_return"],
        "MC (UCITS)": factor_monthly_data["ucits_return"]
        - factor_monthly_data["sp500_return"]
        - factor_monthly_data["ucits_active_return"],
    }
    for strategy, difference in active_return_checks.items():
        if not np.allclose(difference, 0.0, atol=TOLERANCE, rtol=0.0):
            raise ValueError(f"{strategy}: active-return identity does not reconcile.")
    pd.DataFrame(
        [
            {
                "series": "Mkt-RF",
                "max_abs_difference": factor_monthly_data["mkt_rf"]
                .sub(factor_monthly_data["ff5_mkt_rf"])
                .abs()
                .max(),
                "mean_abs_difference": factor_monthly_data["mkt_rf"]
                .sub(factor_monthly_data["ff5_mkt_rf"])
                .abs()
                .mean(),
            },
            {
                "series": "RF",
                "max_abs_difference": factor_monthly_data["rf"]
                .sub(factor_monthly_data["ff5_rf"])
                .abs()
                .max(),
                "mean_abs_difference": factor_monthly_data["rf"]
                .sub(factor_monthly_data["ff5_rf"])
                .abs()
                .mean(),
            },
        ]
    )
    return (factor_monthly_data,)
