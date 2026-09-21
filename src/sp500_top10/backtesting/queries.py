"""Backtesting: queries."""

from __future__ import annotations

from ..config import BacktestingConfig
from ..data.sql_resources import read_sql


def load_inputs_quarterly_weights(repository, *, config: BacktestingConfig):
    """Load inputs with explicit inputs; preserve legacy conventions."""
    INPUT_TABLE = config.input_table
    return repository.query(
        f"\n    SELECT\n        selection_date,\n        top_n,\n        weighting_method,\n        rank,\n        ticker,\n        name,\n        target_weight\n    FROM {INPUT_TABLE}\n    ORDER BY\n        top_n,\n        weighting_method,\n        selection_date,\n        rank\n    "
    )


def load_calendar_representative_tickers(repository, *, config: BacktestingConfig):
    """Load calendar with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("backtesting_load_calendar_representative_tickers.sql"))


def load_calendar_calendar_check(repository, representative_list, *, config: BacktestingConfig):
    """Load calendar with explicit inputs; preserve legacy conventions."""
    return repository.query(
        read_sql("backtesting_load_calendar_calendar_check.sql"), [representative_list]
    )


def load_prices_price_data(
    repository, base_date, final_date, strategy_tickers, *, config: BacktestingConfig
):
    """Load prices with explicit inputs; preserve legacy conventions."""
    return repository.query(
        read_sql("backtesting_load_prices_price_data.sql"),
        [strategy_tickers, base_date, final_date],
    )
