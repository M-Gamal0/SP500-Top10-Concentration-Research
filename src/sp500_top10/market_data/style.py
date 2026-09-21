"""Market Data: style."""

from __future__ import annotations

import pandas as pd

from ..config import MarketDataConfig
from .french import clean_french_return, extract_french_table


def prepare_fama_french_style_monthly(style_monthly_raw_text_input, *, config: MarketDataConfig):
    """Calculate style with explicit inputs; preserve legacy conventions."""
    BACKTEST_END_DATE = config.backtest_end_date
    BACKTEST_START_DATE = config.backtest_start_date
    style_monthly_raw_text = style_monthly_raw_text_input
    style_monthly_source = extract_french_table(
        raw_text=style_monthly_raw_text,
        date_pattern="\\d{6}",
        required_columns=["BIG LoBM", "BIG HiBM"],
        section_marker="Average Value Weighted Returns -- Monthly",
    )
    style_monthly_source["month_end"] = pd.PeriodIndex(
        style_monthly_source["date_code"].astype(str).str.strip(), freq="M"
    ).to_timestamp("M")
    fama_french_style_monthly = pd.DataFrame(
        {
            "month_end": style_monthly_source["month_end"],
            "big_growth_return": clean_french_return(style_monthly_source["BIG LoBM"]),
            "big_value_return": clean_french_return(style_monthly_source["BIG HiBM"]),
        }
    )
    fama_french_style_monthly = (
        fama_french_style_monthly[
            (fama_french_style_monthly["month_end"] >= BACKTEST_START_DATE)
            & (fama_french_style_monthly["month_end"] <= BACKTEST_END_DATE)
        ]
        .sort_values("month_end")
        .reset_index(drop=True)
    )
    return (fama_french_style_monthly,)


def calculate_style(style_daily_raw_text_input, *, config: MarketDataConfig):
    """Calculate style with explicit inputs; preserve legacy conventions."""
    BACKTEST_END_DATE = config.backtest_end_date
    BACKTEST_START_DATE = config.backtest_start_date
    style_daily_raw_text = style_daily_raw_text_input
    style_daily_source = extract_french_table(
        raw_text=style_daily_raw_text,
        date_pattern="\\d{8}",
        required_columns=["BIG LoBM", "BIG HiBM"],
        section_marker="Average Value Weighted Returns -- Daily",
    )
    style_daily_source["date"] = pd.to_datetime(
        style_daily_source["date_code"].astype(str).str.strip(),
        format="%Y%m%d",
        errors="raise",
    )
    fama_french_style_daily = pd.DataFrame(
        {
            "date": style_daily_source["date"],
            "big_growth_return": clean_french_return(style_daily_source["BIG LoBM"]),
            "big_value_return": clean_french_return(style_daily_source["BIG HiBM"]),
        }
    )
    fama_french_style_daily = (
        fama_french_style_daily[
            (fama_french_style_daily["date"] >= BACKTEST_START_DATE)
            & (fama_french_style_daily["date"] <= BACKTEST_END_DATE)
        ]
        .sort_values("date")
        .reset_index(drop=True)
    )
    return (fama_french_style_daily,)
