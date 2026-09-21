"""Backtesting: prices."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import BacktestingConfig
from .calendar import get_previous_trading_date


def build_constituent_schedule(active_quarterly_weights, *, config: BacktestingConfig):
    """Calculate prices with explicit inputs; preserve legacy conventions."""
    MAX_REQUIRED_TOP_N = config.max_required_top_n
    constituent_schedule = (
        active_quarterly_weights[
            ["selection_date", "effective_rebalance_date", "rank", "ticker", "name"]
        ]
        .drop_duplicates(["selection_date", "ticker"])
        .sort_values(["effective_rebalance_date", "rank"])
        .reset_index(drop=True)
    )
    constituent_count_check = constituent_schedule.groupby("selection_date")["ticker"].nunique()
    if not constituent_count_check.eq(MAX_REQUIRED_TOP_N).all():
        raise ValueError(
            f"The combined constituent schedule does not contain exactly {MAX_REQUIRED_TOP_N} names per quarter."
        )
    strategy_tickers = sorted(constituent_schedule["ticker"].unique().tolist())
    return (constituent_schedule, strategy_tickers)


def prepare_return_matrices(
    constituent_schedule,
    final_date,
    price_data_input,
    trading_dates,
    *,
    config: BacktestingConfig,
):
    """Calculate prices with explicit inputs; preserve legacy conventions."""
    price_data = price_data_input
    price_data["date"] = pd.to_datetime(price_data["date"]).dt.normalize()
    rebalance_dates = (
        constituent_schedule[["effective_rebalance_date"]]
        .drop_duplicates()
        .sort_values("effective_rebalance_date")
        .reset_index(drop=True)
    )
    rebalance_dates["next_effective_rebalance_date"] = rebalance_dates[
        "effective_rebalance_date"
    ].shift(-1)
    holding_periods = constituent_schedule.merge(
        rebalance_dates,
        on="effective_rebalance_date",
        how="left",
        validate="many_to_one",
    )
    holding_periods["holding_end_date"] = holding_periods["next_effective_rebalance_date"].apply(
        lambda date: (
            get_previous_trading_date(date, trading_dates) if pd.notna(date) else final_date
        )
    )
    continuity_rows = []
    for row in holding_periods.itertuples(index=False):
        price_start_date = get_previous_trading_date(row.effective_rebalance_date, trading_dates)
        expected_dates = trading_dates[
            (trading_dates >= price_start_date) & (trading_dates <= row.holding_end_date)
        ]
        ticker_prices = price_data.loc[
            (price_data["ticker"] == row.ticker)
            & (price_data["date"] >= price_start_date)
            & (price_data["date"] <= row.holding_end_date)
        ]
        valid_prices = ticker_prices.loc[
            ticker_prices["close"].notna() & ticker_prices["closeadj"].notna()
        ]
        continuity_rows.append(
            {
                "selection_date": row.selection_date,
                "ticker": row.ticker,
                "expected_dates": len(expected_dates),
                "observed_dates": ticker_prices["date"].nunique(),
                "valid_price_dates": valid_prices["date"].nunique(),
            }
        )
    price_continuity = pd.DataFrame(continuity_rows)
    price_continuity["complete"] = (
        price_continuity["expected_dates"] == price_continuity["observed_dates"]
    ) & (price_continuity["expected_dates"] == price_continuity["valid_price_dates"])
    if not price_continuity["complete"].all():
        failed_continuity = price_continuity.loc[~price_continuity["complete"]]
        raise ValueError(
            "Incomplete price history detected for required holding periods:\n"
            + failed_continuity.head(20).to_string(index=False)
        )
    prices = price_data.sort_values(["ticker", "date"]).reset_index(drop=True).copy()
    prices["price_return"] = prices.groupby("ticker")["close"].pct_change(fill_method=None)
    prices["total_return"] = prices.groupby("ticker")["closeadj"].pct_change(fill_method=None)
    prices["price_return"] = prices["price_return"].replace([np.inf, -np.inf], np.nan)
    prices["total_return"] = prices["total_return"].replace([np.inf, -np.inf], np.nan)
    price_return_matrix = prices.pivot(
        index="date", columns="ticker", values="price_return"
    ).sort_index()
    total_return_matrix = prices.pivot(
        index="date", columns="ticker", values="total_return"
    ).sort_index()
    return (price_return_matrix, total_return_matrix)
