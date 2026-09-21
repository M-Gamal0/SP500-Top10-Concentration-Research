"""Factors: persistence."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import FactorsConfig
from .regression_comparison import fit_active_factor_model_hac


def calculate_persistence(factor_monthly_data, *, config: FactorsConfig):
    """Calculate persistence with explicit inputs; preserve legacy conventions."""
    MULTIFACTOR_FACTORS = config.multifactor_factors
    ROLLING_ACTIVE_WINDOW_MONTHS = config.rolling_active_window_months
    TOLERANCE = config.tolerance
    if len(factor_monthly_data) < ROLLING_ACTIVE_WINDOW_MONTHS:
        raise ValueError(
            f"The common factor sample is shorter than the required {ROLLING_ACTIVE_WINDOW_MONTHS}-month rolling window."
        )
    if ROLLING_ACTIVE_WINDOW_MONTHS <= len(MULTIFACTOR_FACTORS) + 1:
        raise ValueError("Rolling window is too short for the selected multifactor model.")
    required_rolling_columns = ["month_end", "active_return", *MULTIFACTOR_FACTORS]
    if factor_monthly_data[required_rolling_columns].isna().any().any():
        raise ValueError("Missing values detected in the rolling factor-adjustment sample.")
    rolling_factor_adjusted_rows = []
    for end_idx in range(ROLLING_ACTIVE_WINDOW_MONTHS - 1, len(factor_monthly_data)):
        sample = factor_monthly_data.iloc[
            end_idx - ROLLING_ACTIVE_WINDOW_MONTHS + 1 : end_idx + 1
        ].copy()
        model = fit_active_factor_model_hac(
            sample=sample, factors=MULTIFACTOR_FACTORS, config=config
        )
        conf_int = model.conf_int(alpha=0.05)
        raw_active_return_monthly_mean = sample["active_return"].mean()
        raw_active_return_annualized = raw_active_return_monthly_mean * 12.0
        alpha_monthly = model.params["const"]
        alpha_annualized = alpha_monthly * 12.0
        systematic_contribution_monthly = sum(
            (model.params[factor] * sample[factor].mean() for factor in MULTIFACTOR_FACTORS)
        )
        model_implied_active_return_monthly = alpha_monthly + systematic_contribution_monthly
        reconciliation_difference = (
            raw_active_return_monthly_mean - model_implied_active_return_monthly
        )
        if not np.isclose(reconciliation_difference, 0.0, atol=TOLERANCE, rtol=0.0):
            raise ValueError(
                f"Rolling FF5 + Momentum attribution failed to reconcile for window ending {sample['month_end'].iloc[-1]:%Y-%m}."
            )
        row = {
            "model": "FF5 + Momentum",
            "window_start": sample["month_end"].iloc[0],
            "window_end": sample["month_end"].iloc[-1],
            "n_months": len(sample),
            "raw_active_return_monthly_mean": raw_active_return_monthly_mean,
            "raw_active_return_annualized": raw_active_return_annualized,
            "alpha_monthly": alpha_monthly,
            "alpha_annualized": alpha_annualized,
            "alpha_hac3_se": model.bse["const"],
            "alpha_tstat": model.tvalues["const"],
            "alpha_pvalue": model.pvalues["const"],
            "alpha_ci95_low_annualized": conf_int.loc["const", 0] * 12.0,
            "alpha_ci95_high_annualized": conf_int.loc["const", 1] * 12.0,
            "r_squared": model.rsquared,
            "adjusted_r_squared": model.rsquared_adj,
            "systematic_contribution_annualized": systematic_contribution_monthly * 12.0,
            "model_implied_active_return_annualized": model_implied_active_return_monthly * 12.0,
            "reconciliation_difference": reconciliation_difference * 12.0,
        }
        for factor in MULTIFACTOR_FACTORS:
            output_name = {
                "ff5_mkt_rf": "mkt",
                "ff5_smb": "smb",
                "ff5_hml": "hml",
                "rmw": "rmw",
                "cma": "cma",
                "mom": "mom",
            }[factor]
            row[f"beta_{output_name}"] = model.params[factor]
            row[f"{output_name}_tstat"] = model.tvalues[factor]
            row[f"{output_name}_pvalue"] = model.pvalues[factor]
        rolling_factor_adjusted_rows.append(row)
    rolling_factor_adjusted_performance = pd.DataFrame(rolling_factor_adjusted_rows)
    rolling_factor_adjusted_performance["raw_active_return_positive"] = (
        rolling_factor_adjusted_performance["raw_active_return_annualized"] > 0.0
    )
    rolling_factor_adjusted_performance["alpha_positive"] = (
        rolling_factor_adjusted_performance["alpha_annualized"] > 0.0
    )
    rolling_factor_adjusted_performance["alpha_significant_positive_5pct"] = (
        rolling_factor_adjusted_performance["alpha_annualized"] > 0.0
    ) & (rolling_factor_adjusted_performance["alpha_pvalue"] < 0.05)
    rolling_factor_adjusted_performance["alpha_significant_negative_5pct"] = (
        rolling_factor_adjusted_performance["alpha_annualized"] < 0.0
    ) & (rolling_factor_adjusted_performance["alpha_pvalue"] < 0.05)
    if rolling_factor_adjusted_performance.empty:
        raise ValueError("No rolling active-return regressions were produced.")
    if not rolling_factor_adjusted_performance["n_months"].eq(ROLLING_ACTIVE_WINDOW_MONTHS).all():
        raise ValueError(
            f"Not every rolling regression contains exactly {ROLLING_ACTIVE_WINDOW_MONTHS} months."
        )
    if not rolling_factor_adjusted_performance["r_squared"].between(0.0, 1.0).all():
        raise ValueError("Rolling R² falls outside [0, 1].")
    if not np.allclose(
        rolling_factor_adjusted_performance["reconciliation_difference"],
        0.0,
        atol=TOLERANCE * 12.0,
        rtol=0.0,
    ):
        raise ValueError("One or more rolling multifactor attributions failed reconciliation.")
    expected_rolling_windows = len(factor_monthly_data) - ROLLING_ACTIVE_WINDOW_MONTHS + 1
    if len(rolling_factor_adjusted_performance) != expected_rolling_windows:
        raise ValueError(
            f"Unexpected number of rolling regressions. Expected {expected_rolling_windows}, received {len(rolling_factor_adjusted_performance)}."
        )
    factor_adjusted_persistence_summary = pd.DataFrame(
        [
            {
                "model": "FF5 + Momentum",
                "rolling_window_months": ROLLING_ACTIVE_WINDOW_MONTHS,
                "n_windows": len(rolling_factor_adjusted_performance),
                "first_window_end": rolling_factor_adjusted_performance["window_end"].min(),
                "latest_window_end": rolling_factor_adjusted_performance["window_end"].max(),
                "pct_windows_raw_active_positive": rolling_factor_adjusted_performance[
                    "raw_active_return_positive"
                ].mean()
                * 100.0,
                "pct_windows_alpha_positive": rolling_factor_adjusted_performance[
                    "alpha_positive"
                ].mean()
                * 100.0,
                "pct_windows_alpha_significant_positive_5pct": rolling_factor_adjusted_performance[
                    "alpha_significant_positive_5pct"
                ].mean()
                * 100.0,
                "pct_windows_alpha_significant_negative_5pct": rolling_factor_adjusted_performance[
                    "alpha_significant_negative_5pct"
                ].mean()
                * 100.0,
                "median_raw_active_return_annualized": rolling_factor_adjusted_performance[
                    "raw_active_return_annualized"
                ].median(),
                "median_alpha_annualized": rolling_factor_adjusted_performance[
                    "alpha_annualized"
                ].median(),
                "latest_raw_active_return_annualized": rolling_factor_adjusted_performance[
                    "raw_active_return_annualized"
                ].iloc[-1],
                "latest_alpha_annualized": rolling_factor_adjusted_performance[
                    "alpha_annualized"
                ].iloc[-1],
                "latest_alpha_tstat": rolling_factor_adjusted_performance["alpha_tstat"].iloc[-1],
                "latest_adjusted_r_squared": rolling_factor_adjusted_performance[
                    "adjusted_r_squared"
                ].iloc[-1],
            }
        ]
    )
    factor_adjusted_persistence_summary.iloc[0]
    return (factor_adjusted_persistence_summary, rolling_factor_adjusted_performance)
