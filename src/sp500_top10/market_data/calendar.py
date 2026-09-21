"""Market Data: calendar."""

from __future__ import annotations

import pandas as pd

from ..config import MarketDataConfig


def calculate_calendar(backtest_calendar_input, *, config: MarketDataConfig):
    """Calculate calendar with explicit inputs; preserve legacy conventions."""
    backtest_calendar = backtest_calendar_input
    backtest_calendar["date"] = pd.to_datetime(backtest_calendar["date"]).astype("datetime64[ns]")
    return (backtest_calendar,)
