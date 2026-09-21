"""Market Data: fetch."""

from __future__ import annotations

from pathlib import Path

from ..config import MarketDataConfig
from .fred import download_fred_series
from .french import download_french_zip_csv
from .yahoo import download_yahoo_data


def fetch_benchmarks_yahoo_data(*, config: MarketDataConfig, raw_dir: Path | None = None):
    """Load benchmarks with explicit inputs; preserve legacy conventions."""
    BACKTEST_START_DATE = config.backtest_start_date
    BENCHMARK_TICKERS = config.benchmark_tickers
    YAHOO_DOWNLOAD_END_DATE = config.yahoo_download_end_date
    return download_yahoo_data(
        tickers=BENCHMARK_TICKERS,
        start_date=BACKTEST_START_DATE,
        end_date=YAHOO_DOWNLOAD_END_DATE,
        raw_dir=raw_dir,
    )


def fetch_risk_free_risk_free_raw(*, config: MarketDataConfig, raw_dir: Path | None = None):
    """Load risk free with explicit inputs; preserve legacy conventions."""
    RISK_FREE_DOWNLOAD_END_DATE = config.risk_free_download_end_date
    RISK_FREE_DOWNLOAD_START_DATE = config.risk_free_download_start_date
    RISK_FREE_SERIES = config.risk_free_series
    return download_fred_series(
        series_id=RISK_FREE_SERIES,
        start_date=RISK_FREE_DOWNLOAD_START_DATE,
        end_date=RISK_FREE_DOWNLOAD_END_DATE,
        config=config,
        raw_dir=raw_dir,
    )


def fetch_factors_ff3_raw_text(*, config: MarketDataConfig, raw_dir: Path | None = None):
    """Load factors with explicit inputs; preserve legacy conventions."""
    FRENCH_FF3_MONTHLY_URL = config.french_ff3_monthly_url
    return download_french_zip_csv(FRENCH_FF3_MONTHLY_URL, raw_dir=raw_dir)


def fetch_factors_ff5_raw_text(*, config: MarketDataConfig, raw_dir: Path | None = None):
    """Load factors with explicit inputs; preserve legacy conventions."""
    FRENCH_FF5_MONTHLY_URL = config.french_ff5_monthly_url
    return download_french_zip_csv(FRENCH_FF5_MONTHLY_URL, raw_dir=raw_dir)


def fetch_factors_momentum_raw_text(*, config: MarketDataConfig, raw_dir: Path | None = None):
    """Load factors with explicit inputs; preserve legacy conventions."""
    FRENCH_MOMENTUM_MONTHLY_URL = config.french_momentum_monthly_url
    return download_french_zip_csv(FRENCH_MOMENTUM_MONTHLY_URL, raw_dir=raw_dir)


def fetch_style_style_monthly_raw_text(*, config: MarketDataConfig, raw_dir: Path | None = None):
    """Load style with explicit inputs; preserve legacy conventions."""
    FRENCH_6_PORTFOLIOS_MONTHLY_URL = config.french_6_portfolios_monthly_url
    return download_french_zip_csv(FRENCH_6_PORTFOLIOS_MONTHLY_URL, raw_dir=raw_dir)


def fetch_style_style_daily_raw_text(*, config: MarketDataConfig, raw_dir: Path | None = None):
    """Load style with explicit inputs; preserve legacy conventions."""
    FRENCH_6_PORTFOLIOS_DAILY_URL = config.french_6_portfolios_daily_url
    return download_french_zip_csv(FRENCH_6_PORTFOLIOS_DAILY_URL, raw_dir=raw_dir)
