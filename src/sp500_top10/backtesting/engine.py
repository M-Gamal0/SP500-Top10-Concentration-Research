"""Backtesting: engine."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import BacktestingConfig
from .calendar import get_next_trading_date
from .rebalancing import review_buffered_20_weights


def make_rebalance_rows(
    date,
    rebalance_type: str,
    pre_rebalance_weights: pd.Series,
    target_weights: pd.Series,
) -> list[dict]:
    all_tickers = pre_rebalance_weights.index.union(target_weights.index)
    pre_weights = pre_rebalance_weights.reindex(all_tickers).fillna(0.0)
    aligned_targets = target_weights.reindex(all_tickers).fillna(0.0)
    return [
        {
            "date": date,
            "rebalance_type": rebalance_type,
            "ticker": ticker,
            "pre_rebalance_weight": float(pre_weights.loc[ticker]),
            "target_weight": float(aligned_targets.loc[ticker]),
        }
        for ticker in all_tickers
    ]


def run_backtest(
    backtest_dates,
    rebalance_weight_map,
    price_return_matrix,
    total_return_matrix,
    base_date,
    trading_dates,
    month_end_trading_dates,
    initial_index_value=1000.0,
    enable_monthly_buffered_20=False,
    *,
    config: BacktestingConfig,
):
    VALIDATION_TOLERANCE = config.validation_tolerance
    current_weights = None
    price_index_value = float(initial_index_value)
    total_index_value = float(initial_index_value)
    index_rows = []
    weight_rows = []
    monthly_review_rows = []
    rebalance_rows = []
    monthly_reset_map = {}
    first_rebalance_date = min(rebalance_weight_map)
    first_weights = rebalance_weight_map[first_rebalance_date].copy()
    index_rows.append(
        {
            "date": base_date,
            "is_rebalance_date": False,
            "rebalance_type": "initial_base",
            "price_return": 0.0,
            "total_return": 0.0,
            "price_index_value": price_index_value,
            "total_index_value": total_index_value,
        }
    )
    for ticker, weight in first_weights.items():
        weight_rows.append(
            {
                "date": base_date,
                "ticker": ticker,
                "is_rebalance_date": False,
                "rebalance_type": "initial_base",
                "beginning_weight": float(weight),
                "ending_weight": float(weight),
                "price_return": 0.0,
                "total_return": 0.0,
                "price_return_contribution": 0.0,
                "total_return_contribution": 0.0,
            }
        )
    for date in backtest_dates:
        is_quarterly_rebalance = date in rebalance_weight_map
        is_monthly_reset = date in monthly_reset_map
        if is_quarterly_rebalance:
            target_weights = rebalance_weight_map[date].copy()
            if current_weights is not None:
                rebalance_rows.extend(
                    make_rebalance_rows(
                        date=date,
                        rebalance_type="quarterly",
                        pre_rebalance_weights=current_weights,
                        target_weights=target_weights,
                    )
                )
            current_weights = target_weights.copy()
            rebalance_type = "quarterly"
        elif is_monthly_reset:
            target_weights = monthly_reset_map[date].copy()
            rebalance_rows.extend(
                make_rebalance_rows(
                    date=date,
                    rebalance_type="monthly_20",
                    pre_rebalance_weights=current_weights,
                    target_weights=target_weights,
                )
            )
            current_weights = target_weights.copy()
            rebalance_type = "monthly_20"
        else:
            rebalance_type = None
        if current_weights is None:
            raise ValueError(f"No active portfolio weights on {date.date()}.")
        beginning_weights = current_weights.copy()
        daily_price_returns = price_return_matrix.loc[date].reindex(beginning_weights.index)
        daily_total_returns = total_return_matrix.loc[date].reindex(beginning_weights.index)
        if daily_price_returns.isna().any() or daily_total_returns.isna().any():
            raise ValueError(f"Missing required return on {date.date()}.")
        price_contributions = beginning_weights * daily_price_returns
        total_contributions = beginning_weights * daily_total_returns
        price_index_return = float(price_contributions.sum())
        total_index_return = float(total_contributions.sum())
        price_index_value *= 1 + price_index_return
        total_index_value *= 1 + total_index_return
        ending_weights = beginning_weights * (1 + daily_price_returns) / (1 + price_index_return)
        if not np.isclose(ending_weights.sum(), 1.0, atol=VALIDATION_TOLERANCE):
            raise ValueError(f"Ending weights do not sum to 100% on {date.date()}.")
        current_weights = ending_weights.copy()
        is_rebalance_date = is_quarterly_rebalance or is_monthly_reset
        index_rows.append(
            {
                "date": date,
                "is_rebalance_date": is_rebalance_date,
                "rebalance_type": rebalance_type,
                "price_return": price_index_return,
                "total_return": total_index_return,
                "price_index_value": price_index_value,
                "total_index_value": total_index_value,
            }
        )
        for ticker in beginning_weights.index:
            weight_rows.append(
                {
                    "date": date,
                    "ticker": ticker,
                    "is_rebalance_date": is_rebalance_date,
                    "rebalance_type": rebalance_type,
                    "beginning_weight": float(beginning_weights.loc[ticker]),
                    "ending_weight": float(ending_weights.loc[ticker]),
                    "price_return": float(daily_price_returns.loc[ticker]),
                    "total_return": float(daily_total_returns.loc[ticker]),
                    "price_return_contribution": float(price_contributions.loc[ticker]),
                    "total_return_contribution": float(total_contributions.loc[ticker]),
                }
            )
        if enable_monthly_buffered_20 and date in month_end_trading_dates:
            breach_detected, reset_weights, dominant_ticker = review_buffered_20_weights(
                ending_weights, config=config
            )
            if not breach_detected:
                continue
            next_trading_date = get_next_trading_date(date, trading_dates)
            if next_trading_date is None:
                monthly_review_rows.append(
                    {
                        "review_date": date,
                        "dominant_ticker": dominant_ticker,
                        "breach_detected": True,
                        "scheduled_rebalance_date": pd.NaT,
                        "action": "no_next_trading_date",
                    }
                )
            elif next_trading_date in rebalance_weight_map:
                monthly_review_rows.append(
                    {
                        "review_date": date,
                        "dominant_ticker": dominant_ticker,
                        "breach_detected": True,
                        "scheduled_rebalance_date": next_trading_date,
                        "action": "superseded_by_quarterly",
                    }
                )
            else:
                monthly_reset_map[next_trading_date] = reset_weights.copy()
                monthly_review_rows.append(
                    {
                        "review_date": date,
                        "dominant_ticker": dominant_ticker,
                        "breach_detected": True,
                        "scheduled_rebalance_date": next_trading_date,
                        "action": "monthly_reset_scheduled",
                    }
                )
    daily_index = pd.DataFrame(index_rows)
    daily_weights = pd.DataFrame(weight_rows)
    monthly_reviews = pd.DataFrame(
        monthly_review_rows,
        columns=[
            "review_date",
            "dominant_ticker",
            "breach_detected",
            "scheduled_rebalance_date",
            "action",
        ],
    )
    rebalance_events = pd.DataFrame(
        rebalance_rows,
        columns=[
            "date",
            "rebalance_type",
            "ticker",
            "pre_rebalance_weight",
            "target_weight",
        ],
    )
    return (daily_index, daily_weights, monthly_reviews, rebalance_events)
