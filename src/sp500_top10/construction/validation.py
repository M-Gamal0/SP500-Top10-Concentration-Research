"""Construction: validation."""

from __future__ import annotations

import pandas as pd

from ..config import ConstructionConfig


def validate_weighting(
    data: pd.DataFrame,
    top_n: int,
    tolerance: float = None,
    *,
    config: ConstructionConfig,
) -> None:
    WEIGHT_TOLERANCE = config.weight_tolerance
    if tolerance is None:
        tolerance = WEIGHT_TOLERANCE
    required_columns = [
        "selection_date",
        "rank",
        "ticker",
        "resolved_marketcap",
        "weighting_method",
        "target_weight",
    ]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    methods = data["weighting_method"].unique()
    if len(methods) != 1:
        raise ValueError(f"Expected one weighting method, found: {methods}")
    method = methods[0]
    if data.duplicated(["selection_date", "ticker"]).any():
        raise ValueError("Duplicate selection_date + ticker rows found.")
    portfolio_check = data.groupby("selection_date").agg(
        holdings=("ticker", "size"),
        unique_tickers=("ticker", "nunique"),
        min_rank=("rank", "min"),
        max_rank=("rank", "max"),
        unique_ranks=("rank", "nunique"),
        weight_sum=("target_weight", "sum"),
    )
    if (
        (portfolio_check["holdings"] != top_n).any()
        or (portfolio_check["unique_tickers"] != top_n).any()
        or (portfolio_check["min_rank"] != 1).any()
        or (portfolio_check["max_rank"] != top_n).any()
        or (portfolio_check["unique_ranks"] != top_n).any()
    ):
        raise ValueError("Portfolio constituent or rank structure is invalid.")
    if data["target_weight"].isna().any():
        raise ValueError("Missing target weights found.")
    if (data["target_weight"] <= 0).any():
        raise ValueError("Non-positive target weights found.")
    if ((portfolio_check["weight_sum"] - 1.0).abs() > tolerance).any():
        raise ValueError("Target weights do not sum to 100%.")
    if method == "market_cap":
        expected_weight = data["resolved_marketcap"] / data.groupby("selection_date")[
            "resolved_marketcap"
        ].transform("sum")
        if ((data["target_weight"] - expected_weight).abs() > tolerance).any():
            raise ValueError("Market-cap weights are incorrect.")
    elif method == "equal_weight":
        expected_weight = 1 / top_n
        if ((data["target_weight"] - expected_weight).abs() > tolerance).any():
            raise ValueError("Equal weights are incorrect.")
    elif method == "buffered_20":
        if "weight_cap" not in data.columns:
            raise ValueError("Buffered strategy is missing weight_cap.")
        if (data["target_weight"] > data["weight_cap"] + tolerance).any():
            raise ValueError("Buffered 20 cap breach found.")


def calculate_validation(
    top10_buffered_20_weights,
    top10_equal_weights,
    top10_market_cap_weights,
    top20_market_cap_weights,
    *,
    config: ConstructionConfig,
):
    """Calculate validation with explicit inputs; preserve legacy conventions."""
    CORE_TOP_N = config.core_top_n
    ROBUSTNESS_TOP_N = config.robustness_top_n
    validate_weighting(top10_market_cap_weights, top_n=CORE_TOP_N, config=config)
    validate_weighting(top10_equal_weights, top_n=CORE_TOP_N, config=config)
    validate_weighting(top10_buffered_20_weights, top_n=CORE_TOP_N, config=config)
    validate_weighting(top20_market_cap_weights, top_n=ROBUSTNESS_TOP_N, config=config)
    return ()
