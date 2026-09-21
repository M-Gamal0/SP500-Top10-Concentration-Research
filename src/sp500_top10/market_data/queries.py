"""Market Data: queries."""

from __future__ import annotations

from ..config import MarketDataConfig
from ..data.sql_resources import read_sql


def load_calendar_backtest_calendar(repository, *, config: MarketDataConfig):
    """Load calendar with explicit inputs; preserve legacy conventions."""
    BACKTEST_END_DATE = config.backtest_end_date
    BACKTEST_START_DATE = config.backtest_start_date
    return repository.query(
        read_sql("market_data_load_calendar_backtest_calendar.sql"),
        [BACKTEST_START_DATE, BACKTEST_END_DATE],
    )
