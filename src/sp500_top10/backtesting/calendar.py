"""Backtesting: calendar."""

from __future__ import annotations

from math import ceil

import pandas as pd

from ..config import BacktestingConfig


def get_next_trading_date(date, trading_dates: pd.DatetimeIndex):
    date = pd.Timestamp(date).normalize()
    future_dates = trading_dates[trading_dates > date]
    if len(future_dates) == 0:
        return None
    return pd.Timestamp(future_dates[0]).normalize()


def get_previous_trading_date(date, trading_dates: pd.DatetimeIndex):
    date = pd.Timestamp(date).normalize()
    previous_dates = trading_dates[trading_dates < date]
    if len(previous_dates) == 0:
        return None
    return pd.Timestamp(previous_dates[-1]).normalize()


def get_month_end_trading_dates(trading_dates: pd.DatetimeIndex) -> set[pd.Timestamp]:
    calendar = pd.DataFrame({"date": trading_dates})
    calendar["month"] = calendar["date"].dt.to_period("M")
    return {pd.Timestamp(date).normalize() for date in calendar.groupby("month")["date"].max()}


def select_calendar_representatives(representative_tickers_input, *, config: BacktestingConfig):
    """Calculate calendar with explicit inputs; preserve legacy conventions."""
    CALENDAR_COVERAGE_THRESHOLD = config.calendar_coverage_threshold
    representative_tickers = representative_tickers_input
    representative_list = representative_tickers["ticker"].tolist()
    minimum_calendar_coverage = ceil(len(representative_list) * CALENDAR_COVERAGE_THRESHOLD)
    return (minimum_calendar_coverage, representative_list)


def build_backtest_calendar(
    calendar_check_input,
    minimum_calendar_coverage,
    quarterly_weights,
    *,
    config: BacktestingConfig,
):
    """Calculate calendar with explicit inputs; preserve legacy conventions."""
    BACKTEST_END_DATE = config.backtest_end_date
    calendar_check = calendar_check_input
    trading_dates = pd.DatetimeIndex(
        pd.to_datetime(
            calendar_check.loc[calendar_check["ticker_count"] >= minimum_calendar_coverage, "date"]
        ).dt.normalize()
    )
    eligible_end_dates = trading_dates[trading_dates <= BACKTEST_END_DATE]
    if len(eligible_end_dates) == 0:
        raise ValueError("No trading date exists on or before BACKTEST_END_DATE.")
    final_date = pd.Timestamp(eligible_end_dates[-1]).normalize()
    selection_dates = quarterly_weights["selection_date"].drop_duplicates().sort_values()
    effective_date_map = {
        selection_date: get_next_trading_date(selection_date, trading_dates)
        for selection_date in selection_dates
    }
    quarterly_weights["effective_rebalance_date"] = quarterly_weights["selection_date"].map(
        effective_date_map
    )
    active_quarterly_weights = (
        quarterly_weights.loc[
            quarterly_weights["effective_rebalance_date"].notna()
            & (quarterly_weights["effective_rebalance_date"] <= final_date)
        ]
        .copy()
        .reset_index(drop=True)
    )
    if active_quarterly_weights.empty:
        raise ValueError("No quarterly portfolios become effective inside the backtest window.")
    first_rebalance_date = pd.Timestamp(
        active_quarterly_weights["effective_rebalance_date"].min()
    ).normalize()
    base_date = get_previous_trading_date(first_rebalance_date, trading_dates)
    if base_date is None:
        raise ValueError("No trading date exists before the first effective rebalance date.")
    backtest_dates = trading_dates[
        (trading_dates >= first_rebalance_date) & (trading_dates <= final_date)
    ]
    month_end_trading_dates = get_month_end_trading_dates(
        trading_dates[trading_dates <= final_date]
    )
    return (
        active_quarterly_weights,
        backtest_dates,
        base_date,
        final_date,
        month_end_trading_dates,
        trading_dates,
    )
