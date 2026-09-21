"""Analytics: cost sensitivity."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def prepare_cost_returns(cost_daily_returns_input, *, config: AnalyticsConfig):
    """Calculate cost sensitivity with explicit inputs; preserve legacy conventions."""
    cost_daily_returns = cost_daily_returns_input
    cost_daily_returns["date"] = pd.to_datetime(cost_daily_returns["date"])
    return (cost_daily_returns,)


def calculate_cost_sensitivity(cost_daily_returns, cost_turnover_input, *, config: AnalyticsConfig):
    """Calculate cost sensitivity with explicit inputs; preserve legacy conventions."""
    COST_METHODS = config.cost_methods
    COST_SCENARIOS_BPS = config.cost_scenarios_bps
    COST_STRATEGY_ORDER = config.cost_strategy_order
    TOLERANCE = config.tolerance
    cost_turnover = cost_turnover_input
    cost_turnover["date"] = pd.to_datetime(cost_turnover["date"])
    if not np.allclose(
        cost_turnover["absolute_weight_change"],
        2 * cost_turnover["turnover"],
        atol=TOLERANCE,
        rtol=0,
    ):
        raise ValueError(
            "Turnover validation failed: one-way turnover should equal 0.5 × absolute weight change."
        )
    analysis_start = cost_daily_returns["date"].min()
    analysis_end = cost_daily_returns["date"].max()
    elapsed_years = (analysis_end - analysis_start).days / 365.25
    if elapsed_years <= 0:
        raise ValueError("Invalid transaction-cost analysis period.")
    cost_rows = []
    for weighting_method, strategy_label in COST_METHODS.items():
        strategy_returns = (
            cost_daily_returns.loc[
                cost_daily_returns["weighting_method"].eq(weighting_method),
                ["date", "total_return"],
            ]
            .sort_values("date")
            .reset_index(drop=True)
            .copy()
        )
        strategy_turnover = cost_turnover.loc[
            cost_turnover["weighting_method"].eq(weighting_method)
        ].copy()
        daily_turnover = strategy_turnover.groupby("date")["turnover"].sum()
        strategy_returns["one_way_turnover"] = (
            strategy_returns["date"].map(daily_turnover).fillna(0.0)
        )
        gross_growth = (1 + strategy_returns["total_return"]).prod()
        gross_cagr = gross_growth ** (1 / elapsed_years) - 1
        for cost_bps in COST_SCENARIOS_BPS:
            cost_rate = cost_bps / 10000
            strategy_returns["cost_drag"] = strategy_returns["one_way_turnover"] * cost_rate
            net_daily_factor = (1 + strategy_returns["total_return"]) * (
                1 - strategy_returns["cost_drag"]
            )
            net_growth = net_daily_factor.prod()
            net_cagr = net_growth ** (1 / elapsed_years) - 1
            cost_rows.append(
                {
                    "strategy": strategy_label,
                    "cost_bps": cost_bps,
                    "gross_cagr": gross_cagr,
                    "net_cagr": net_cagr,
                    "cagr_cost_drag_pp": (gross_cagr - net_cagr) * 100,
                    "total_one_way_turnover": strategy_turnover["turnover"].sum(),
                    "trading_events": len(strategy_turnover),
                    "monthly_cap_reset_events": int(
                        strategy_turnover["rebalance_type"].eq("monthly_20_35").sum()
                    ),
                }
            )
    transaction_cost_sensitivity = pd.DataFrame(cost_rows)
    zero_cost = transaction_cost_sensitivity.loc[transaction_cost_sensitivity["cost_bps"].eq(0)]
    if not np.allclose(zero_cost["gross_cagr"], zero_cost["net_cagr"], atol=1e-12, rtol=0):
        raise ValueError("0 bps scenario does not reconcile to gross CAGR.")
    for strategy in COST_STRATEGY_ORDER:
        strategy_check = transaction_cost_sensitivity.loc[
            transaction_cost_sensitivity["strategy"].eq(strategy)
        ].sort_values("cost_bps")
        if not (strategy_check["net_cagr"].diff().dropna() <= TOLERANCE).all():
            raise ValueError(f"{strategy}: net CAGR increases as transaction costs rise.")
    transaction_cost_chart = (
        transaction_cost_sensitivity.pivot(index="cost_bps", columns="strategy", values="net_cagr")
        .reindex(columns=COST_STRATEGY_ORDER)
        .mul(100)
        .reset_index()
        .rename(columns={"cost_bps": "Cost (bps)"})
    )
    return (transaction_cost_chart, transaction_cost_sensitivity)
