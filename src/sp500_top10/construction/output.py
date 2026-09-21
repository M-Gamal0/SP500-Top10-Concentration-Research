"""Construction: output."""

from __future__ import annotations

import pandas as pd

from ..config import ConstructionConfig


def prepare_weight_output(data: pd.DataFrame, top_n: int) -> pd.DataFrame:
    output = data.copy()
    output["top_n"] = top_n
    if "base_weight" not in output.columns:
        output["base_weight"] = output["target_weight"]
    if "weight_cap" not in output.columns:
        output["weight_cap"] = float("nan")
    if "initial_cap_breach" not in output.columns:
        output["initial_cap_breach"] = pd.NA
    if "cap_binding" not in output.columns:
        output["cap_binding"] = pd.NA
    if "weight_change" not in output.columns:
        output["weight_change"] = output["target_weight"] - output["base_weight"]
    return output[
        [
            "selection_date",
            "top_n",
            "weighting_method",
            "rank",
            "ticker",
            "name",
            "resolved_marketcap",
            "marketcap_source",
            "base_weight",
            "weight_cap",
            "target_weight",
            "initial_cap_breach",
            "cap_binding",
            "weight_change",
        ]
    ]


def calculate_output(
    top10_buffered_20_weights,
    top10_equal_weights,
    top10_market_cap_weights,
    top20_market_cap_weights,
    *,
    config: ConstructionConfig,
):
    """Calculate output with explicit inputs; preserve legacy conventions."""
    CORE_TOP_N = config.core_top_n
    ROBUSTNESS_TOP_N = config.robustness_top_n
    WEIGHT_TOLERANCE = config.weight_tolerance
    quarterly_index_weights = pd.concat(
        [
            prepare_weight_output(top10_market_cap_weights, top_n=CORE_TOP_N),
            prepare_weight_output(top10_equal_weights, top_n=CORE_TOP_N),
            prepare_weight_output(top10_buffered_20_weights, top_n=CORE_TOP_N),
            prepare_weight_output(top20_market_cap_weights, top_n=ROBUSTNESS_TOP_N),
        ],
        ignore_index=True,
    )
    expected_portfolio_specs = {
        (10, "market_cap"),
        (10, "equal_weight"),
        (10, "buffered_20"),
        (20, "market_cap"),
    }
    actual_portfolio_specs = set(
        quarterly_index_weights[["top_n", "weighting_method"]].itertuples(index=False, name=None)
    )
    if actual_portfolio_specs != expected_portfolio_specs:
        raise ValueError(
            f"Unexpected portfolio specifications. Expected {expected_portfolio_specs}, found {actual_portfolio_specs}."
        )
    if not not quarterly_index_weights.duplicated(
        ["selection_date", "top_n", "weighting_method", "ticker"]
    ).any():
        raise ValueError(
            "Validation failed: not quarterly_index_weights.duplicated(['selection_date', 'top_n', 'weighting_method', 'ticker']).any()"
        )
    combined_weight_sums = quarterly_index_weights.groupby(
        ["selection_date", "top_n", "weighting_method"]
    )["target_weight"].sum()
    if not ((combined_weight_sums - 1.0).abs() <= WEIGHT_TOLERANCE).all():
        raise ValueError(
            "Validation failed: ((combined_weight_sums - 1.0).abs() <= WEIGHT_TOLERANCE).all()"
        )
    return (quarterly_index_weights,)
