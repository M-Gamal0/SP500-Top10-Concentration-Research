"""Analytics: regime performance."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def calculate_regime_performance(
    growth_1000_wide, monthly_market_style_states, *, config: AnalyticsConfig
):
    """Calculate regime performance with explicit inputs; preserve legacy conventions."""
    SLIDE9_INDEX_ORDER = config.slide9_index_order
    STATE_ORDER = config.state_order
    STATE_STRATEGIES = config.state_strategies
    monthly_strategy_returns = (
        growth_1000_wide.set_index("date")[SLIDE9_INDEX_ORDER]
        .resample("ME")
        .last()
        .pct_change()
        .dropna()
        .reset_index()
        .rename(columns={"date": "month_end"})
    )
    monthly_strategy_returns["month"] = monthly_strategy_returns["month_end"].dt.to_period("M")
    state_data = monthly_market_style_states.copy()
    state_data["month"] = state_data["month_end"].dt.to_period("M")
    state_performance = state_data[
        ["month", "market_state", "style_state", "combined_state"]
    ].merge(
        monthly_strategy_returns[["month", "S&P 500", "MC", "EW", "MC (UCITS)"]],
        on="month",
        how="inner",
        validate="one_to_one",
    )
    for strategy in STATE_STRATEGIES:
        state_performance[f"{strategy}_active_return_pp"] = (
            state_performance[strategy] - state_performance["S&P 500"]
        ) * 100
    summary_rows = []
    for market_state, style_state in STATE_ORDER:
        group = state_performance.loc[
            state_performance["market_state"].eq(market_state)
            & state_performance["style_state"].eq(style_state)
        ]
        row = {"state": f"{market_state} / {style_state}", "months_num": len(group)}
        for strategy in STATE_STRATEGIES:
            active_returns = group[f"{strategy}_active_return_pp"]
            row[f"{strategy}_mean_active_return_pp"] = active_returns.mean()
            row[f"{strategy}_win_frequency_pct"] = (
                (active_returns > 0).mean() * 100 if len(active_returns) > 0 else np.nan
            )
        summary_rows.append(row)
    market_style_performance_summary = pd.DataFrame(summary_rows)
    if len(market_style_performance_summary) != 9:
        raise ValueError("Expected exactly 9 market/style states.")
    if market_style_performance_summary["months_num"].sum() != len(state_performance):
        raise ValueError("State month counts do not reconcile to the common monthly sample.")
    for strategy in STATE_STRATEGIES:
        win_column = f"{strategy}_win_frequency_pct"
        valid_win_rates = market_style_performance_summary[win_column].dropna()
        if not valid_win_rates.between(0, 100).all():
            raise ValueError(f"{strategy}: invalid win frequency.")
    market_style_performance_table = market_style_performance_summary[
        ["state", "months_num"]
    ].copy()
    market_style_performance_table["Months Num"] = market_style_performance_table["months_num"].map(
        lambda x: f"{x} Months"
    )
    for strategy in STATE_STRATEGIES:
        mean_col = f"{strategy}_mean_active_return_pp"
        win_col = f"{strategy}_win_frequency_pct"
        market_style_performance_table[strategy] = market_style_performance_summary.apply(
            lambda row: f"{row[mean_col]:+.2f} pp\n{row[win_col]:.0f}% win frequency",
            axis=1,
        )
    market_style_performance_table = market_style_performance_table[
        ["state", "Months Num", "MC", "EW", "MC (UCITS)"]
    ].rename(columns={"state": "State"})
    return (market_style_performance_summary,)
