"""Market Data: factors."""

from __future__ import annotations

import pandas as pd

from ..config import MarketDataConfig
from .french import clean_french_return, extract_french_table


def calculate_factors(ff3_raw_text_input, *, config: MarketDataConfig):
    """Calculate factors with explicit inputs; preserve legacy conventions."""
    BACKTEST_END_DATE = config.backtest_end_date
    BACKTEST_START_DATE = config.backtest_start_date
    ff3_raw_text = ff3_raw_text_input
    ff3_source = extract_french_table(
        raw_text=ff3_raw_text,
        date_pattern="\\d{6}",
        required_columns=["Mkt-RF", "SMB", "HML", "RF"],
    )
    ff3_source["month_end"] = pd.PeriodIndex(
        ff3_source["date_code"].astype(str).str.strip(), freq="M"
    ).to_timestamp("M")
    fama_french_3_monthly = pd.DataFrame(
        {
            "month_end": ff3_source["month_end"],
            "mkt_rf": clean_french_return(ff3_source["Mkt-RF"]),
            "smb": clean_french_return(ff3_source["SMB"]),
            "hml": clean_french_return(ff3_source["HML"]),
            "rf": clean_french_return(ff3_source["RF"]),
        }
    )
    fama_french_3_monthly = (
        fama_french_3_monthly[
            (fama_french_3_monthly["month_end"] >= BACKTEST_START_DATE)
            & (fama_french_3_monthly["month_end"] <= BACKTEST_END_DATE)
        ]
        .sort_values("month_end")
        .reset_index(drop=True)
    )
    return (fama_french_3_monthly,)


def prepare_fama_french_5_monthly(ff5_raw_text_input, *, config: MarketDataConfig):
    """Calculate factors with explicit inputs; preserve legacy conventions."""
    BACKTEST_END_DATE = config.backtest_end_date
    BACKTEST_START_DATE = config.backtest_start_date
    ff5_raw_text = ff5_raw_text_input
    ff5_source = extract_french_table(
        raw_text=ff5_raw_text,
        date_pattern="\\d{6}",
        required_columns=["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"],
    )
    ff5_source["month_end"] = pd.PeriodIndex(
        ff5_source["date_code"].astype(str).str.strip(), freq="M"
    ).to_timestamp("M")
    fama_french_5_monthly = pd.DataFrame(
        {
            "month_end": ff5_source["month_end"],
            "mkt_rf": clean_french_return(ff5_source["Mkt-RF"]),
            "smb": clean_french_return(ff5_source["SMB"]),
            "hml": clean_french_return(ff5_source["HML"]),
            "rmw": clean_french_return(ff5_source["RMW"]),
            "cma": clean_french_return(ff5_source["CMA"]),
            "rf": clean_french_return(ff5_source["RF"]),
        }
    )
    fama_french_5_monthly = (
        fama_french_5_monthly[
            (fama_french_5_monthly["month_end"] >= BACKTEST_START_DATE)
            & (fama_french_5_monthly["month_end"] <= BACKTEST_END_DATE)
        ]
        .sort_values("month_end")
        .reset_index(drop=True)
    )
    return (fama_french_5_monthly,)


def prepare_fama_french_5_momentum_monthly(
    fama_french_5_monthly, momentum_raw_text_input, *, config: MarketDataConfig
):
    """Calculate factors with explicit inputs; preserve legacy conventions."""
    BACKTEST_END_DATE = config.backtest_end_date
    BACKTEST_START_DATE = config.backtest_start_date
    momentum_raw_text = momentum_raw_text_input
    momentum_source = extract_french_table(
        raw_text=momentum_raw_text, date_pattern="\\d{6}", required_columns=["Mom"]
    )
    momentum_source["month_end"] = pd.PeriodIndex(
        momentum_source["date_code"].astype(str).str.strip(), freq="M"
    ).to_timestamp("M")
    fama_french_momentum_monthly = pd.DataFrame(
        {
            "month_end": momentum_source["month_end"],
            "mom": clean_french_return(momentum_source["Mom"]),
        }
    )
    fama_french_momentum_monthly = (
        fama_french_momentum_monthly[
            (fama_french_momentum_monthly["month_end"] >= BACKTEST_START_DATE)
            & (fama_french_momentum_monthly["month_end"] <= BACKTEST_END_DATE)
        ]
        .sort_values("month_end")
        .reset_index(drop=True)
    )
    fama_french_5_momentum_monthly = (
        fama_french_5_monthly.merge(
            fama_french_momentum_monthly,
            on="month_end",
            how="inner",
            validate="one_to_one",
        )[["month_end", "mkt_rf", "smb", "hml", "rmw", "cma", "mom", "rf"]]
        .sort_values("month_end")
        .reset_index(drop=True)
    )
    return (fama_french_5_momentum_monthly, fama_french_momentum_monthly)
