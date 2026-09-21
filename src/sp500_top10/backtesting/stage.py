"""Orchestrate backtesting without notebook execution."""

from ..config import BacktestingConfig
from ..data.results import StageResult
from .assembly import calculate_assembly
from .calendar import build_backtest_calendar, select_calendar_representatives
from .inputs import calculate_inputs
from .prices import build_constituent_schedule, prepare_return_matrices
from .queries import (
    load_calendar_calendar_check,
    load_calendar_representative_tickers,
    load_inputs_quarterly_weights,
    load_prices_price_data,
)
from .validation import calculate_validation


def run(repository, config: BacktestingConfig) -> StageResult:
    quarterly_weights_input = load_inputs_quarterly_weights(repository, config=config)
    (quarterly_weights,) = calculate_inputs(quarterly_weights_input, config=config)
    representative_tickers_input = load_calendar_representative_tickers(repository, config=config)
    minimum_calendar_coverage, representative_list = select_calendar_representatives(
        representative_tickers_input, config=config
    )
    calendar_check_input = load_calendar_calendar_check(
        repository, representative_list, config=config
    )
    (
        active_quarterly_weights,
        backtest_dates,
        base_date,
        final_date,
        month_end_trading_dates,
        trading_dates,
    ) = build_backtest_calendar(
        calendar_check_input,
        minimum_calendar_coverage,
        quarterly_weights,
        config=config,
    )
    constituent_schedule, strategy_tickers = build_constituent_schedule(
        active_quarterly_weights, config=config
    )
    price_data_input = load_prices_price_data(
        repository, base_date, final_date, strategy_tickers, config=config
    )
    price_return_matrix, total_return_matrix = prepare_return_matrices(
        constituent_schedule, final_date, price_data_input, trading_dates, config=config
    )
    (
        all_daily_index,
        all_daily_weights,
        all_monthly_reviews,
        all_rebalance_events,
        all_turnover,
    ) = calculate_assembly(
        active_quarterly_weights,
        backtest_dates,
        base_date,
        month_end_trading_dates,
        price_return_matrix,
        total_return_matrix,
        trading_dates,
        config=config,
    )
    calculate_validation(
        active_quarterly_weights,
        all_daily_index,
        all_daily_weights,
        all_monthly_reviews,
        all_rebalance_events,
        all_turnover,
        base_date,
        final_date,
        month_end_trading_dates,
        config=config,
    )
    return StageResult(
        tables={
            "backtest_daily_index": all_daily_index,
            "backtest_daily_weights": all_daily_weights,
            "backtest_rebalance_events": all_rebalance_events,
            "backtest_turnover": all_turnover,
            "backtest_monthly_reviews": all_monthly_reviews,
        },
        csvs={},
    )
