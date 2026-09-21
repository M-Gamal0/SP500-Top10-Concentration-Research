"""Analytics: rolling returns."""

from __future__ import annotations

import pandas as pd

from ..config import AnalyticsConfig


def calculate_rolling_returns(growth_1000_wide, *, config: AnalyticsConfig):
    """Calculate rolling returns with explicit inputs; preserve legacy conventions."""
    ROLLING_MONTHS = config.rolling_months
    ROLLING_STRATEGIES = config.rolling_strategies
    SLIDE9_INDEX_ORDER = config.slide9_index_order
    monthly_wealth = (
        growth_1000_wide.set_index("date")[SLIDE9_INDEX_ORDER].resample("ME").last().dropna()
    )
    expected_months = pd.period_range(
        monthly_wealth.index.min().to_period("M"),
        monthly_wealth.index.max().to_period("M"),
        freq="M",
    )
    actual_months = monthly_wealth.index.to_period("M")
    if not actual_months.equals(expected_months):
        raise ValueError("Monthly wealth series contains missing months.")
    if monthly_wealth.isna().any().any():
        raise ValueError("Monthly wealth series contains missing values.")
    if len(monthly_wealth) <= ROLLING_MONTHS:
        raise ValueError("Insufficient history for a 60-month rolling window.")
    rolling_cagr = (monthly_wealth / monthly_wealth.shift(ROLLING_MONTHS)) ** (
        12 / ROLLING_MONTHS
    ) - 1
    rolling_60m_cagr_gap_monthly = pd.DataFrame(index=rolling_cagr.index)
    for strategy in ROLLING_STRATEGIES:
        rolling_60m_cagr_gap_monthly[strategy] = (
            rolling_cagr[strategy] - rolling_cagr["S&P 500"]
        ) * 100
    rolling_60m_cagr_gap_monthly = (
        rolling_60m_cagr_gap_monthly.dropna().reset_index().rename(columns={"date": "Date"})
    )
    if rolling_60m_cagr_gap_monthly.empty:
        raise ValueError("No complete rolling 60-month observations were produced.")
    if rolling_60m_cagr_gap_monthly[ROLLING_STRATEGIES].isna().any().any():
        raise ValueError("Missing values detected in rolling CAGR gaps.")
    if rolling_60m_cagr_gap_monthly["Date"].duplicated().any():
        raise ValueError("Duplicate monthly dates detected.")
    if not rolling_60m_cagr_gap_monthly["Date"].is_monotonic_increasing:
        raise ValueError("Rolling CAGR gap dates are not sorted.")
    return (rolling_60m_cagr_gap_monthly,)
