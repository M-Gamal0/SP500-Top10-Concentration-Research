"""Factors: regression comparison."""

from __future__ import annotations

import pandas as pd
import statsmodels.api as sm

from ..config import FactorsConfig


def fit_active_factor_model_hac(
    sample, factors, dependent_column="active_return", *, config: FactorsConfig
):
    HAC_LAGS = config.hac_lags
    y = sample[dependent_column]
    X = sm.add_constant(sample[factors], has_constant="add")
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
    return model


def calculate_regression_comparison(factor_monthly_data, *, config: FactorsConfig):
    """Calculate regression comparison with explicit inputs; preserve legacy conventions."""
    MULTIFACTOR_FACTORS = config.multifactor_factors
    RECENT_WINDOW_MONTHS = config.recent_window_months
    regression_period_samples = {
        "Earlier History": factor_monthly_data.iloc[:-RECENT_WINDOW_MONTHS].copy(),
        "Recent 10Y": factor_monthly_data.iloc[-RECENT_WINDOW_MONTHS:].copy(),
    }
    earlier_regression_sample = regression_period_samples["Earlier History"]
    recent_regression_sample = regression_period_samples["Recent 10Y"]
    if earlier_regression_sample.empty:
        raise ValueError("Earlier History regression sample is empty.")
    if len(recent_regression_sample) != RECENT_WINDOW_MONTHS:
        raise ValueError(
            f"Recent regression sample does not contain exactly {RECENT_WINDOW_MONTHS} months."
        )
    if earlier_regression_sample["month_end"].max() >= recent_regression_sample["month_end"].min():
        raise ValueError("Earlier History and Recent 10Y regression samples overlap.")
    if len(earlier_regression_sample) + len(recent_regression_sample) != len(factor_monthly_data):
        raise ValueError("Regression samples do not reconcile to the common factor sample.")
    minimum_required_observations = len(MULTIFACTOR_FACTORS) + 2
    if any(
        (
            len(sample) < minimum_required_observations
            for sample in regression_period_samples.values()
        )
    ):
        raise ValueError("Insufficient observations for the FF5 + Momentum regression.")
    regression_rows = []
    for period_name, sample in regression_period_samples.items():
        model = fit_active_factor_model_hac(
            sample=sample, factors=MULTIFACTOR_FACTORS, config=config
        )
        conf_int = model.conf_int(alpha=0.05)
        row = {
            "model": "FF5 + Momentum",
            "period": period_name,
            "start_date": sample["month_end"].iloc[0],
            "end_date": sample["month_end"].iloc[-1],
            "n_months": len(sample),
            "active_return_monthly_mean": sample["active_return"].mean(),
            "active_return_ann_mean": sample["active_return"].mean() * 12.0,
            "alpha_monthly": model.params["const"],
            "alpha_annualized": model.params["const"] * 12.0,
            "alpha_hac3_se": model.bse["const"],
            "alpha_tstat": model.tvalues["const"],
            "alpha_pvalue": model.pvalues["const"],
            "alpha_ci95_low_annualized": conf_int.loc["const", 0] * 12.0,
            "alpha_ci95_high_annualized": conf_int.loc["const", 1] * 12.0,
            "r_squared": model.rsquared,
            "adjusted_r_squared": model.rsquared_adj,
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
            row[f"{output_name}_hac3_se"] = model.bse[factor]
            row[f"{output_name}_tstat"] = model.tvalues[factor]
            row[f"{output_name}_pvalue"] = model.pvalues[factor]
            row[f"{output_name}_ci95_low"] = conf_int.loc[factor, 0]
            row[f"{output_name}_ci95_high"] = conf_int.loc[factor, 1]
        regression_rows.append(row)
    active_return_regression_by_period = pd.DataFrame(regression_rows)
    active_return_regression_by_period["alpha_significant_5pct"] = (
        active_return_regression_by_period["alpha_pvalue"] < 0.05
    )
    active_return_regression_by_period["hml_significant_5pct"] = (
        active_return_regression_by_period["hml_pvalue"] < 0.05
    )
    active_return_regression_by_period["mom_significant_5pct"] = (
        active_return_regression_by_period["mom_pvalue"] < 0.05
    )
    required_regression_columns = [
        "active_return_ann_mean",
        "alpha_annualized",
        "alpha_tstat",
        "beta_mkt",
        "beta_smb",
        "beta_hml",
        "beta_rmw",
        "beta_cma",
        "beta_mom",
        "adjusted_r_squared",
    ]
    if active_return_regression_by_period[required_regression_columns].isna().any().any():
        raise ValueError("Missing values detected in multifactor regression output.")
    if not active_return_regression_by_period["r_squared"].between(0.0, 1.0).all():
        raise ValueError("Multifactor R² falls outside [0, 1].")
    for _, row in active_return_regression_by_period.iterrows():
        pass
    return (active_return_regression_by_period,)
