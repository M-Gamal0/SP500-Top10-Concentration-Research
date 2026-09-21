"""Analytics: calendar returns."""

from __future__ import annotations

import numpy as np

from ..config import AnalyticsConfig


def calculate_calendar_returns(growth_1000_wide, *, config: AnalyticsConfig):
    """Calculate calendar returns with explicit inputs; preserve legacy conventions."""
    A5_INDEX_ORDER = config.a5_index_order
    a5_levels = (
        growth_1000_wide[["date", "S&P 500", "MC", "EW", "MC (UCITS)"]]
        .sort_values("date")
        .reset_index(drop=True)
        .copy()
    )
    a5_daily_returns = a5_levels.set_index("date")[A5_INDEX_ORDER].pct_change()
    calendar_year_returns_raw = (1 + a5_daily_returns).groupby(a5_daily_returns.index.year).prod(
        min_count=1
    ) - 1
    calendar_year_returns_raw = calendar_year_returns_raw.dropna(how="all")
    year_end_levels = (
        a5_levels.assign(year=lambda x: x["date"].dt.year).groupby("year")[A5_INDEX_ORDER].last()
    )
    year_end_return_check = year_end_levels.pct_change()
    common_check_years = calendar_year_returns_raw.index.intersection(
        year_end_return_check.dropna(how="all").index
    )
    if not np.allclose(
        calendar_year_returns_raw.loc[common_check_years, A5_INDEX_ORDER],
        year_end_return_check.loc[common_check_years, A5_INDEX_ORDER],
        atol=1e-12,
        rtol=0,
    ):
        raise ValueError("Calendar-year return reconciliation failed.")
    first_level_date = a5_levels["date"].min()
    last_level_date = a5_levels["date"].max()
    first_return_year = int(calendar_year_returns_raw.index.min())
    last_return_year = int(calendar_year_returns_raw.index.max())
    partial_years = set()
    if first_level_date.year == first_return_year:
        partial_years.add(first_return_year)
    if last_level_date.year == last_return_year and last_level_date.month < 12:
        partial_years.add(last_return_year)
    calendar_year_returns = (
        calendar_year_returns_raw.mul(100)
        .reset_index()
        .rename(columns={"date": "Year", "year": "Year", "S&P 500": "S&P 500 TR"})
    )
    calendar_year_returns = calendar_year_returns.rename(
        columns={calendar_year_returns.columns[0]: "Year"}
    )
    calendar_year_returns["Year"] = (
        calendar_year_returns["Year"]
        .astype(int)
        .map(lambda year: f"{year}*" if year in partial_years else str(year))
    )
    calendar_year_returns = calendar_year_returns[
        ["Year", "S&P 500 TR", "MC", "EW", "MC (UCITS)"]
    ].copy()
    calendar_year_returns[["S&P 500 TR", "MC", "EW", "MC (UCITS)"]] = calendar_year_returns[
        ["S&P 500 TR", "MC", "EW", "MC (UCITS)"]
    ].round(2)
    if calendar_year_returns["Year"].duplicated().any():
        raise ValueError("Duplicate calendar years detected.")
    if calendar_year_returns[["S&P 500 TR", "MC", "EW", "MC (UCITS)"]].isna().any().any():
        raise ValueError("Missing calendar-year return detected.")
    return (calendar_year_returns,)
