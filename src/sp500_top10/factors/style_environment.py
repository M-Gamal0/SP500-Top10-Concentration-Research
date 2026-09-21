"""Factors: style environment."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import FactorsConfig


def compound_annualized_return(monthly_returns):
    monthly_returns = pd.Series(monthly_returns, dtype=float).dropna()
    n_months = len(monthly_returns)
    if n_months == 0:
        return np.nan
    growth = (1.0 + monthly_returns).prod()
    return growth ** (12.0 / n_months) - 1.0


def calculate_style_environment(factor_monthly_data, *, config: FactorsConfig):
    """Calculate style environment with explicit inputs; preserve legacy conventions."""
    RECENT_WINDOW_MONTHS = config.recent_window_months
    STYLE_LEADERSHIP_THRESHOLD = config.style_leadership_threshold
    TOLERANCE = config.tolerance
    if len(factor_monthly_data) <= RECENT_WINDOW_MONTHS:
        raise ValueError(
            f"The common factor sample must contain more than {RECENT_WINDOW_MONTHS} months so Earlier History is non-empty."
        )
    earlier_history = factor_monthly_data.iloc[:-RECENT_WINDOW_MONTHS].copy()
    recent_10y = factor_monthly_data.iloc[-RECENT_WINDOW_MONTHS:].copy()
    period_samples = {"Earlier History": earlier_history, "Recent 10Y": recent_10y}
    if len(recent_10y) != RECENT_WINDOW_MONTHS:
        raise ValueError(f"Recent period does not contain exactly {RECENT_WINDOW_MONTHS} months.")
    if earlier_history["month_end"].max() >= recent_10y["month_end"].min():
        raise ValueError("Earlier History and Recent 10Y overlap.")
    if len(earlier_history) + len(recent_10y) != len(factor_monthly_data):
        raise ValueError("Period split does not reconcile to the common factor sample.")
    style_environment_data = factor_monthly_data.copy()
    style_environment_data["style_state"] = np.select(
        [
            style_environment_data["style_spread"] < -STYLE_LEADERSHIP_THRESHOLD,
            style_environment_data["style_spread"] > STYLE_LEADERSHIP_THRESHOLD,
        ],
        ["Value-Led", "Growth-Led"],
        default="Neutral Style",
    )
    earlier_history = style_environment_data.iloc[:-RECENT_WINDOW_MONTHS].copy()
    recent_10y = style_environment_data.iloc[-RECENT_WINDOW_MONTHS:].copy()
    period_samples = {"Earlier History": earlier_history, "Recent 10Y": recent_10y}
    comparison_rows = []
    for period_name, sample in period_samples.items():
        n_months = len(sample)
        big_growth_cagr = compound_annualized_return(sample["big_growth_return"])
        big_value_cagr = compound_annualized_return(sample["big_value_return"])
        mc_cagr = compound_annualized_return(sample["mc_return"])
        sp500_cagr = compound_annualized_return(sample["sp500_return"])
        style_counts = sample["style_state"].value_counts()
        value_led_months = int(style_counts.get("Value-Led", 0))
        neutral_style_months = int(style_counts.get("Neutral Style", 0))
        growth_led_months = int(style_counts.get("Growth-Led", 0))
        comparison_rows.append(
            {
                "period": period_name,
                "start_date": sample["month_end"].iloc[0],
                "end_date": sample["month_end"].iloc[-1],
                "n_months": n_months,
                "big_growth_cagr": big_growth_cagr,
                "big_value_cagr": big_value_cagr,
                "growth_minus_value_cagr_gap": big_growth_cagr - big_value_cagr,
                "growth_minus_value_ann_mean": sample["style_spread"].mean() * 12.0,
                "hml_ann_mean": sample["hml"].mean() * 12.0,
                "mc_cagr": mc_cagr,
                "sp500_cagr": sp500_cagr,
                "cagr_gap": mc_cagr - sp500_cagr,
                "active_return_ann_mean": sample["active_return"].mean() * 12.0,
                "value_led_months": value_led_months,
                "neutral_style_months": neutral_style_months,
                "growth_led_months": growth_led_months,
                "pct_value_led_months": value_led_months / n_months * 100.0,
                "pct_neutral_style_months": neutral_style_months / n_months * 100.0,
                "pct_growth_led_months": growth_led_months / n_months * 100.0,
            }
        )
    style_environment_period_compare = pd.DataFrame(comparison_rows)
    style_environment_state_mix = style_environment_period_compare[
        [
            "period",
            "pct_value_led_months",
            "pct_neutral_style_months",
            "pct_growth_led_months",
        ]
    ].rename(
        columns={
            "period": "Period",
            "pct_value_led_months": "Value-Led",
            "pct_neutral_style_months": "Neutral Style",
            "pct_growth_led_months": "Growth-Led",
        }
    )
    state_count_check = style_environment_period_compare[
        ["value_led_months", "neutral_style_months", "growth_led_months"]
    ].sum(axis=1)
    if not np.array_equal(
        state_count_check.to_numpy(),
        style_environment_period_compare["n_months"].to_numpy(),
    ):
        raise ValueError("Style-state counts do not reconcile to period month counts.")
    state_pct_check = style_environment_state_mix[["Value-Led", "Neutral Style", "Growth-Led"]].sum(
        axis=1
    )
    if not np.allclose(state_pct_check, 100.0, atol=1e-10):
        raise ValueError("Style-state percentages do not sum to 100%.")
    active_identity_check = (
        style_environment_data["mc_return"]
        - style_environment_data["sp500_return"]
        - style_environment_data["active_return"]
    )
    if not np.allclose(active_identity_check, 0.0, atol=TOLERANCE):
        raise ValueError("Active-return identity does not reconcile.")
    for _, row in style_environment_period_compare.iterrows():
        pass
    for _, row in style_environment_period_compare.iterrows():
        pass
    return (style_environment_period_compare, style_environment_state_mix)
