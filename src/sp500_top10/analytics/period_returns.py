"""Analytics: period returns."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def calculate_period_returns(growth_1000_wide, *, config: AnalyticsConfig):
    """Calculate period returns with explicit inputs; preserve legacy conventions."""
    PERIOD_MONTHS = config.period_months
    SLIDE9_INDEX_ORDER = config.slide9_index_order
    monthly_levels = (
        growth_1000_wide.set_index("date")[SLIDE9_INDEX_ORDER].resample("ME").last().dropna()
    )
    expected_months = pd.period_range(
        monthly_levels.index.min().to_period("M"),
        monthly_levels.index.max().to_period("M"),
        freq="M",
    )
    actual_months = monthly_levels.index.to_period("M")
    if not actual_months.equals(expected_months):
        raise ValueError("Monthly series contains missing months.")
    period_rows = []
    for period_label, months in PERIOD_MONTHS.items():
        if months is None:
            start_values = monthly_levels.iloc[0]
            end_values = monthly_levels.iloc[-1]
            months_in_period = len(monthly_levels) - 1
        else:
            if len(monthly_levels) <= months:
                raise ValueError(f"Insufficient history for {period_label}.")
            start_values = monthly_levels.iloc[-(months + 1)]
            end_values = monthly_levels.iloc[-1]
            months_in_period = months
        for index_name in SLIDE9_INDEX_ORDER:
            total_return = end_values[index_name] / start_values[index_name] - 1
            cagr = (1 + total_return) ** (12 / months_in_period) - 1
            period_rows.append(
                {
                    "period": period_label,
                    "index": index_name,
                    "total_return": total_return,
                    "cagr": cagr,
                }
            )
    period_return_summary = pd.DataFrame(period_rows)
    benchmark_cagr_by_period = period_return_summary.loc[
        period_return_summary["index"].eq("S&P 500"), ["period", "cagr"]
    ].rename(columns={"cagr": "benchmark_cagr"})
    period_return_summary = period_return_summary.merge(
        benchmark_cagr_by_period, on="period", how="left", validate="many_to_one"
    )
    period_return_summary["cagr_gap_vs_sp500_pp"] = (
        period_return_summary["cagr"] - period_return_summary["benchmark_cagr"]
    ) * 100
    period_return_summary.loc[
        period_return_summary["index"].eq("S&P 500"), "cagr_gap_vs_sp500_pp"
    ] = np.nan
    period_return_summary = period_return_summary[
        ["period", "index", "total_return", "cagr", "cagr_gap_vs_sp500_pp"]
    ]
    period_return_summary_display = period_return_summary.copy()
    period_return_summary_display["Total Return"] = period_return_summary_display[
        "total_return"
    ].map(lambda x: f"{x:.1%}")
    period_return_summary_display["CAGR"] = period_return_summary_display["cagr"].map(
        lambda x: f"{x:.1%}"
    )
    period_return_summary_display["CAGR Gap vs. S&P 500"] = period_return_summary_display[
        "cagr_gap_vs_sp500_pp"
    ].map(lambda x: "—" if pd.isna(x) else f"{x:+.1f} pp")
    period_return_summary_display = period_return_summary_display[
        ["period", "index", "Total Return", "CAGR", "CAGR Gap vs. S&P 500"]
    ].rename(columns={"period": "Period", "index": "Index"})
    return (period_return_summary,)
