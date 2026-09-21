"""Backtesting: validation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import BacktestingConfig
from .rebalancing import review_buffered_20_weights


def validate_backtest_outputs(
    daily_index: pd.DataFrame,
    daily_weights: pd.DataFrame,
    rebalance_events: pd.DataFrame,
    turnover: pd.DataFrame,
    monthly_reviews: pd.DataFrame,
    expected_quarterly_weights: pd.DataFrame,
    month_end_trading_dates: set[pd.Timestamp],
    top_n: int,
    base_date: pd.Timestamp,
    final_date: pd.Timestamp,
    tolerance: float = None,
    *,
    config: BacktestingConfig,
) -> None:
    VALIDATION_TOLERANCE = config.validation_tolerance
    if tolerance is None:
        tolerance = VALIDATION_TOLERANCE
    if daily_index.duplicated(["top_n", "weighting_method", "date"]).any():
        raise ValueError("Duplicate daily-index rows detected.")
    if daily_weights.duplicated(["top_n", "weighting_method", "date", "ticker"]).any():
        raise ValueError("Duplicate daily-weight rows detected.")
    if rebalance_events.duplicated(
        ["top_n", "weighting_method", "date", "rebalance_type", "ticker"]
    ).any():
        raise ValueError("Duplicate rebalance-event rows detected.")
    if turnover.duplicated(["top_n", "weighting_method", "date", "rebalance_type"]).any():
        raise ValueError("Duplicate turnover rows detected.")
    if not (daily_index["top_n"] == top_n).all():
        raise ValueError("Unexpected top_n value in daily index.")
    coverage = daily_index.groupby("weighting_method").agg(
        rows=("date", "size"), start_date=("date", "min"), end_date=("date", "max")
    )
    if coverage["rows"].nunique() != 1:
        raise ValueError("Strategies have different date counts.")
    if not (coverage["start_date"] == base_date).all():
        raise ValueError("Unexpected backtest start date.")
    if not (coverage["end_date"] == final_date).all():
        raise ValueError("Unexpected backtest end date.")
    if (
        daily_index[["price_return", "total_return", "price_index_value", "total_index_value"]]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("Missing values detected in daily index output.")
    if (daily_index[["price_index_value", "total_index_value"]] <= 0).any().any():
        raise ValueError("Non-positive index level detected.")
    daily_weight_check = daily_weights.groupby(["weighting_method", "date"]).agg(
        holdings=("ticker", "size"),
        beginning_sum=("beginning_weight", "sum"),
        ending_sum=("ending_weight", "sum"),
    )
    if not (daily_weight_check["holdings"] == top_n).all():
        raise ValueError("Unexpected daily constituent count.")
    if not np.allclose(daily_weight_check["beginning_sum"], 1.0, atol=tolerance):
        raise ValueError("Beginning weights do not sum to 100%.")
    if not np.allclose(daily_weight_check["ending_sum"], 1.0, atol=tolerance):
        raise ValueError("Ending weights do not sum to 100%.")
    if (daily_weights[["beginning_weight", "ending_weight"]] < -tolerance).any().any():
        raise ValueError("Negative portfolio weight detected.")
    contribution_check = (
        daily_weights.groupby(["weighting_method", "date"], as_index=False)
        .agg(
            calculated_price_return=("price_return_contribution", "sum"),
            calculated_total_return=("total_return_contribution", "sum"),
        )
        .merge(
            daily_index[["weighting_method", "date", "price_return", "total_return"]],
            on=["weighting_method", "date"],
            how="left",
            validate="one_to_one",
        )
    )
    if (
        contribution_check["calculated_price_return"] - contribution_check["price_return"]
    ).abs().max() > tolerance:
        raise ValueError("Price-return contributions do not reconcile.")
    if (
        contribution_check["calculated_total_return"] - contribution_check["total_return"]
    ).abs().max() > tolerance:
        raise ValueError("Total-return contributions do not reconcile.")
    compounding_check = daily_index.sort_values(["weighting_method", "date"]).copy()
    compounding_check["calculated_price_return"] = compounding_check.groupby("weighting_method")[
        "price_index_value"
    ].pct_change(fill_method=None)
    compounding_check["calculated_total_return"] = compounding_check.groupby("weighting_method")[
        "total_index_value"
    ].pct_change(fill_method=None)
    non_base_rows = compounding_check["date"] != base_date
    if (
        compounding_check.loc[non_base_rows, "calculated_price_return"]
        - compounding_check.loc[non_base_rows, "price_return"]
    ).abs().max() > tolerance:
        raise ValueError("Price-index compounding does not reconcile.")
    if (
        compounding_check.loc[non_base_rows, "calculated_total_return"]
        - compounding_check.loc[non_base_rows, "total_return"]
    ).abs().max() > tolerance:
        raise ValueError("Total-return-index compounding does not reconcile.")
    expected_targets = expected_quarterly_weights[
        ["effective_rebalance_date", "weighting_method", "ticker", "target_weight"]
    ].rename(
        columns={
            "effective_rebalance_date": "date",
            "target_weight": "expected_target_weight",
        }
    )
    actual_targets = daily_weights.loc[
        daily_weights["rebalance_type"] == "quarterly",
        ["weighting_method", "date", "ticker", "beginning_weight"],
    ]
    target_check = expected_targets.merge(
        actual_targets,
        on=["weighting_method", "date", "ticker"],
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    if not (target_check["_merge"] == "both").all():
        raise ValueError("Quarterly target rows do not match the realized rebalance rows.")
    if (
        target_check["beginning_weight"] - target_check["expected_target_weight"]
    ).abs().max() > tolerance:
        raise ValueError("Quarterly target weights were not installed exactly.")
    calculated_weight_change = (
        rebalance_events["target_weight"] - rebalance_events["pre_rebalance_weight"]
    )
    if not np.allclose(rebalance_events["weight_change"], calculated_weight_change, atol=tolerance):
        raise ValueError("Stored rebalance weight changes are incorrect.")
    rebalance_sums = rebalance_events.groupby(["weighting_method", "date", "rebalance_type"]).agg(
        pre_weight_sum=("pre_rebalance_weight", "sum"),
        target_weight_sum=("target_weight", "sum"),
        net_weight_change=("weight_change", "sum"),
    )
    if not np.allclose(rebalance_sums["pre_weight_sum"], 1.0, atol=tolerance):
        raise ValueError("Pre-rebalance weights do not sum to 100%.")
    if not np.allclose(rebalance_sums["target_weight_sum"], 1.0, atol=tolerance):
        raise ValueError("Rebalance target weights do not sum to 100%.")
    if not np.allclose(rebalance_sums["net_weight_change"], 0.0, atol=tolerance):
        raise ValueError("Net rebalance weight change is not zero.")
    recalculated_turnover = rebalance_events.groupby(
        ["weighting_method", "date", "rebalance_type"], as_index=False
    ).agg(recalculated_turnover=("weight_change", lambda x: 0.5 * x.abs().sum()))
    turnover_check = turnover.merge(
        recalculated_turnover,
        on=["weighting_method", "date", "rebalance_type"],
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    if not (turnover_check["_merge"] == "both").all():
        raise ValueError("Turnover rows do not match rebalance events.")
    if (
        turnover_check["turnover"] - turnover_check["recalculated_turnover"]
    ).abs().max() > tolerance:
        raise ValueError("Turnover calculation does not reconcile.")
    if (turnover["turnover"] < -tolerance).any() or (turnover["turnover"] > 1 + tolerance).any():
        raise ValueError("Turnover falls outside the valid 0% to 100% range.")
    buffered_month_end_weights = daily_weights.loc[
        (daily_weights["weighting_method"] == "buffered_20")
        & daily_weights["date"].isin(month_end_trading_dates)
        & (daily_weights["date"] != base_date)
    ]
    expected_breach_dates = set()
    for date, group in buffered_month_end_weights.groupby("date"):
        current_weights = group.set_index("ticker")["ending_weight"]
        breach_detected, _, _ = review_buffered_20_weights(current_weights, config=config)
        if breach_detected:
            expected_breach_dates.add(pd.Timestamp(date).normalize())
    actual_breach_dates = set(pd.to_datetime(monthly_reviews["review_date"]).dt.normalize())
    if expected_breach_dates != actual_breach_dates:
        raise ValueError("Monthly buffered 20 breach log is incomplete or contains extra events.")
    if not monthly_reviews.empty:
        if not (monthly_reviews["weighting_method"] == "buffered_20").all():
            raise ValueError("Monthly 20 event found outside the buffered strategy.")
        valid_actions = {
            "monthly_reset_scheduled",
            "superseded_by_quarterly",
            "no_next_trading_date",
        }
        if not monthly_reviews["action"].isin(valid_actions).all():
            raise ValueError("Unexpected monthly review action.")
        scheduled_monthly_dates = set(
            monthly_reviews.loc[
                monthly_reviews["action"] == "monthly_reset_scheduled",
                "scheduled_rebalance_date",
            ]
        )
        actual_monthly_dates = set(
            daily_index.loc[
                (daily_index["weighting_method"] == "buffered_20")
                & (daily_index["rebalance_type"] == "monthly_20"),
                "date",
            ]
        )
        if scheduled_monthly_dates != actual_monthly_dates:
            raise ValueError("Scheduled monthly resets do not match realized monthly resets.")
        superseded_dates = set(
            monthly_reviews.loc[
                monthly_reviews["action"] == "superseded_by_quarterly",
                "scheduled_rebalance_date",
            ]
        )
        buffered_quarterly_dates = set(
            daily_index.loc[
                (daily_index["weighting_method"] == "buffered_20")
                & (daily_index["rebalance_type"] == "quarterly"),
                "date",
            ]
        )
        if not superseded_dates <= buffered_quarterly_dates:
            raise ValueError(
                "A monthly reset was marked as superseded without a quarterly rebalance."
            )


def calculate_validation(
    active_quarterly_weights,
    all_daily_index,
    all_daily_weights,
    all_monthly_reviews,
    all_rebalance_events,
    all_turnover,
    base_date,
    final_date,
    month_end_trading_dates,
    *,
    config: BacktestingConfig,
):
    """Calculate validation with explicit inputs; preserve legacy conventions."""
    PORTFOLIO_SPECS = config.portfolio_specs
    for top_n in sorted({top_n for top_n, _ in PORTFOLIO_SPECS}):
        validate_backtest_outputs(
            daily_index=all_daily_index.loc[all_daily_index["top_n"].eq(top_n)].copy(),
            daily_weights=all_daily_weights.loc[all_daily_weights["top_n"].eq(top_n)].copy(),
            rebalance_events=all_rebalance_events.loc[
                all_rebalance_events["top_n"].eq(top_n)
            ].copy(),
            turnover=all_turnover.loc[all_turnover["top_n"].eq(top_n)].copy(),
            monthly_reviews=all_monthly_reviews.loc[all_monthly_reviews["top_n"].eq(top_n)].copy(),
            expected_quarterly_weights=active_quarterly_weights.loc[
                active_quarterly_weights["top_n"].eq(top_n)
            ].copy(),
            month_end_trading_dates=month_end_trading_dates,
            top_n=top_n,
            base_date=base_date,
            final_date=final_date,
            config=config,
        )
    return ()
