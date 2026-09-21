"""Analytics: rolling distribution."""

from __future__ import annotations

import pandas as pd

from ..config import AnalyticsConfig


def calculate_rolling_distribution(growth_1000_wide, *, config: AnalyticsConfig):
    """Calculate rolling distribution with explicit inputs; preserve legacy conventions."""
    ROLLING_HORIZONS = config.rolling_horizons
    ROLLING_STRATEGIES = config.rolling_strategies
    SLIDE9_INDEX_ORDER = config.slide9_index_order
    STRATEGY_Y_POSITION = config.strategy_y_position
    monthly_wealth = (
        growth_1000_wide.set_index("date")[SLIDE9_INDEX_ORDER].resample("ME").last().dropna()
    )
    expected_months = pd.period_range(
        monthly_wealth.index.min().to_period("M"),
        monthly_wealth.index.max().to_period("M"),
        freq="M",
    )
    actual_months = monthly_wealth.index.to_period("M")
    if not actual_months.equals(expected_months):
        raise ValueError("Monthly wealth series contains missing months.")
    if monthly_wealth.isna().any().any():
        raise ValueError("Monthly wealth series contains missing values.")
    if len(monthly_wealth) <= max(ROLLING_HORIZONS):
        raise ValueError("Insufficient history for requested rolling windows.")
    rolling_rows = []
    for horizon_months, horizon_label in ROLLING_HORIZONS.items():
        for end_position in range(horizon_months, len(monthly_wealth)):
            start_position = end_position - horizon_months
            start_date = monthly_wealth.index[start_position]
            end_date = monthly_wealth.index[end_position]
            start_values = monthly_wealth.iloc[start_position]
            end_values = monthly_wealth.iloc[end_position]
            benchmark_cagr = (end_values["S&P 500"] / start_values["S&P 500"]) ** (
                12 / horizon_months
            ) - 1
            for strategy in ROLLING_STRATEGIES:
                strategy_cagr = (end_values[strategy] / start_values[strategy]) ** (
                    12 / horizon_months
                ) - 1
                rolling_rows.append(
                    {
                        "horizon": horizon_label,
                        "horizon_months": horizon_months,
                        "window_start": start_date,
                        "window_end": end_date,
                        "strategy": strategy,
                        "strategy_cagr": strategy_cagr,
                        "benchmark_cagr": benchmark_cagr,
                        "cagr_gap_pp": (strategy_cagr - benchmark_cagr) * 100,
                    }
                )
    rolling_cagr_windows = pd.DataFrame(rolling_rows)
    distribution_rows = []
    for (
        horizon_label,
        horizon_months,
        strategy,
    ), group in rolling_cagr_windows.groupby(["horizon", "horizon_months", "strategy"], sort=False):
        gaps = group["cagr_gap_pp"]
        distribution_rows.append(
            {
                "horizon": horizon_label,
                "horizon_months": horizon_months,
                "strategy": strategy,
                "median_cagr_gap_pp": gaps.median(),
                "p10_cagr_gap_pp": gaps.quantile(0.1),
                "p90_cagr_gap_pp": gaps.quantile(0.9),
                "win_rate_pct": (gaps > 0).mean() * 100,
                "n_windows": len(gaps),
            }
        )
    rolling_cagr_distribution = pd.DataFrame(distribution_rows)
    rolling_cagr_chart = rolling_cagr_distribution.copy()
    rolling_cagr_chart["median_x"] = rolling_cagr_chart["median_cagr_gap_pp"]
    rolling_cagr_chart["y_position"] = rolling_cagr_chart["strategy"].map(STRATEGY_Y_POSITION)
    rolling_cagr_chart["negative_error"] = (
        rolling_cagr_chart["median_cagr_gap_pp"] - rolling_cagr_chart["p10_cagr_gap_pp"]
    )
    rolling_cagr_chart["positive_error"] = (
        rolling_cagr_chart["p90_cagr_gap_pp"] - rolling_cagr_chart["median_cagr_gap_pp"]
    )
    rolling_cagr_chart = rolling_cagr_chart[
        [
            "horizon",
            "strategy",
            "y_position",
            "median_x",
            "p10_cagr_gap_pp",
            "p90_cagr_gap_pp",
            "negative_error",
            "positive_error",
            "win_rate_pct",
            "n_windows",
        ]
    ].copy()
    if (rolling_cagr_chart["negative_error"] < 0).any():
        raise ValueError("Negative custom error-bar magnitude detected.")
    if (rolling_cagr_chart["positive_error"] < 0).any():
        raise ValueError("Negative custom error-bar magnitude detected.")
    if rolling_cagr_chart[["median_x", "negative_error", "positive_error"]].isna().any().any():
        raise ValueError("Missing values in rolling CAGR chart data.")
    if not (rolling_cagr_chart[["negative_error", "positive_error"]] >= 0).all().all():
        raise ValueError("PowerPoint error-bar values must be non-negative.")
    for horizon_months, horizon_label in ROLLING_HORIZONS.items():
        expected_windows = len(monthly_wealth) - horizon_months
        horizon_check = rolling_cagr_distribution.loc[
            rolling_cagr_distribution["horizon_months"].eq(horizon_months)
        ]
        if not horizon_check["n_windows"].eq(expected_windows).all():
            raise ValueError(f"{horizon_label}: rolling window count validation failed.")
    if not rolling_cagr_distribution["win_rate_pct"].between(0, 100).all():
        raise ValueError("Rolling win rate is outside 0%–100%.")
    if not (
        rolling_cagr_distribution["p10_cagr_gap_pp"]
        <= rolling_cagr_distribution["median_cagr_gap_pp"]
    ).all():
        raise ValueError("10th percentile exceeds median.")
    if not (
        rolling_cagr_distribution["median_cagr_gap_pp"]
        <= rolling_cagr_distribution["p90_cagr_gap_pp"]
    ).all():
        raise ValueError("Median exceeds 90th percentile.")
    return (rolling_cagr_chart, rolling_cagr_distribution)
