"""Backtesting: assembly."""

from __future__ import annotations

import pandas as pd

from ..config import BacktestingConfig
from .engine import run_backtest
from .rebalancing import build_rebalance_weight_map


def calculate_assembly(
    active_quarterly_weights,
    backtest_dates,
    base_date,
    month_end_trading_dates,
    price_return_matrix,
    total_return_matrix,
    trading_dates,
    *,
    config: BacktestingConfig,
):
    """Calculate assembly with explicit inputs; preserve legacy conventions."""
    CORE_TOP_N = config.core_top_n
    INITIAL_INDEX_VALUE = config.initial_index_value
    PORTFOLIO_SPECS = config.portfolio_specs
    strategy_inputs = {}
    strategy_results = {}
    for top_n, method in PORTFOLIO_SPECS:
        strategy_weights, strategy_rebalance_map = build_rebalance_weight_map(
            active_quarterly_weights,
            top_n=top_n,
            weighting_method=method,
            config=config,
        )
        strategy_key = (top_n, method)
        strategy_inputs[strategy_key] = {
            "weights": strategy_weights,
            "rebalance_weight_map": strategy_rebalance_map,
        }
        (
            strategy_daily_index,
            strategy_daily_weights,
            strategy_monthly_reviews,
            strategy_rebalance_events,
        ) = run_backtest(
            backtest_dates=backtest_dates,
            rebalance_weight_map=strategy_rebalance_map,
            price_return_matrix=price_return_matrix,
            total_return_matrix=total_return_matrix,
            base_date=base_date,
            trading_dates=trading_dates,
            month_end_trading_dates=month_end_trading_dates,
            initial_index_value=INITIAL_INDEX_VALUE,
            enable_monthly_buffered_20=top_n == CORE_TOP_N and method == "buffered_20",
            config=config,
        )
        for output in [
            strategy_daily_index,
            strategy_daily_weights,
            strategy_monthly_reviews,
            strategy_rebalance_events,
        ]:
            output["top_n"] = top_n
            output["weighting_method"] = method
        strategy_results[strategy_key] = {
            "daily_index": strategy_daily_index,
            "daily_weights": strategy_daily_weights,
            "monthly_reviews": strategy_monthly_reviews,
            "rebalance_events": strategy_rebalance_events,
        }
    all_daily_index = pd.concat(
        [result["daily_index"] for result in strategy_results.values()],
        ignore_index=True,
    )
    all_daily_weights = pd.concat(
        [result["daily_weights"] for result in strategy_results.values()],
        ignore_index=True,
    )
    all_rebalance_events = pd.concat(
        [result["rebalance_events"] for result in strategy_results.values()],
        ignore_index=True,
    )
    monthly_review_frames = [
        result["monthly_reviews"]
        for result in strategy_results.values()
        if not result["monthly_reviews"].empty
    ]
    if monthly_review_frames:
        all_monthly_reviews = pd.concat(monthly_review_frames, ignore_index=True)
    else:
        all_monthly_reviews = pd.DataFrame(
            columns=[
                "review_date",
                "top_n",
                "weighting_method",
                "dominant_ticker",
                "breach_detected",
                "scheduled_rebalance_date",
                "action",
            ]
        )
    all_rebalance_events["weight_change"] = (
        all_rebalance_events["target_weight"] - all_rebalance_events["pre_rebalance_weight"]
    )
    all_turnover = all_rebalance_events.groupby(
        ["top_n", "weighting_method", "date", "rebalance_type"], as_index=False
    ).agg(absolute_weight_change=("weight_change", lambda x: x.abs().sum()))
    all_turnover["turnover"] = 0.5 * all_turnover["absolute_weight_change"]
    all_daily_index = (
        all_daily_index[
            [
                "date",
                "top_n",
                "weighting_method",
                "is_rebalance_date",
                "rebalance_type",
                "price_return",
                "total_return",
                "price_index_value",
                "total_index_value",
            ]
        ]
        .sort_values(["top_n", "weighting_method", "date"])
        .reset_index(drop=True)
    )
    all_daily_weights = (
        all_daily_weights[
            [
                "date",
                "top_n",
                "weighting_method",
                "ticker",
                "is_rebalance_date",
                "rebalance_type",
                "beginning_weight",
                "ending_weight",
                "price_return",
                "total_return",
                "price_return_contribution",
                "total_return_contribution",
            ]
        ]
        .sort_values(["top_n", "weighting_method", "date", "ticker"])
        .reset_index(drop=True)
    )
    all_rebalance_events = (
        all_rebalance_events[
            [
                "date",
                "top_n",
                "weighting_method",
                "rebalance_type",
                "ticker",
                "pre_rebalance_weight",
                "target_weight",
                "weight_change",
            ]
        ]
        .sort_values(["top_n", "weighting_method", "date", "ticker"])
        .reset_index(drop=True)
    )
    all_turnover = (
        all_turnover[
            [
                "date",
                "top_n",
                "weighting_method",
                "rebalance_type",
                "absolute_weight_change",
                "turnover",
            ]
        ]
        .sort_values(["top_n", "weighting_method", "date"])
        .reset_index(drop=True)
    )
    all_monthly_reviews = (
        all_monthly_reviews[
            [
                "review_date",
                "top_n",
                "weighting_method",
                "dominant_ticker",
                "breach_detected",
                "scheduled_rebalance_date",
                "action",
            ]
        ]
        .sort_values(["top_n", "weighting_method", "review_date"])
        .reset_index(drop=True)
    )
    pd.DataFrame(
        {
            "output": [
                "daily_index",
                "daily_weights",
                "rebalance_events",
                "turnover",
                "monthly_reviews",
            ],
            "rows": [
                len(all_daily_index),
                len(all_daily_weights),
                len(all_rebalance_events),
                len(all_turnover),
                len(all_monthly_reviews),
            ],
        }
    )
    return (
        all_daily_index,
        all_daily_weights,
        all_monthly_reviews,
        all_rebalance_events,
        all_turnover,
    )
