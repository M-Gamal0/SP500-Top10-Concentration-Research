"""Factors: model comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import FactorsConfig
from .regression_comparison import fit_active_factor_model_hac


def calculate_model_comparison(
    active_return_regression_by_period, factor_monthly_data, *, config: FactorsConfig
):
    """Calculate model comparison with explicit inputs; preserve legacy conventions."""
    MODEL_SPECS = config.model_specs
    RECENT_WINDOW_MONTHS = config.recent_window_months
    TOLERANCE = config.tolerance
    robustness_sample = factor_monthly_data.iloc[-RECENT_WINDOW_MONTHS:].copy()
    if len(robustness_sample) != RECENT_WINDOW_MONTHS:
        raise ValueError(
            f"Robustness sample does not contain exactly {RECENT_WINDOW_MONTHS} months."
        )
    robustness_rows = []
    for model_order, (model_name, specification) in enumerate(MODEL_SPECS.items(), start=1):
        factors = specification["factors"]
        model = fit_active_factor_model_hac(
            sample=robustness_sample, factors=factors, config=config
        )
        conf_int = model.conf_int(alpha=0.05)
        row = {
            "model_order": model_order,
            "model": model_name,
            "period": "Recent 10Y",
            "start_date": robustness_sample["month_end"].iloc[0],
            "end_date": robustness_sample["month_end"].iloc[-1],
            "n_months": len(robustness_sample),
            "n_factors": len(factors),
            "active_return_ann_mean": robustness_sample["active_return"].mean() * 12.0,
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
        hml_factor = specification["hml_factor"]
        if hml_factor is not None:
            row["hml_beta"] = model.params[hml_factor]
            row["hml_tstat"] = model.tvalues[hml_factor]
            row["hml_pvalue"] = model.pvalues[hml_factor]
        else:
            row["hml_beta"] = np.nan
            row["hml_tstat"] = np.nan
            row["hml_pvalue"] = np.nan
        mom_factor = specification["mom_factor"]
        if mom_factor is not None:
            row["mom_beta"] = model.params[mom_factor]
            row["mom_tstat"] = model.tvalues[mom_factor]
            row["mom_pvalue"] = model.pvalues[mom_factor]
        else:
            row["mom_beta"] = np.nan
            row["mom_tstat"] = np.nan
            row["mom_pvalue"] = np.nan
        robustness_rows.append(row)
    factor_model_robustness_recent_10y = pd.DataFrame(robustness_rows)
    if factor_model_robustness_recent_10y["model"].tolist() != list(MODEL_SPECS.keys()):
        raise ValueError("Robustness model ordering changed unexpectedly.")
    if not factor_model_robustness_recent_10y["n_months"].eq(RECENT_WINDOW_MONTHS).all():
        raise ValueError("Robustness models are not using the same 120-month sample.")
    if not (
        factor_model_robustness_recent_10y["start_date"].nunique() == 1
        and factor_model_robustness_recent_10y["end_date"].nunique() == 1
    ):
        raise ValueError("Robustness models do not share identical sample dates.")
    if (
        factor_model_robustness_recent_10y[
            ["alpha_annualized", "alpha_tstat", "adjusted_r_squared"]
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("Missing core statistics in factor-model robustness output.")
    main_model_row = factor_model_robustness_recent_10y.loc[
        factor_model_robustness_recent_10y["model"].eq("FF5 + Momentum")
    ].iloc[0]
    main_era_row = active_return_regression_by_period.loc[
        active_return_regression_by_period["period"].eq("Recent 10Y")
    ].iloc[0]
    for robustness_column, era_column in {
        "alpha_annualized": "alpha_annualized",
        "alpha_tstat": "alpha_tstat",
        "adjusted_r_squared": "adjusted_r_squared",
    }.items():
        if not np.isclose(
            main_model_row[robustness_column],
            main_era_row[era_column],
            atol=TOLERANCE,
            rtol=0.0,
        ):
            raise ValueError(
                "FF5 + Momentum robustness result does not reconcile with the main Recent 10Y era regression."
            )
    for _, row in factor_model_robustness_recent_10y.iterrows():
        pass
    return (factor_model_robustness_recent_10y,)
