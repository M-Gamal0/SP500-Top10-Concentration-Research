"""Analytics: construction comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def prepare_weight_metrics(daily_weight_metrics_input, *, config: AnalyticsConfig):
    """Calculate construction comparison with explicit inputs; preserve legacy conventions."""
    CONSTRUCTION_METHODS = config.construction_methods
    daily_weight_metrics = daily_weight_metrics_input
    daily_weight_metrics["index"] = daily_weight_metrics["weighting_method"].map(
        CONSTRUCTION_METHODS
    )
    daily_weight_metrics["max_issuer_weight_pct"] = daily_weight_metrics["max_issuer_weight"] * 100
    return (daily_weight_metrics,)


def compare_constructions(
    daily_weight_metrics,
    growth_1000_summary,
    growth_1000_wide,
    relative_drawdown_summary,
    turnover_data_input,
    *,
    config: AnalyticsConfig,
):
    """Calculate construction comparison with explicit inputs; preserve legacy conventions."""
    CONSTRUCTION_METHODS = config.construction_methods
    CONSTRUCTION_ORDER = config.construction_order
    TOLERANCE = config.tolerance
    turnover_data = turnover_data_input
    turnover_data["date"] = pd.to_datetime(turnover_data["date"])
    if not np.allclose(
        turnover_data["absolute_weight_change"],
        2 * turnover_data["turnover"],
        atol=TOLERANCE,
        rtol=0,
    ):
        raise ValueError(
            "Turnover convention validation failed: absolute weight change should equal 2 × one-way turnover."
        )
    analysis_start = growth_1000_wide["date"].min()
    analysis_end = growth_1000_wide["date"].max()
    elapsed_years = (analysis_end - analysis_start).days / 365.25
    if elapsed_years <= 0:
        raise ValueError("Invalid period for annualizing turnover.")
    annualized_turnover = turnover_data.groupby("weighting_method", as_index=False).agg(
        total_one_way_turnover=("turnover", "sum"), trading_events=("date", "size")
    )
    annualized_turnover["index"] = annualized_turnover["weighting_method"].map(CONSTRUCTION_METHODS)
    annualized_turnover["annualized_one_way_turnover_pct"] = (
        annualized_turnover["total_one_way_turnover"] / elapsed_years * 100
    )
    construction_summary = (
        growth_1000_summary[["index", "cagr"]]
        .loc[lambda x: x["index"].isin(CONSTRUCTION_ORDER)]
        .merge(
            daily_weight_metrics[["index", "max_issuer_weight_pct"]],
            on="index",
            how="left",
            validate="one_to_one",
        )
        .merge(
            relative_drawdown_summary[["strategy", "worst_relative_drawdown_pct"]].rename(
                columns={"strategy": "index"}
            ),
            on="index",
            how="left",
            validate="one_to_one",
        )
        .merge(
            annualized_turnover[["index", "annualized_one_way_turnover_pct"]],
            on="index",
            how="left",
            validate="one_to_one",
        )
    )
    mc_cagr = construction_summary.loc[construction_summary["index"].eq("MC"), "cagr"].iloc[0]
    construction_summary["cagr_gap_vs_mc_pp"] = (construction_summary["cagr"] - mc_cagr) * 100
    construction_summary["index"] = pd.Categorical(
        construction_summary["index"], categories=CONSTRUCTION_ORDER, ordered=True
    )
    construction_summary = construction_summary.sort_values("index").reset_index(drop=True)
    construction_summary["index"] = construction_summary["index"].astype(str)
    required_columns = [
        "cagr",
        "max_issuer_weight_pct",
        "worst_relative_drawdown_pct",
        "annualized_one_way_turnover_pct",
    ]
    if construction_summary[required_columns].isna().any().any():
        raise ValueError("Missing values detected in construction summary.")
    if len(construction_summary) != 3:
        raise ValueError("Expected exactly three Top 10 strategies.")
    if not construction_summary["max_issuer_weight_pct"].between(0, 100).all():
        raise ValueError("Maximum issuer weight is outside 0%–100%.")
    construction_table = pd.DataFrame(
        {
            "Metric": [
                "Full-period CAGR",
                "CAGR gap vs. MC",
                "Maximum issuer weight",
                "Worst relative drawdown vs. S&P 500",
                "Annualized one-way turnover",
            ]
        }
    )
    for strategy in CONSTRUCTION_ORDER:
        row = construction_summary.loc[construction_summary["index"].eq(strategy)].iloc[0]
        construction_table[strategy] = [
            f"{row['cagr']:.2%}",
            "—" if strategy == "MC" else f"{row['cagr_gap_vs_mc_pp']:+.2f} pp",
            f"{row['max_issuer_weight_pct']:.1f}%",
            f"{row['worst_relative_drawdown_pct']:.1f}%",
            f"{row['annualized_one_way_turnover_pct']:.1f}%",
        ]
    return (construction_summary,)
