"""Analytics: drawdowns."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def calculate_drawdowns(growth_1000_wide, *, config: AnalyticsConfig):
    """Calculate drawdowns with explicit inputs; preserve legacy conventions."""
    DRAWDOWN_INDEX_ORDER = config.drawdown_index_order
    TOLERANCE = config.tolerance
    absolute_drawdown_daily = (
        growth_1000_wide[["date", "S&P 500", "MC", "EW", "MC (UCITS)"]]
        .sort_values("date")
        .reset_index(drop=True)
        .copy()
    )
    for index_name in DRAWDOWN_INDEX_ORDER:
        running_peak = absolute_drawdown_daily[index_name].cummax()
        absolute_drawdown_daily[index_name] = (
            absolute_drawdown_daily[index_name] / running_peak - 1
        ) * 100
    absolute_drawdown_daily = absolute_drawdown_daily.rename(columns={"date": "Date"})
    summary_rows = []
    for index_name in DRAWDOWN_INDEX_ORDER:
        frame = (
            growth_1000_wide[["date", index_name]].sort_values("date").reset_index(drop=True).copy()
        )
        frame["running_peak"] = frame[index_name].cummax()
        frame["drawdown"] = frame[index_name] / frame["running_peak"] - 1
        trough_idx = frame["drawdown"].idxmin()
        trough_date = frame.loc[trough_idx, "date"]
        max_drawdown = frame.loc[trough_idx, "drawdown"]
        peak_level = frame.loc[trough_idx, "running_peak"]
        peak_candidates = frame.loc[:trough_idx]
        peak_date = peak_candidates.loc[
            np.isclose(peak_candidates[index_name], peak_level, atol=TOLERANCE, rtol=0),
            "date",
        ].iloc[-1]
        recovery_candidates = frame.loc[
            (frame["date"] > trough_date) & (frame[index_name] >= peak_level - TOLERANCE)
        ]
        if recovery_candidates.empty:
            recovery_date = pd.NaT
        else:
            recovery_date = recovery_candidates["date"].iloc[0]
        summary_rows.append(
            {
                "index": index_name,
                "max_loss_pct": max_drawdown * 100,
                "peak": peak_date,
                "trough": trough_date,
                "recovery": recovery_date,
            }
        )
    absolute_drawdown_summary = pd.DataFrame(summary_rows)
    if absolute_drawdown_daily[DRAWDOWN_INDEX_ORDER].isna().any().any():
        raise ValueError("Missing values detected in daily drawdown series.")
    if (absolute_drawdown_daily[DRAWDOWN_INDEX_ORDER] > TOLERANCE).any().any():
        raise ValueError("Absolute drawdown cannot be greater than zero.")
    if absolute_drawdown_daily["Date"].duplicated().any():
        raise ValueError("Duplicate dates detected in absolute drawdown series.")
    if not absolute_drawdown_daily["Date"].is_monotonic_increasing:
        raise ValueError("Absolute drawdown dates are not sorted.")
    if (absolute_drawdown_summary["max_loss_pct"] > TOLERANCE).any():
        raise ValueError("Maximum drawdown must be zero or negative.")
    if (absolute_drawdown_summary["peak"] > absolute_drawdown_summary["trough"]).any():
        raise ValueError("Peak date occurs after trough date.")
    recovered = absolute_drawdown_summary["recovery"].notna()
    if (
        absolute_drawdown_summary.loc[recovered, "recovery"]
        < absolute_drawdown_summary.loc[recovered, "trough"]
    ).any():
        raise ValueError("Recovery date occurs before trough date.")
    absolute_drawdown_summary_display = absolute_drawdown_summary.copy()
    absolute_drawdown_summary_display["Max Loss"] = absolute_drawdown_summary_display[
        "max_loss_pct"
    ].map(lambda x: f"{x:.1f}%")
    for column in ["peak", "trough", "recovery"]:
        absolute_drawdown_summary_display[column] = absolute_drawdown_summary_display[column].apply(
            lambda x: x.strftime("%b %d, %Y") if pd.notna(x) else "Not recovered"
        )
    absolute_drawdown_summary_display = absolute_drawdown_summary_display[
        ["index", "Max Loss", "peak", "trough", "recovery"]
    ].rename(
        columns={
            "index": "Index",
            "peak": "Peak",
            "trough": "Trough",
            "recovery": "Recovery",
        }
    )
    return (absolute_drawdown_daily, absolute_drawdown_summary)
