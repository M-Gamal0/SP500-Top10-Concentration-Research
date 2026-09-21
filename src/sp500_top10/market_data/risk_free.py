"""Market Data: risk free."""

from __future__ import annotations

import pandas as pd

from ..config import MarketDataConfig


def calculate_risk_free(backtest_calendar, risk_free_raw_input, *, config: MarketDataConfig):
    """Calculate risk free with explicit inputs; preserve legacy conventions."""
    RISK_FREE_SERIES = config.risk_free_series
    TRADING_DAYS_PER_YEAR = config.trading_days_per_year
    risk_free_raw = risk_free_raw_input
    risk_free_aligned = pd.merge_asof(
        backtest_calendar.sort_values("date"),
        risk_free_raw[["date", "value"]]
        .rename(columns={"date": "observation_date"})
        .sort_values("observation_date"),
        left_on="date",
        right_on="observation_date",
        direction="backward",
    )
    risk_free_aligned["series_id"] = RISK_FREE_SERIES
    risk_free_aligned["daily_risk_free_return"] = (
        risk_free_aligned["value"] / 100 / TRADING_DAYS_PER_YEAR
    )
    risk_free_daily = risk_free_aligned.rename(columns={"value": "annual_rate_percent"})[
        ["date", "series_id", "annual_rate_percent", "daily_risk_free_return"]
    ].copy()
    (risk_free_aligned["observation_date"] != risk_free_aligned["date"]).sum()
    return (risk_free_aligned, risk_free_daily)
