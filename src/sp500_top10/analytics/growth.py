"""Analytics: growth."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def normalize_strategy_levels(strategy_levels_input, *, config: AnalyticsConfig):
    """Calculate growth with explicit inputs; preserve legacy conventions."""
    strategy_levels = strategy_levels_input
    strategy_levels["date"] = pd.to_datetime(strategy_levels["date"])
    return (strategy_levels,)


def calculate_growth(benchmark_levels_input, strategy_levels, *, config: AnalyticsConfig):
    """Calculate growth with explicit inputs; preserve legacy conventions."""
    SLIDE9_INDEX_ORDER = config.slide9_index_order
    SLIDE9_METHOD_LABELS = config.slide9_method_labels
    TOLERANCE = config.tolerance
    benchmark_levels = benchmark_levels_input
    benchmark_levels["date"] = pd.to_datetime(benchmark_levels["date"])
    if strategy_levels.duplicated(["date", "weighting_method"]).any():
        raise ValueError("Duplicate strategy index observations detected.")
    if benchmark_levels["date"].duplicated().any():
        raise ValueError("Duplicate S&P 500 TR observations detected.")
    actual_methods = set(strategy_levels["weighting_method"].unique())
    expected_methods = set(SLIDE9_METHOD_LABELS)
    if actual_methods != expected_methods:
        raise ValueError(
            f"Unexpected weighting methods. Expected {sorted(expected_methods)}, found {sorted(actual_methods)}."
        )
    strategy_dates = strategy_levels.groupby("weighting_method")["date"].apply(set)
    benchmark_dates = set(benchmark_levels["date"])
    for method, dates in strategy_dates.items():
        if dates != benchmark_dates:
            raise ValueError(f"{method}: trading calendar does not match the S&P 500 TR benchmark.")
    strategy_wide = strategy_levels.pivot(
        index="date", columns="weighting_method", values="total_index_value"
    ).sort_index()
    strategy_wide = strategy_wide.rename(columns=SLIDE9_METHOD_LABELS)
    for index_name in SLIDE9_METHOD_LABELS.values():
        strategy_wide[index_name] = (
            strategy_wide[index_name] / strategy_wide[index_name].iloc[0] * 1000
        )
    benchmark_wealth = benchmark_levels.set_index("date")["close"].sort_index()
    benchmark_wealth = benchmark_wealth / benchmark_wealth.iloc[0] * 1000
    growth_1000_wide = strategy_wide.copy()
    growth_1000_wide.insert(0, "S&P 500", benchmark_wealth)
    growth_1000_wide = growth_1000_wide[SLIDE9_INDEX_ORDER].reset_index()
    growth_1000_full_period = growth_1000_wide.rename(columns={"date": "Date"}).copy()
    growth_1000_full_period = growth_1000_full_period[["Date", "S&P 500", "MC", "EW", "MC (UCITS)"]]
    start_date = growth_1000_wide["date"].iloc[0]
    end_date = growth_1000_wide["date"].iloc[-1]
    years = (end_date - start_date).days / 365.25
    summary_rows = []
    for index_name in SLIDE9_INDEX_ORDER:
        ending_value = float(growth_1000_wide[index_name].iloc[-1])
        cagr = (ending_value / 1000) ** (1 / years) - 1
        summary_rows.append({"index": index_name, "ending_value": ending_value, "cagr": cagr})
    growth_1000_summary = pd.DataFrame(summary_rows)
    benchmark_cagr = growth_1000_summary.loc[
        growth_1000_summary["index"].eq("S&P 500"), "cagr"
    ].iloc[0]
    growth_1000_summary["cagr_gap_vs_sp500_pp"] = (
        growth_1000_summary["cagr"] - benchmark_cagr
    ) * 100
    growth_1000_summary.loc[growth_1000_summary["index"].eq("S&P 500"), "cagr_gap_vs_sp500_pp"] = (
        np.nan
    )
    if growth_1000_wide[SLIDE9_INDEX_ORDER].isna().any().any():
        raise ValueError("Missing values in Slide 9 wealth series.")
    if not (growth_1000_wide[SLIDE9_INDEX_ORDER] > 0).all().all():
        raise ValueError("Growth series contains non-positive values.")
    if not np.allclose(
        growth_1000_wide[SLIDE9_INDEX_ORDER].iloc[0], 1000.0, atol=TOLERANCE, rtol=0
    ):
        raise ValueError("Not all Slide 9 series begin at $1,000.")
    if years <= 0:
        raise ValueError("Invalid Slide 9 analysis period.")
    growth_1000_summary_display = growth_1000_summary.copy()
    growth_1000_summary_display["Ending Value"] = growth_1000_summary_display["ending_value"].map(
        lambda x: f"${x:,.0f}"
    )
    growth_1000_summary_display["CAGR"] = growth_1000_summary_display["cagr"].map(
        lambda x: f"{x:.1%}"
    )
    growth_1000_summary_display["CAGR Gap vs. S&P 500"] = growth_1000_summary_display[
        "cagr_gap_vs_sp500_pp"
    ].map(lambda x: "—" if pd.isna(x) else f"{x:+.1f} pp")
    growth_1000_summary_display = growth_1000_summary_display[
        ["index", "Ending Value", "CAGR", "CAGR Gap vs. S&P 500"]
    ].rename(columns={"index": "Index"})
    return (growth_1000_full_period, growth_1000_summary, growth_1000_wide)
