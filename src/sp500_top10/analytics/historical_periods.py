"""Analytics: historical periods."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def calculate_historical_periods(growth_1000_wide, *, config: AnalyticsConfig):
    """Calculate historical periods with explicit inputs; preserve legacy conventions."""
    PERIOD_ANALYSIS_INDEX_ORDER = config.period_analysis_index_order
    period_definitions = pd.DataFrame(
        config.historical_periods,
        columns=["period_number", "phase", "start_date", "end_date", "period_name"],
    )
    period_definitions["start_date"] = pd.to_datetime(period_definitions["start_date"])
    period_definitions["end_date"] = pd.to_datetime(period_definitions["end_date"])
    period_wealth = (
        growth_1000_wide[["date", "S&P 500", "MC", "EW", "MC (UCITS)"]]
        .sort_values("date")
        .set_index("date")
    )
    required_dates = set(period_definitions["start_date"]).union(
        set(period_definitions["end_date"])
    )
    available_dates = set(period_wealth.index)
    missing_dates = sorted(required_dates - available_dates)
    if missing_dates:
        raise ValueError(
            f"Period analysis contains dates not present in the daily index history: {missing_dates}"
        )
    if (period_definitions["end_date"] <= period_definitions["start_date"]).any():
        raise ValueError("Every period end date must be after its start date.")
    period_rows = []
    for period in period_definitions.itertuples(index=False):
        start_date = period.start_date
        end_date = period.end_date
        calendar_days = (end_date - start_date).days
        start_values = period_wealth.loc[start_date]
        end_values = period_wealth.loc[end_date]
        benchmark_total_return = end_values["S&P 500"] / start_values["S&P 500"] - 1
        benchmark_annualized_return = (end_values["S&P 500"] / start_values["S&P 500"]) ** (
            365.25 / calendar_days
        ) - 1
        for index_name in PERIOD_ANALYSIS_INDEX_ORDER:
            total_return = end_values[index_name] / start_values[index_name] - 1
            annualized_return = (end_values[index_name] / start_values[index_name]) ** (
                365.25 / calendar_days
            ) - 1
            period_rows.append(
                {
                    "period_number": period.period_number,
                    "phase": period.phase,
                    "period_name": period.period_name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "calendar_days": calendar_days,
                    "index": index_name,
                    "total_return": total_return,
                    "annualized_return": annualized_return,
                    "total_return_gap_vs_sp500_pp": (total_return - benchmark_total_return) * 100,
                    "annualized_return_gap_vs_sp500_pp": (
                        annualized_return - benchmark_annualized_return
                    )
                    * 100,
                }
            )
    period_analysis = pd.DataFrame(period_rows)
    benchmark_mask = period_analysis["index"].eq("S&P 500")
    period_analysis.loc[
        benchmark_mask, ["total_return_gap_vs_sp500_pp", "annualized_return_gap_vs_sp500_pp"]
    ] = np.nan
    period_analysis["index"] = pd.Categorical(
        period_analysis["index"], categories=PERIOD_ANALYSIS_INDEX_ORDER, ordered=True
    )
    period_analysis = period_analysis.sort_values(["period_number", "index"]).reset_index(drop=True)
    period_analysis["index"] = period_analysis["index"].astype(str)
    expected_rows = len(period_definitions) * len(PERIOD_ANALYSIS_INDEX_ORDER)
    if len(period_analysis) != expected_rows:
        raise ValueError(f"Expected {expected_rows} rows, found {len(period_analysis)}.")
    period_counts = period_analysis.groupby("period_number")["index"].nunique()
    if not period_counts.eq(4).all():
        raise ValueError("Each period must contain exactly four indices.")
    if period_analysis[["total_return", "annualized_return"]].isna().any().any():
        raise ValueError("Missing return values detected.")
    return (period_analysis,)
