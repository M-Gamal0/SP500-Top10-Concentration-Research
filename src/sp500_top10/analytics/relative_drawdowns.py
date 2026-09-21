"""Analytics: relative drawdowns."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def relative_drawdown_analysis(
    daily_frame, strategy, benchmark="S&P 500", *, config: AnalyticsConfig
):
    TOLERANCE = config.tolerance
    frame = (
        daily_frame[["date", benchmark, strategy]].sort_values("date").reset_index(drop=True).copy()
    )
    frame["relative_wealth"] = frame[strategy] / frame[benchmark]
    frame["relative_wealth"] = frame["relative_wealth"] / frame["relative_wealth"].iloc[0]
    frame["relative_peak"] = frame["relative_wealth"].cummax()
    frame["relative_drawdown"] = frame["relative_wealth"] / frame["relative_peak"] - 1
    episodes = []
    running_peak = frame.loc[0, "relative_wealth"]
    running_peak_date = frame.loc[0, "date"]
    open_episode = None
    for row in frame.itertuples(index=False):
        date = row.date
        relative_wealth = row.relative_wealth
        if relative_wealth >= running_peak - TOLERANCE:
            if open_episode is not None:
                open_episode["recovery_date"] = date
                open_episode["completed"] = True
                open_episode["duration_calendar_days"] = (date - open_episode["peak_date"]).days
                episodes.append(open_episode)
                open_episode = None
            if relative_wealth > running_peak + TOLERANCE:
                running_peak = relative_wealth
                running_peak_date = date
            continue
        current_drawdown = relative_wealth / running_peak - 1
        if open_episode is None:
            open_episode = {
                "peak_date": running_peak_date,
                "peak_relative_wealth": running_peak,
                "trough_date": date,
                "trough_relative_wealth": relative_wealth,
                "worst_relative_drawdown": current_drawdown,
                "recovery_date": pd.NaT,
                "completed": False,
            }
        elif current_drawdown < open_episode["worst_relative_drawdown"]:
            open_episode["trough_date"] = date
            open_episode["trough_relative_wealth"] = relative_wealth
            open_episode["worst_relative_drawdown"] = current_drawdown
    if open_episode is not None:
        open_episode["duration_calendar_days"] = (
            frame["date"].iloc[-1] - open_episode["peak_date"]
        ).days
        episodes.append(open_episode)
    episodes_df = pd.DataFrame(episodes)
    worst_idx = frame["relative_drawdown"].idxmin()
    worst_relative_drawdown = frame.loc[worst_idx, "relative_drawdown"]
    if not episodes_df.empty:
        worst_episode = episodes_df.loc[episodes_df["worst_relative_drawdown"].idxmin()]
        completed_episodes = episodes_df.loc[episodes_df["completed"]]
        open_episodes = episodes_df.loc[~episodes_df["completed"]]
        longest_completed_days = (
            completed_episodes["duration_calendar_days"].max()
            if not completed_episodes.empty
            else 0
        )
        if not open_episodes.empty:
            current_open_days = int(open_episodes["duration_calendar_days"].iloc[-1])
            current_open_censored = True
        else:
            current_open_days = 0
            current_open_censored = False
        summary = {
            "strategy": strategy,
            "worst_relative_drawdown_pct": worst_relative_drawdown * 100,
            "peak": worst_episode["peak_date"],
            "trough": worst_episode["trough_date"],
            "recovery": worst_episode["recovery_date"],
            "longest_completed_underperformance_days": int(longest_completed_days),
            "current_open_underperformance_days": current_open_days,
            "current_open_censored": current_open_censored,
        }
    else:
        summary = {
            "strategy": strategy,
            "worst_relative_drawdown_pct": 0.0,
            "peak": frame["date"].iloc[0],
            "trough": frame["date"].iloc[0],
            "recovery": frame["date"].iloc[0],
            "longest_completed_underperformance_days": 0,
            "current_open_underperformance_days": 0,
            "current_open_censored": False,
        }
    return (frame[["date", "relative_wealth", "relative_drawdown"]], summary)


def calculate_relative_drawdowns(growth_1000_wide, *, config: AnalyticsConfig):
    """Calculate relative drawdowns with explicit inputs; preserve legacy conventions."""
    RELATIVE_STRATEGIES = config.relative_strategies
    TOLERANCE = config.tolerance
    relative_series = {}
    relative_summary_rows = []
    for strategy in RELATIVE_STRATEGIES:
        series, summary = relative_drawdown_analysis(
            growth_1000_wide, strategy=strategy, config=config
        )
        relative_series[strategy] = series
        relative_summary_rows.append(summary)
    relative_drawdown_daily = growth_1000_wide[["date"]].copy()
    for strategy in RELATIVE_STRATEGIES:
        strategy_series = relative_series[strategy]
        relative_drawdown_daily[f"{strategy} Relative Wealth"] = strategy_series["relative_wealth"]
        relative_drawdown_daily[f"{strategy} Relative Drawdown"] = (
            strategy_series["relative_drawdown"] * 100
        )
    relative_drawdown_daily = relative_drawdown_daily.rename(columns={"date": "Date"})
    relative_drawdown_summary = pd.DataFrame(relative_summary_rows)
    relative_drawdown_summary["longest_completed_underperformance_years"] = (
        relative_drawdown_summary["longest_completed_underperformance_days"] / 365.25
    )
    relative_drawdown_summary["current_open_underperformance_years"] = (
        relative_drawdown_summary["current_open_underperformance_days"] / 365.25
    )
    relative_columns = [column for column in relative_drawdown_daily.columns if column != "Date"]
    if relative_drawdown_daily[relative_columns].isna().any().any():
        raise ValueError("Missing values detected in relative drawdown output.")
    drawdown_columns = [f"{strategy} Relative Drawdown" for strategy in RELATIVE_STRATEGIES]
    if (relative_drawdown_daily[drawdown_columns] > TOLERANCE).any().any():
        raise ValueError("Relative drawdown cannot exceed zero.")
    wealth_columns = [f"{strategy} Relative Wealth" for strategy in RELATIVE_STRATEGIES]
    if not np.allclose(
        relative_drawdown_daily[wealth_columns].iloc[0], 1.0, atol=TOLERANCE, rtol=0
    ):
        raise ValueError("Relative wealth series do not start at 1.0.")
    if relative_drawdown_daily["Date"].duplicated().any():
        raise ValueError("Duplicate dates detected in relative drawdown output.")
    relative_drawdown_summary_display = relative_drawdown_summary[
        [
            "strategy",
            "worst_relative_drawdown_pct",
            "longest_completed_underperformance_years",
            "current_open_underperformance_years",
            "current_open_censored",
        ]
    ].copy()
    relative_drawdown_summary_display["Worst Relative Drawdown"] = (
        relative_drawdown_summary_display["worst_relative_drawdown_pct"].map(lambda x: f"{x:.1f}%")
    )
    relative_drawdown_summary_display["Longest Completed Streak"] = (
        relative_drawdown_summary_display["longest_completed_underperformance_years"].map(
            lambda x: f"{x:.1f} yrs"
        )
    )
    relative_drawdown_summary_display["Current Open Streak"] = (
        relative_drawdown_summary_display.apply(
            lambda row: (
                f"{row['current_open_underperformance_years']:.1f} yrs (censored)"
                if row["current_open_censored"]
                else "None"
            ),
            axis=1,
        )
    )
    relative_drawdown_summary_display = relative_drawdown_summary_display[
        [
            "strategy",
            "Worst Relative Drawdown",
            "Longest Completed Streak",
            "Current Open Streak",
        ]
    ].rename(columns={"strategy": "Strategy"})
    return (relative_drawdown_daily, relative_drawdown_summary)
