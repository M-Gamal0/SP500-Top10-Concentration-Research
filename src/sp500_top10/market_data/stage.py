"""Orchestrate market data without notebook execution."""

from __future__ import annotations

from pathlib import Path

from ..config import MarketDataConfig
from ..data.results import StageResult
from .benchmarks import calculate_benchmarks
from .calendar import calculate_calendar
from .factors import (
    calculate_factors,
    prepare_fama_french_5_momentum_monthly,
    prepare_fama_french_5_monthly,
)
from .fetch import (
    fetch_benchmarks_yahoo_data,
    fetch_factors_ff3_raw_text,
    fetch_factors_ff5_raw_text,
    fetch_factors_momentum_raw_text,
    fetch_risk_free_risk_free_raw,
    fetch_style_style_daily_raw_text,
    fetch_style_style_monthly_raw_text,
)
from .queries import load_calendar_backtest_calendar
from .risk_free import calculate_risk_free
from .style import calculate_style, prepare_fama_french_style_monthly
from .validation import calculate_validation


def run(repository, config: MarketDataConfig, *, raw_dir: Path | None = None) -> StageResult:
    backtest_calendar_input = load_calendar_backtest_calendar(repository, config=config)
    (backtest_calendar,) = calculate_calendar(backtest_calendar_input, config=config)
    yahoo_data_input = fetch_benchmarks_yahoo_data(config=config, raw_dir=raw_dir)
    (benchmark_daily,) = calculate_benchmarks(yahoo_data_input, config=config)
    risk_free_raw_input = fetch_risk_free_risk_free_raw(config=config, raw_dir=raw_dir)
    risk_free_aligned, risk_free_daily = calculate_risk_free(
        backtest_calendar, risk_free_raw_input, config=config
    )
    ff3_raw_text_input = fetch_factors_ff3_raw_text(config=config, raw_dir=raw_dir)
    (fama_french_3_monthly,) = calculate_factors(ff3_raw_text_input, config=config)
    ff5_raw_text_input = fetch_factors_ff5_raw_text(config=config, raw_dir=raw_dir)
    (fama_french_5_monthly,) = prepare_fama_french_5_monthly(ff5_raw_text_input, config=config)
    momentum_raw_text_input = fetch_factors_momentum_raw_text(config=config, raw_dir=raw_dir)
    fama_french_5_momentum_monthly, fama_french_momentum_monthly = (
        prepare_fama_french_5_momentum_monthly(
            fama_french_5_monthly, momentum_raw_text_input, config=config
        )
    )
    style_monthly_raw_text_input = fetch_style_style_monthly_raw_text(
        config=config, raw_dir=raw_dir
    )
    (fama_french_style_monthly,) = prepare_fama_french_style_monthly(
        style_monthly_raw_text_input, config=config
    )
    style_daily_raw_text_input = fetch_style_style_daily_raw_text(config=config, raw_dir=raw_dir)
    (fama_french_style_daily,) = calculate_style(style_daily_raw_text_input, config=config)
    calculate_validation(
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
        config=config,
    )
    return StageResult(
        tables={
            "benchmark_daily": benchmark_daily,
            "risk_free_daily": risk_free_daily,
            "fama_french_3_monthly": fama_french_3_monthly,
            "fama_french_5_momentum_monthly": fama_french_5_momentum_monthly,
            "fama_french_style_monthly": fama_french_style_monthly,
            "fama_french_style_daily": fama_french_style_daily,
        },
        csvs={},
    )
