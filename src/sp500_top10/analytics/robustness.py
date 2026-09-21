"""Analytics: robustness."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def prepare_robustness_levels(robustness_strategy_levels_input, *, config: AnalyticsConfig):
    """Calculate robustness with explicit inputs; preserve legacy conventions."""
    robustness_strategy_levels = robustness_strategy_levels_input
    robustness_strategy_levels["date"] = pd.to_datetime(robustness_strategy_levels["date"])
    return (robustness_strategy_levels,)


def calculate_robustness_returns(
    robustness_benchmark_input, robustness_strategy_levels, *, config: AnalyticsConfig
):
    """Calculate robustness with explicit inputs; preserve legacy conventions."""
    ROBUSTNESS_TOP_NS = config.robustness_top_ns
    ROLLING_WIN_MONTHS = config.rolling_win_months
    robustness_benchmark = robustness_benchmark_input
    robustness_benchmark["date"] = pd.to_datetime(robustness_benchmark["date"])
    available_top_n = set(robustness_strategy_levels["top_n"].unique())
    expected_top_n = set(ROBUSTNESS_TOP_NS)
    if available_top_n != expected_top_n:
        raise ValueError(
            f"Expected Top-N series {sorted(expected_top_n)}, found {sorted(available_top_n)}."
        )
    if robustness_strategy_levels.duplicated(["date", "top_n"]).any():
        raise ValueError("Duplicate Top-N daily index observations detected.")
    if robustness_benchmark["date"].duplicated().any():
        raise ValueError("Duplicate S&P 500 benchmark observations detected.")
    robustness_daily = (
        robustness_strategy_levels.pivot(index="date", columns="top_n", values="total_index_value")
        .rename(columns=ROBUSTNESS_TOP_NS)
        .reset_index()
        .merge(
            robustness_benchmark.rename(columns={"close": "S&P 500"}),
            on="date",
            how="inner",
            validate="one_to_one",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )
    if robustness_daily[["Top 10 MC", "Top 20 MC", "S&P 500"]].isna().any().any():
        raise ValueError("Missing values detected in robustness series.")
    expected_dates = set(robustness_benchmark["date"])
    for top_n in ROBUSTNESS_TOP_NS:
        strategy_dates = set(
            robustness_strategy_levels.loc[robustness_strategy_levels["top_n"].eq(top_n), "date"]
        )
        if strategy_dates != expected_dates:
            raise ValueError(f"Top {top_n} MC calendar does not match benchmark.")
    analysis_start = robustness_daily["date"].iloc[0]
    analysis_end = robustness_daily["date"].iloc[-1]
    elapsed_years = (analysis_end - analysis_start).days / 365.25
    if elapsed_years <= 0:
        raise ValueError("Invalid robustness analysis period.")
    full_period_cagr = {}
    for portfolio in ["Top 10 MC", "Top 20 MC", "S&P 500"]:
        start_value = float(robustness_daily[portfolio].iloc[0])
        end_value = float(robustness_daily[portfolio].iloc[-1])
        full_period_cagr[portfolio] = (end_value / start_value) ** (1 / elapsed_years) - 1
    benchmark_cagr = full_period_cagr["S&P 500"]
    robustness_monthly = (
        robustness_daily.set_index("date")[["Top 10 MC", "Top 20 MC", "S&P 500"]]
        .resample("ME")
        .last()
    )
    expected_months = pd.period_range(
        robustness_monthly.index.min().to_period("M"),
        robustness_monthly.index.max().to_period("M"),
        freq="M",
    )
    actual_months = robustness_monthly.index.to_period("M")
    if not actual_months.equals(expected_months):
        raise ValueError("Robustness monthly series contains missing months.")
    rolling_60m_cagr = (robustness_monthly / robustness_monthly.shift(ROLLING_WIN_MONTHS)) ** (
        12 / ROLLING_WIN_MONTHS
    ) - 1
    five_year_win_frequency_pct = {}
    for portfolio in ["Top 10 MC", "Top 20 MC"]:
        rolling_gap = (rolling_60m_cagr[portfolio] - rolling_60m_cagr["S&P 500"]).dropna()
        if rolling_gap.empty:
            raise ValueError(f"No complete 60-month windows for {portfolio}.")
        five_year_win_frequency_pct[portfolio] = (rolling_gap > 0).mean() * 100
    worst_relative_drawdown_pct = {}
    benchmark_normalized = robustness_daily["S&P 500"] / robustness_daily["S&P 500"].iloc[0]
    for portfolio in ["Top 10 MC", "Top 20 MC"]:
        strategy_normalized = robustness_daily[portfolio] / robustness_daily[portfolio].iloc[0]
        relative_wealth = strategy_normalized / benchmark_normalized
        relative_drawdown = relative_wealth / relative_wealth.cummax() - 1
        worst_relative_drawdown_pct[portfolio] = relative_drawdown.min() * 100
    return (
        benchmark_cagr,
        five_year_win_frequency_pct,
        full_period_cagr,
        worst_relative_drawdown_pct,
    )


def summarize_robustness(
    benchmark_cagr,
    five_year_win_frequency_pct,
    full_period_cagr,
    max_issuer_weights_input,
    worst_relative_drawdown_pct,
    *,
    config: AnalyticsConfig,
):
    """Calculate robustness with explicit inputs; preserve legacy conventions."""
    ROBUSTNESS_TOP_NS = config.robustness_top_ns
    max_issuer_weights = max_issuer_weights_input
    max_issuer_weight_pct = {
        ROBUSTNESS_TOP_NS[row.top_n]: row.max_issuer_weight * 100
        for row in max_issuer_weights.itertuples(index=False)
    }
    if set(max_issuer_weight_pct) != {"Top 10 MC", "Top 20 MC"}:
        raise ValueError("Missing maximum issuer-weight result.")
    topn_robustness_summary = pd.DataFrame(
        [
            {
                "portfolio": "Top 10 MC",
                "top_n": 10,
                "full_period_cagr": full_period_cagr["Top 10 MC"],
                "cagr_gap_vs_sp500_pp": (full_period_cagr["Top 10 MC"] - benchmark_cagr) * 100,
                "five_year_win_frequency_pct": five_year_win_frequency_pct["Top 10 MC"],
                "worst_relative_drawdown_pct": worst_relative_drawdown_pct["Top 10 MC"],
                "max_issuer_weight_pct": max_issuer_weight_pct["Top 10 MC"],
            },
            {
                "portfolio": "Top 20 MC",
                "top_n": 20,
                "full_period_cagr": full_period_cagr["Top 20 MC"],
                "cagr_gap_vs_sp500_pp": (full_period_cagr["Top 20 MC"] - benchmark_cagr) * 100,
                "five_year_win_frequency_pct": five_year_win_frequency_pct["Top 20 MC"],
                "worst_relative_drawdown_pct": worst_relative_drawdown_pct["Top 20 MC"],
                "max_issuer_weight_pct": max_issuer_weight_pct["Top 20 MC"],
            },
            {
                "portfolio": "S&P 500",
                "top_n": np.nan,
                "full_period_cagr": benchmark_cagr,
                "cagr_gap_vs_sp500_pp": 0.0,
                "five_year_win_frequency_pct": np.nan,
                "worst_relative_drawdown_pct": 0.0,
                "max_issuer_weight_pct": np.nan,
            },
        ]
    )
    if len(topn_robustness_summary) != 3:
        raise ValueError("Expected three robustness comparison rows.")
    strategy_rows = topn_robustness_summary["portfolio"].isin(["Top 10 MC", "Top 20 MC"])
    required_strategy_metrics = [
        "full_period_cagr",
        "cagr_gap_vs_sp500_pp",
        "five_year_win_frequency_pct",
        "worst_relative_drawdown_pct",
        "max_issuer_weight_pct",
    ]
    if topn_robustness_summary.loc[strategy_rows, required_strategy_metrics].isna().any().any():
        raise ValueError("Missing Top 10 / Top 20 robustness metric.")
    if (
        not topn_robustness_summary.loc[strategy_rows, "five_year_win_frequency_pct"]
        .between(0, 100)
        .all()
    ):
        raise ValueError("Invalid 5-year win frequency.")
    pd.DataFrame(
        {
            "Metric": [
                "Full-period CAGR gap vs. S&P 500",
                "5-year rolling win frequency",
                "Worst relative drawdown vs. S&P 500",
                "Maximum issuer weight",
            ],
            "Top 10 MC": [
                f"{topn_robustness_summary.loc[topn_robustness_summary['portfolio'].eq('Top 10 MC'), 'cagr_gap_vs_sp500_pp'].iloc[0]:+.2f} pp",
                f"{topn_robustness_summary.loc[topn_robustness_summary['portfolio'].eq('Top 10 MC'), 'five_year_win_frequency_pct'].iloc[0]:.1f}%",
                f"{topn_robustness_summary.loc[topn_robustness_summary['portfolio'].eq('Top 10 MC'), 'worst_relative_drawdown_pct'].iloc[0]:.1f}%",
                f"{topn_robustness_summary.loc[topn_robustness_summary['portfolio'].eq('Top 10 MC'), 'max_issuer_weight_pct'].iloc[0]:.1f}%",
            ],
            "Top 20 MC": [
                f"{topn_robustness_summary.loc[topn_robustness_summary['portfolio'].eq('Top 20 MC'), 'cagr_gap_vs_sp500_pp'].iloc[0]:+.2f} pp",
                f"{topn_robustness_summary.loc[topn_robustness_summary['portfolio'].eq('Top 20 MC'), 'five_year_win_frequency_pct'].iloc[0]:.1f}%",
                f"{topn_robustness_summary.loc[topn_robustness_summary['portfolio'].eq('Top 20 MC'), 'worst_relative_drawdown_pct'].iloc[0]:.1f}%",
                f"{topn_robustness_summary.loc[topn_robustness_summary['portfolio'].eq('Top 20 MC'), 'max_issuer_weight_pct'].iloc[0]:.1f}%",
            ],
            "S&P 500": ["0.00 pp", "—", "0.0%", "—"],
        }
    )
    return (topn_robustness_summary,)
