"""Factors: exposure."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from ..config import FactorsConfig


def fit_ff3_portfolio_hac(sample, portfolio, *, config: FactorsConfig):
    HAC_LAGS = config.hac_lags
    return_column = {"MC": "mc_return", "S&P 500": "sp500_return"}[portfolio]
    y = sample[return_column] - sample["rf"]
    X = sm.add_constant(sample[["mkt_rf", "smb", "hml"]], has_constant="add")
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
    return model


def calculate_exposure(factor_monthly_data, *, config: FactorsConfig):
    """Calculate exposure with explicit inputs; preserve legacy conventions."""
    EXPOSURE_WINDOW_MONTHS = config.exposure_window_months
    FACTOR_PORTFOLIOS = config.factor_portfolios
    rolling_rows = []
    for end_idx in range(EXPOSURE_WINDOW_MONTHS - 1, len(factor_monthly_data)):
        sample = factor_monthly_data.iloc[end_idx - EXPOSURE_WINDOW_MONTHS + 1 : end_idx + 1]
        window_start = sample["month_end"].iloc[0]
        window_end = sample["month_end"].iloc[-1]
        for portfolio in FACTOR_PORTFOLIOS:
            fit = fit_ff3_portfolio_hac(sample, portfolio, config=config)
            hml_beta = fit.params["hml"]
            hml_se = fit.bse["hml"]
            rolling_rows.append(
                {
                    "window_start": window_start,
                    "window_end": window_end,
                    "portfolio": portfolio,
                    "n_months": len(sample),
                    "hml_beta": hml_beta,
                    "hml_hac3_se": hml_se,
                    "hml_ci95_low": hml_beta - 1.96 * hml_se,
                    "hml_ci95_high": hml_beta + 1.96 * hml_se,
                }
            )
    rolling_hml_exposures = pd.DataFrame(rolling_rows)
    if rolling_hml_exposures.empty:
        raise ValueError("No rolling HML regressions were produced.")
    if not rolling_hml_exposures["n_months"].eq(EXPOSURE_WINDOW_MONTHS).all():
        raise ValueError(
            f"Not every FF3 regression contains exactly {EXPOSURE_WINDOW_MONTHS} months."
        )
    if (
        rolling_hml_exposures[["hml_beta", "hml_hac3_se", "hml_ci95_low", "hml_ci95_high"]]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("Missing values detected in rolling HML estimates.")
    mc_hml = rolling_hml_exposures.loc[
        rolling_hml_exposures["portfolio"].eq("MC"),
        ["window_end", "hml_beta", "hml_ci95_low", "hml_ci95_high"],
    ].rename(
        columns={
            "window_end": "Date",
            "hml_beta": "MC",
            "hml_ci95_low": "MC CI Low",
            "hml_ci95_high": "MC CI High",
        }
    )
    sp500_hml = rolling_hml_exposures.loc[
        rolling_hml_exposures["portfolio"].eq("S&P 500"), ["window_end", "hml_beta"]
    ].rename(columns={"window_end": "Date", "hml_beta": "S&P 500"})
    rolling_36m_hml_chart = mc_hml.merge(sp500_hml, on="Date", how="inner", validate="one_to_one")[
        ["Date", "MC", "MC CI Low", "MC CI High", "S&P 500"]
    ]
    factor_exposure_summary = pd.DataFrame(
        [
            {
                "index": portfolio,
                "first_hml_beta": rolling_hml_exposures.loc[
                    rolling_hml_exposures["portfolio"].eq(portfolio), "hml_beta"
                ].iloc[0],
                "latest_hml_beta": rolling_hml_exposures.loc[
                    rolling_hml_exposures["portfolio"].eq(portfolio), "hml_beta"
                ].iloc[-1],
                "median_hml_beta": rolling_hml_exposures.loc[
                    rolling_hml_exposures["portfolio"].eq(portfolio), "hml_beta"
                ].median(),
                "minimum_hml_beta": rolling_hml_exposures.loc[
                    rolling_hml_exposures["portfolio"].eq(portfolio), "hml_beta"
                ].min(),
                "maximum_hml_beta": rolling_hml_exposures.loc[
                    rolling_hml_exposures["portfolio"].eq(portfolio), "hml_beta"
                ].max(),
                "pct_windows_growth_sensitive": (
                    rolling_hml_exposures.loc[
                        rolling_hml_exposures["portfolio"].eq(portfolio), "hml_beta"
                    ]
                    < 0
                ).mean()
                * 100,
            }
            for portfolio in FACTOR_PORTFOLIOS
        ]
    )
    latest_mc = rolling_hml_exposures.loc[rolling_hml_exposures["portfolio"].eq("MC")].iloc[-1]
    factor_exposure_summary["latest_hml_ci95_low"] = np.nan
    factor_exposure_summary["latest_hml_ci95_high"] = np.nan
    factor_exposure_summary.loc[
        factor_exposure_summary["index"].eq("MC"), "latest_hml_ci95_low"
    ] = latest_mc["hml_ci95_low"]
    factor_exposure_summary.loc[
        factor_exposure_summary["index"].eq("MC"), "latest_hml_ci95_high"
    ] = latest_mc["hml_ci95_high"]
    return (factor_exposure_summary, rolling_36m_hml_chart, rolling_hml_exposures)
