"""Market Data: validation."""

from __future__ import annotations

from ..config import MarketDataConfig


def calculate_validation(
    backtest_calendar,
    benchmark_daily,
    fama_french_3_monthly,
    fama_french_5_momentum_monthly,
    fama_french_5_monthly,
    fama_french_momentum_monthly,
    fama_french_style_daily,
    fama_french_style_monthly,
    risk_free_aligned,
    risk_free_daily,
    *,
    config: MarketDataConfig,
):
    """Calculate validation with explicit inputs; preserve legacy conventions."""
    BACKTEST_END_DATE = config.backtest_end_date
    BACKTEST_START_DATE = config.backtest_start_date
    BENCHMARK_TICKERS = config.benchmark_tickers
    TRADING_DAYS_PER_YEAR = config.trading_days_per_year
    if not backtest_calendar["date"].is_unique:
        raise ValueError("Validation failed: backtest_calendar['date'].is_unique")
    if not backtest_calendar["date"].min() == BACKTEST_START_DATE:
        raise ValueError(
            "Validation failed: backtest_calendar['date'].min() == BACKTEST_START_DATE"
        )
    if not backtest_calendar["date"].max() == BACKTEST_END_DATE:
        raise ValueError("Validation failed: backtest_calendar['date'].max() == BACKTEST_END_DATE")
    canonical_dates = set(backtest_calendar["date"])
    if not set(benchmark_daily["ticker"].unique()) == set(BENCHMARK_TICKERS):
        raise ValueError(
            "Validation failed: set(benchmark_daily['ticker'].unique()) == set(BENCHMARK_TICKERS)"
        )
    if not not benchmark_daily.duplicated(["date", "ticker"]).any():
        raise ValueError(
            "Validation failed: not benchmark_daily.duplicated(['date', 'ticker']).any()"
        )
    if not benchmark_daily["benchmark_type"].notna().all():
        raise ValueError("Validation failed: benchmark_daily['benchmark_type'].notna().all()")
    if not benchmark_daily["close"].notna().all():
        raise ValueError("Validation failed: benchmark_daily['close'].notna().all()")
    if (
        not benchmark_daily.groupby("ticker")["daily_return"]
        .apply(lambda x: x.isna().sum())
        .eq(1)
        .all()
    ):
        raise ValueError(
            "Validation failed: benchmark_daily.groupby('ticker')['daily_return'].apply(lambda x: x.isna().sum()).eq(1).all()"
        )
    for ticker in BENCHMARK_TICKERS:
        ticker_dates = set(benchmark_daily.loc[benchmark_daily["ticker"] == ticker, "date"])
        if not ticker_dates == canonical_dates:
            raise ValueError("Validation failed: ticker_dates == canonical_dates")
    if not not risk_free_daily.duplicated("date").any():
        raise ValueError("Validation failed: not risk_free_daily.duplicated('date').any()")
    if not set(risk_free_daily["date"]) == canonical_dates:
        raise ValueError("Validation failed: set(risk_free_daily['date']) == canonical_dates")
    if not risk_free_daily["annual_rate_percent"].notna().all():
        raise ValueError("Validation failed: risk_free_daily['annual_rate_percent'].notna().all()")
    if not risk_free_daily["daily_risk_free_return"].notna().all():
        raise ValueError(
            "Validation failed: risk_free_daily['daily_risk_free_return'].notna().all()"
        )
    if not (risk_free_aligned["observation_date"] <= risk_free_aligned["date"]).all():
        raise ValueError(
            "Validation failed: (risk_free_aligned['observation_date'] <= risk_free_aligned['date']).all()"
        )
    if not not fama_french_3_monthly.duplicated("month_end").any():
        raise ValueError(
            "Validation failed: not fama_french_3_monthly.duplicated('month_end').any()"
        )
    if not fama_french_3_monthly[["mkt_rf", "smb", "hml", "rf"]].notna().all().all():
        raise ValueError(
            "Validation failed: fama_french_3_monthly[['mkt_rf', 'smb', 'hml', 'rf']].notna().all().all()"
        )
    if not fama_french_3_monthly["month_end"].is_monotonic_increasing:
        raise ValueError(
            "Validation failed: fama_french_3_monthly['month_end'].is_monotonic_increasing"
        )
    if not fama_french_3_monthly["month_end"].min() >= BACKTEST_START_DATE:
        raise ValueError(
            "Validation failed: fama_french_3_monthly['month_end'].min() >= BACKTEST_START_DATE"
        )
    if not fama_french_3_monthly["month_end"].max() <= BACKTEST_END_DATE:
        raise ValueError(
            "Validation failed: fama_french_3_monthly['month_end'].max() <= BACKTEST_END_DATE"
        )
    if not not fama_french_5_monthly.duplicated("month_end").any():
        raise ValueError(
            "Validation failed: not fama_french_5_monthly.duplicated('month_end').any()"
        )
    if not not fama_french_momentum_monthly.duplicated("month_end").any():
        raise ValueError(
            "Validation failed: not fama_french_momentum_monthly.duplicated('month_end').any()"
        )
    if not not fama_french_5_momentum_monthly.duplicated("month_end").any():
        raise ValueError(
            "Validation failed: not fama_french_5_momentum_monthly.duplicated('month_end').any()"
        )
    if not fama_french_5_monthly[["mkt_rf", "smb", "hml", "rmw", "cma", "rf"]].notna().all().all():
        raise ValueError(
            "Validation failed: fama_french_5_monthly[['mkt_rf', 'smb', 'hml', 'rmw', 'cma', 'rf']].notna().all().all()"
        )
    if not fama_french_momentum_monthly[["mom"]].notna().all().all():
        raise ValueError(
            "Validation failed: fama_french_momentum_monthly[['mom']].notna().all().all()"
        )
    if (
        not fama_french_5_momentum_monthly[["mkt_rf", "smb", "hml", "rmw", "cma", "mom", "rf"]]
        .notna()
        .all()
        .all()
    ):
        raise ValueError(
            "Validation failed: fama_french_5_momentum_monthly[['mkt_rf', 'smb', 'hml', 'rmw', 'cma', 'mom', 'rf']].notna().all().all()"
        )
    if not fama_french_5_monthly["month_end"].is_monotonic_increasing:
        raise ValueError(
            "Validation failed: fama_french_5_monthly['month_end'].is_monotonic_increasing"
        )
    if not fama_french_momentum_monthly["month_end"].is_monotonic_increasing:
        raise ValueError(
            "Validation failed: fama_french_momentum_monthly['month_end'].is_monotonic_increasing"
        )
    if not fama_french_5_momentum_monthly["month_end"].is_monotonic_increasing:
        raise ValueError(
            "Validation failed: fama_french_5_momentum_monthly['month_end'].is_monotonic_increasing"
        )
    if not fama_french_5_momentum_monthly["month_end"].min() >= BACKTEST_START_DATE:
        raise ValueError(
            "Validation failed: fama_french_5_momentum_monthly['month_end'].min() >= BACKTEST_START_DATE"
        )
    if not fama_french_5_momentum_monthly["month_end"].max() <= BACKTEST_END_DATE:
        raise ValueError(
            "Validation failed: fama_french_5_momentum_monthly['month_end'].max() <= BACKTEST_END_DATE"
        )
    if not len(fama_french_5_momentum_monthly) >= 120:
        raise ValueError("Validation failed: len(fama_french_5_momentum_monthly) >= 120")
    if not not fama_french_style_monthly.duplicated("month_end").any():
        raise ValueError(
            "Validation failed: not fama_french_style_monthly.duplicated('month_end').any()"
        )
    if not not fama_french_style_daily.duplicated("date").any():
        raise ValueError("Validation failed: not fama_french_style_daily.duplicated('date').any()")
    if not fama_french_style_monthly[["big_growth_return", "big_value_return"]].notna().all().all():
        raise ValueError(
            "Validation failed: fama_french_style_monthly[['big_growth_return', 'big_value_return']].notna().all().all()"
        )
    if not fama_french_style_daily[["big_growth_return", "big_value_return"]].notna().all().all():
        raise ValueError(
            "Validation failed: fama_french_style_daily[['big_growth_return', 'big_value_return']].notna().all().all()"
        )
    if not fama_french_style_monthly["month_end"].is_monotonic_increasing:
        raise ValueError(
            "Validation failed: fama_french_style_monthly['month_end'].is_monotonic_increasing"
        )
    if not fama_french_style_daily["date"].is_monotonic_increasing:
        raise ValueError(
            "Validation failed: fama_french_style_daily['date'].is_monotonic_increasing"
        )
    if not fama_french_style_monthly["month_end"].min() >= BACKTEST_START_DATE:
        raise ValueError(
            "Validation failed: fama_french_style_monthly['month_end'].min() >= BACKTEST_START_DATE"
        )
    if not fama_french_style_monthly["month_end"].max() <= BACKTEST_END_DATE:
        raise ValueError(
            "Validation failed: fama_french_style_monthly['month_end'].max() <= BACKTEST_END_DATE"
        )
    if not fama_french_style_daily["date"].min() >= BACKTEST_START_DATE:
        raise ValueError(
            "Validation failed: fama_french_style_daily['date'].min() >= BACKTEST_START_DATE"
        )
    if not fama_french_style_daily["date"].max() <= BACKTEST_END_DATE:
        raise ValueError(
            "Validation failed: fama_french_style_daily['date'].max() <= BACKTEST_END_DATE"
        )
    daily_style_overlap = set(fama_french_style_daily["date"]) & canonical_dates
    if not len(daily_style_overlap) >= TRADING_DAYS_PER_YEAR:
        raise ValueError("Validation failed: len(daily_style_overlap) >= TRADING_DAYS_PER_YEAR")
    return ()
