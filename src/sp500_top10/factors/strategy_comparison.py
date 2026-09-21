"""Factors: strategy comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import FactorsConfig
from .regression_comparison import fit_active_factor_model_hac


def calculate_strategy_comparison(
    active_return_regression_by_period, factor_monthly_data, *, config: FactorsConfig
):
    """Calculate strategy comparison with explicit inputs; preserve legacy conventions."""
    MULTIFACTOR_FACTORS = config.multifactor_factors
    RECENT_WINDOW_MONTHS = config.recent_window_months
    STRATEGY_ACTIVE_RETURN_COLUMNS = config.strategy_active_return_columns
    TOLERANCE = config.tolerance
    strategy_alpha_period_samples = {
        "Full History": factor_monthly_data.copy(),
        "Recent 10Y": factor_monthly_data.iloc[-RECENT_WINDOW_MONTHS:].copy(),
    }
    if strategy_alpha_period_samples["Full History"].empty:
        raise ValueError("Full History factor sample is empty.")
    if len(strategy_alpha_period_samples["Recent 10Y"]) != RECENT_WINDOW_MONTHS:
        raise ValueError(
            f"Recent 10Y factor sample does not contain exactly {RECENT_WINDOW_MONTHS} months."
        )
    strategy_alpha_rows = []
    for period_name, sample in strategy_alpha_period_samples.items():
        for strategy, dependent_column in STRATEGY_ACTIVE_RETURN_COLUMNS.items():
            model = fit_active_factor_model_hac(
                sample=sample,
                factors=MULTIFACTOR_FACTORS,
                dependent_column=dependent_column,
                config=config,
            )
            conf_int = model.conf_int(alpha=0.05)
            strategy_alpha_rows.append(
                {
                    "model": "FF5 + Momentum",
                    "period": period_name,
                    "strategy": strategy,
                    "start_date": sample["month_end"].iloc[0],
                    "end_date": sample["month_end"].iloc[-1],
                    "n_months": len(sample),
                    "active_return_ann_mean": sample[dependent_column].mean() * 12.0,
                    "alpha_monthly": model.params["const"],
                    "alpha_annualized": model.params["const"] * 12.0,
                    "alpha_hac3_se": model.bse["const"],
                    "alpha_tstat": model.tvalues["const"],
                    "alpha_pvalue": model.pvalues["const"],
                    "alpha_ci95_low_annualized": conf_int.loc["const", 0] * 12.0,
                    "alpha_ci95_high_annualized": conf_int.loc["const", 1] * 12.0,
                    "r_squared": model.rsquared,
                    "adjusted_r_squared": model.rsquared_adj,
                    "beta_mkt": model.params["ff5_mkt_rf"],
                    "beta_smb": model.params["ff5_smb"],
                    "beta_hml": model.params["ff5_hml"],
                    "beta_rmw": model.params["rmw"],
                    "beta_cma": model.params["cma"],
                    "beta_mom": model.params["mom"],
                }
            )
    ff5_momentum_alpha_by_strategy_period = pd.DataFrame(strategy_alpha_rows)
    ff5_momentum_alpha_by_strategy_period["alpha_significant_5pct"] = (
        ff5_momentum_alpha_by_strategy_period["alpha_pvalue"] < 0.05
    )
    expected_rows = len(STRATEGY_ACTIVE_RETURN_COLUMNS) * len(strategy_alpha_period_samples)
    if len(ff5_momentum_alpha_by_strategy_period) != expected_rows:
        raise ValueError(
            f"Unexpected number of strategy-period alpha rows. Expected {expected_rows}, received {len(ff5_momentum_alpha_by_strategy_period)}."
        )
    expected_combinations = {
        (period, strategy)
        for period in strategy_alpha_period_samples
        for strategy in STRATEGY_ACTIVE_RETURN_COLUMNS
    }
    actual_combinations = set(
        ff5_momentum_alpha_by_strategy_period[["period", "strategy"]].itertuples(
            index=False, name=None
        )
    )
    if actual_combinations != expected_combinations:
        raise ValueError("Strategy-period combinations are incomplete or duplicated.")
    sample_date_check = ff5_momentum_alpha_by_strategy_period.groupby("period").agg(
        start_dates=("start_date", "nunique"),
        end_dates=("end_date", "nunique"),
        month_counts=("n_months", "nunique"),
    )
    if not sample_date_check[["start_dates", "end_dates", "month_counts"]].eq(1).all().all():
        raise ValueError("Strategies are not using identical dates within each period.")
    if (
        ff5_momentum_alpha_by_strategy_period[
            ["alpha_annualized", "alpha_tstat", "alpha_pvalue", "adjusted_r_squared"]
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("Missing core statistics in strategy-level FF5 + Momentum output.")
    recent_mc_alpha_row = ff5_momentum_alpha_by_strategy_period.loc[
        ff5_momentum_alpha_by_strategy_period["period"].eq("Recent 10Y")
        & ff5_momentum_alpha_by_strategy_period["strategy"].eq("MC")
    ]
    if len(recent_mc_alpha_row) != 1:
        raise ValueError("Expected exactly one Recent 10Y MC alpha row.")
    recent_mc_alpha_row = recent_mc_alpha_row.iloc[0]
    main_recent_mc_row = active_return_regression_by_period.loc[
        active_return_regression_by_period["period"].eq("Recent 10Y")
    ]
    if len(main_recent_mc_row) != 1:
        raise ValueError("Expected exactly one Recent 10Y MC main-model row.")
    main_recent_mc_row = main_recent_mc_row.iloc[0]
    for strategy_column, main_column in {
        "alpha_annualized": "alpha_annualized",
        "alpha_tstat": "alpha_tstat",
        "adjusted_r_squared": "adjusted_r_squared",
    }.items():
        if not np.isclose(
            recent_mc_alpha_row[strategy_column],
            main_recent_mc_row[main_column],
            atol=TOLERANCE,
            rtol=0.0,
        ):
            raise ValueError(
                "Recent 10Y MC strategy-level result does not reconcile with the main FF5 + Momentum regression."
            )
    for period_name in ["Full History", "Recent 10Y"]:
        period_rows = ff5_momentum_alpha_by_strategy_period.loc[
            ff5_momentum_alpha_by_strategy_period["period"].eq(period_name)
        ]
        for _, row in period_rows.iterrows():
            pass
    return (ff5_momentum_alpha_by_strategy_period,)
