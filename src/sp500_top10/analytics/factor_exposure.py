"""Analytics: factor exposure."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from ..config import AnalyticsConfig


def fit_ff3_hac(sample, portfolio, *, config: AnalyticsConfig):
    FF3_HAC_LAGS = config.ff3_hac_lags
    y = sample[portfolio] - sample["rf"]
    X = sm.add_constant(sample[["mkt_rf", "smb", "hml"]], has_constant="add")
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": FF3_HAC_LAGS})
    return model


def prepare_exposure_returns(growth_1000_wide, *, config: AnalyticsConfig):
    """Calculate factor exposure with explicit inputs; preserve legacy conventions."""
    factor_monthly_returns = (
        growth_1000_wide.set_index("date")[["S&P 500", "MC"]]
        .resample("ME")
        .last()
        .pct_change()
        .dropna()
        .reset_index()
        .rename(columns={"date": "month_end"})
    )
    factor_monthly_returns["month"] = factor_monthly_returns["month_end"].dt.to_period("M")
    return (factor_monthly_returns,)


def calculate_factor_exposure(
    factor_monthly_returns, ff3_monthly_input, *, config: AnalyticsConfig
):
    """Calculate factor exposure with explicit inputs; preserve legacy conventions."""
    FACTOR_PORTFOLIOS = config.factor_portfolios
    FF3_WINDOW_MONTHS = config.ff3_window_months
    ff3_monthly = ff3_monthly_input
    ff3_monthly["month_end"] = pd.to_datetime(ff3_monthly["month_end"])
    ff3_monthly["month"] = ff3_monthly["month_end"].dt.to_period("M")
    factor_regression_data = (
        factor_monthly_returns[["month", "S&P 500", "MC"]]
        .merge(
            ff3_monthly[["month", "mkt_rf", "smb", "hml", "rf"]],
            on="month",
            how="inner",
            validate="one_to_one",
        )
        .sort_values("month")
        .reset_index(drop=True)
    )
    rolling_rows = []
    for end_idx in range(FF3_WINDOW_MONTHS - 1, len(factor_regression_data)):
        sample = factor_regression_data.iloc[end_idx - FF3_WINDOW_MONTHS + 1 : end_idx + 1]
        window_start = sample["month"].iloc[0].to_timestamp("M")
        window_end = sample["month"].iloc[-1].to_timestamp("M")
        for portfolio in FACTOR_PORTFOLIOS:
            fit = fit_ff3_hac(sample, portfolio, config=config)
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
    if not rolling_hml_exposures["n_months"].eq(FF3_WINDOW_MONTHS).all():
        raise ValueError(f"Not every FF3 regression contains exactly {FF3_WINDOW_MONTHS} months.")
    if (
        rolling_hml_exposures[["hml_beta", "hml_hac3_se", "hml_ci95_low", "hml_ci95_high"]]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("Missing values detected in rolling HML estimates.")
    if not (rolling_hml_exposures["hml_ci95_low"] <= rolling_hml_exposures["hml_beta"]).all():
        raise ValueError("Invalid lower confidence bound.")
    if not (rolling_hml_exposures["hml_beta"] <= rolling_hml_exposures["hml_ci95_high"]).all():
        raise ValueError("Invalid upper confidence bound.")
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
