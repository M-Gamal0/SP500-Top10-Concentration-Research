"""Factors: attribution."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import FactorsConfig
from .regression_comparison import fit_active_factor_model_hac


def calculate_attribution(
    active_return_regression_by_period, factor_monthly_data, *, config: FactorsConfig
):
    """Calculate attribution with explicit inputs; preserve legacy conventions."""
    MULTIFACTOR_FACTORS = config.multifactor_factors
    RECENT_WINDOW_MONTHS = config.recent_window_months
    TOLERANCE = config.tolerance
    recent_attribution_sample = factor_monthly_data.iloc[-RECENT_WINDOW_MONTHS:].copy()
    if len(recent_attribution_sample) != RECENT_WINDOW_MONTHS:
        raise ValueError(
            f"Recent attribution sample does not contain exactly {RECENT_WINDOW_MONTHS} months."
        )
    recent_attribution_model = fit_active_factor_model_hac(
        sample=recent_attribution_sample, factors=MULTIFACTOR_FACTORS, config=config
    )
    recent_regression_rows = active_return_regression_by_period.loc[
        active_return_regression_by_period["period"].eq("Recent 10Y")
    ]
    if len(recent_regression_rows) != 1:
        raise ValueError("Expected exactly one Recent 10Y regression row.")
    recent_regression_row = recent_regression_rows.iloc[0]
    if recent_regression_row["start_date"] != recent_attribution_sample["month_end"].iloc[0]:
        raise ValueError("Recent attribution start date does not match the era regression.")
    if recent_regression_row["end_date"] != recent_attribution_sample["month_end"].iloc[-1]:
        raise ValueError("Recent attribution end date does not match the era regression.")
    if int(recent_regression_row["n_months"]) != len(recent_attribution_sample):
        raise ValueError("Recent attribution observation count does not match the era regression.")
    coefficient_checks = {
        "const": "alpha_monthly",
        "ff5_mkt_rf": "beta_mkt",
        "ff5_smb": "beta_smb",
        "ff5_hml": "beta_hml",
        "rmw": "beta_rmw",
        "cma": "beta_cma",
        "mom": "beta_mom",
    }
    for parameter, summary_column in coefficient_checks.items():
        if not np.isclose(
            recent_attribution_model.params[parameter],
            recent_regression_row[summary_column],
            atol=TOLERANCE,
            rtol=0.0,
        ):
            raise ValueError(
                f"Recent attribution coefficient '{parameter}' does not reconcile with the era regression."
            )
    start_date = recent_attribution_sample["month_end"].iloc[0]
    end_date = recent_attribution_sample["month_end"].iloc[-1]
    n_months = len(recent_attribution_sample)
    observed_active_return_monthly = recent_attribution_sample["active_return"].mean()
    observed_active_return_annualized = observed_active_return_monthly * 12.0
    alpha_monthly = recent_attribution_model.params["const"]
    alpha_annualized = alpha_monthly * 12.0
    alpha_tstat = recent_attribution_model.tvalues["const"]
    alpha_pvalue = recent_attribution_model.pvalues["const"]
    r_squared = recent_attribution_model.rsquared
    adjusted_r_squared = recent_attribution_model.rsquared_adj
    factor_specs = [
        {"component_order": 1, "component": "Market", "factor": "ff5_mkt_rf"},
        {"component_order": 2, "component": "SMB", "factor": "ff5_smb"},
        {"component_order": 3, "component": "HML", "factor": "ff5_hml"},
        {"component_order": 4, "component": "RMW", "factor": "rmw"},
        {"component_order": 5, "component": "CMA", "factor": "cma"},
        {"component_order": 6, "component": "Momentum", "factor": "mom"},
    ]
    attribution_rows = []
    for spec in factor_specs:
        factor = spec["factor"]
        beta = recent_attribution_model.params[factor]
        factor_monthly_mean = recent_attribution_sample[factor].mean()
        monthly_contribution = beta * factor_monthly_mean
        attribution_rows.append(
            {
                "component_order": spec["component_order"],
                "component": spec["component"],
                "factor": factor,
                "component_type": "Systematic Factor",
                "coefficient": beta,
                "coefficient_hac3_se": recent_attribution_model.bse[factor],
                "coefficient_tstat": recent_attribution_model.tvalues[factor],
                "coefficient_pvalue": recent_attribution_model.pvalues[factor],
                "driver_monthly_mean": factor_monthly_mean,
                "driver_annualized_mean": factor_monthly_mean * 12.0,
                "monthly_contribution": monthly_contribution,
                "annualized_contribution": monthly_contribution * 12.0,
                "is_total": False,
            }
        )
    attribution_rows.append(
        {
            "component_order": 7,
            "component": "Factor-Adjusted Alpha",
            "factor": None,
            "component_type": "Alpha",
            "coefficient": alpha_monthly,
            "coefficient_hac3_se": recent_attribution_model.bse["const"],
            "coefficient_tstat": alpha_tstat,
            "coefficient_pvalue": alpha_pvalue,
            "driver_monthly_mean": np.nan,
            "driver_annualized_mean": np.nan,
            "monthly_contribution": alpha_monthly,
            "annualized_contribution": alpha_annualized,
            "is_total": False,
        }
    )
    model_monthly_total = sum((row["monthly_contribution"] for row in attribution_rows))
    model_annualized_total = model_monthly_total * 12.0
    observed_active_return_monthly - model_monthly_total
    reconciliation_difference_annualized = (
        observed_active_return_annualized - model_annualized_total
    )
    if not np.isclose(
        observed_active_return_monthly, model_monthly_total, atol=TOLERANCE, rtol=0.0
    ):
        raise ValueError(
            "Multifactor attribution does not reconcile to the observed monthly active-return mean."
        )
    attribution_rows.append(
        {
            "component_order": 8,
            "component": "Observed Active Return",
            "factor": None,
            "component_type": "Total",
            "coefficient": np.nan,
            "coefficient_hac3_se": np.nan,
            "coefficient_tstat": np.nan,
            "coefficient_pvalue": np.nan,
            "driver_monthly_mean": np.nan,
            "driver_annualized_mean": np.nan,
            "monthly_contribution": observed_active_return_monthly,
            "annualized_contribution": observed_active_return_annualized,
            "is_total": True,
        }
    )
    recent_factor_attribution = pd.DataFrame(attribution_rows)
    recent_factor_attribution["model"] = "FF5 + Momentum"
    recent_factor_attribution["period"] = "Recent 10Y"
    recent_factor_attribution["start_date"] = start_date
    recent_factor_attribution["end_date"] = end_date
    recent_factor_attribution["n_months"] = n_months
    recent_factor_attribution["r_squared"] = r_squared
    recent_factor_attribution["adjusted_r_squared"] = adjusted_r_squared
    recent_factor_attribution["alpha_annualized"] = alpha_annualized
    recent_factor_attribution["alpha_tstat"] = alpha_tstat
    recent_factor_attribution["alpha_pvalue"] = alpha_pvalue
    recent_factor_attribution["observed_active_return_annualized"] = (
        observed_active_return_annualized
    )
    recent_factor_attribution["reconciliation_difference_annualized"] = (
        reconciliation_difference_annualized
    )
    if recent_factor_attribution["component"].duplicated().any():
        raise ValueError("Duplicate attribution components detected.")
    if recent_factor_attribution["is_total"].sum() != 1:
        raise ValueError("Expected exactly one total row in the attribution table.")
    if recent_factor_attribution["annualized_contribution"].isna().any():
        raise ValueError("Missing annualized contribution detected.")
    if not np.isclose(reconciliation_difference_annualized, 0.0, atol=TOLERANCE * 12.0, rtol=0.0):
        raise ValueError("Annualized multifactor attribution failed reconciliation.")
    for _, row in (
        recent_factor_attribution.loc[~recent_factor_attribution["is_total"]]
        .sort_values("component_order")
        .iterrows()
    ):
        pass
    return (recent_factor_attribution,)
