"""Central defaults and portable, validated runtime configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ConstructionConfig:
    """Current construction calculation settings; defaults preserve notebook behavior."""

    input_table: str = "quarterly_company_universe"
    output_table: str = "quarterly_index_weights"
    core_top_n: int = 10
    robustness_top_n: int = 20
    dominant_cap: float = 0.18
    other_cap: float = 0.18
    weight_tolerance: float = 1e-10


@dataclass(frozen=True)
class BacktestingConfig:
    """Current backtesting calculation settings; defaults preserve notebook behavior."""

    input_table: str = "quarterly_index_weights"
    output_tables: dict = field(
        default_factory=lambda: {
            "daily_index": "backtest_daily_index",
            "daily_weights": "backtest_daily_weights",
            "rebalance_events": "backtest_rebalance_events",
            "turnover": "backtest_turnover",
            "monthly_reviews": "backtest_monthly_reviews",
        }
    )
    core_top_n: int = 10
    robustness_top_n: int = 20
    core_weighting_methods: list = field(
        default_factory=lambda: ["market_cap", "equal_weight", "buffered_20"]
    )

    @property
    def portfolio_specs(self):
        return [
            (self.core_top_n, "market_cap"),
            (self.core_top_n, "equal_weight"),
            (self.core_top_n, "buffered_20"),
            (self.robustness_top_n, "market_cap"),
        ]

    initial_index_value: float = 1000.0
    backtest_end_date: pd.Timestamp = field(default_factory=lambda: pd.Timestamp("2026-08-31"))
    calendar_coverage_threshold: float = 0.9
    dominant_breach: float = 0.2
    other_breach: float = 0.2
    dominant_cap: float = 0.18
    other_cap: float = 0.18
    validation_tolerance: float = 1e-10

    @property
    def max_required_top_n(self):
        return max((top_n for top_n, _ in self.portfolio_specs))


@dataclass(frozen=True)
class MarketDataConfig:
    """Current market_data calculation settings; defaults preserve notebook behavior."""

    backtest_start_date: pd.Timestamp = field(default_factory=lambda: pd.Timestamp("1998-12-31"))
    backtest_end_date: pd.Timestamp = field(default_factory=lambda: pd.Timestamp("2026-08-31"))
    benchmark_tickers: list = field(default_factory=lambda: ["^GSPC", "^SP500TR"])
    benchmark_types: dict = field(
        default_factory=lambda: {"^GSPC": "PR_index", "^SP500TR": "TR_index"}
    )

    @property
    def yahoo_download_end_date(self):
        return self.backtest_end_date + pd.Timedelta(days=1)

    risk_free_series: str = "DGS3MO"

    @property
    def risk_free_download_start_date(self):
        return self.backtest_start_date - pd.Timedelta(days=30)

    @property
    def risk_free_download_end_date(self):
        return self.backtest_end_date

    trading_days_per_year: int = 252
    fred_csv_url_template: str = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    french_ff3_monthly_url: str = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip"
    french_ff5_monthly_url: str = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip"
    french_momentum_monthly_url: str = (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip"
    )
    french_6_portfolios_monthly_url: str = (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/6_Portfolios_2x3_CSV.zip"
    )
    french_6_portfolios_daily_url: str = (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/6_Portfolios_2x3_daily_CSV.zip"
    )


@dataclass(frozen=True)
class AnalyticsConfig:
    """Current analytics calculation settings; defaults preserve notebook behavior."""

    core_top_n: int = 10
    tolerance: float = 1e-10
    slide8_dates: dict = field(
        default_factory=lambda: {
            pd.Timestamp("1998-12-31"): "Dec 31, 1998",
            pd.Timestamp("2026-08-31"): "Aug 31, 2026",
        }
    )
    slide9_method_labels: dict = field(
        default_factory=lambda: {
            "market_cap": "MC",
            "equal_weight": "EW",
            "buffered_20": "MC (UCITS)",
        }
    )
    slide9_index_order: list = field(default_factory=lambda: ["S&P 500", "MC", "EW", "MC (UCITS)"])
    period_months: dict = field(
        default_factory=lambda: {
            "1 Year": 12,
            "3 Years": 36,
            "5 Years": 60,
            "10 Years": 120,
            "Full Period": None,
        }
    )
    rolling_horizons: dict = field(default_factory=lambda: {60: "5-Year", 120: "10-Year"})
    rolling_strategies: list = field(default_factory=lambda: ["MC", "EW", "MC (UCITS)"])
    strategy_y_position: dict = field(default_factory=lambda: {"MC": 3, "EW": 2, "MC (UCITS)": 1})
    rolling_months: int = 60
    drawdown_index_order: list = field(
        default_factory=lambda: ["S&P 500", "MC", "EW", "MC (UCITS)"]
    )
    relative_strategies: list = field(default_factory=lambda: ["MC", "EW", "MC (UCITS)"])
    period_analysis_index_order: list = field(
        default_factory=lambda: ["S&P 500", "MC", "EW", "MC (UCITS)"]
    )
    market_down_threshold: object = field(default_factory=lambda: -0.02)
    market_up_threshold: float = 0.02
    style_value_threshold: object = field(default_factory=lambda: -0.01)
    style_growth_threshold: float = 0.01
    market_state_order: list = field(
        default_factory=lambda: ["Market Up", "Market Neutral", "Market Down"]
    )
    style_state_order: list = field(
        default_factory=lambda: ["Value-Led", "Neutral Style", "Growth-Led"]
    )
    state_strategies: list = field(default_factory=lambda: ["MC", "EW", "MC (UCITS)"])
    state_order: list = field(
        default_factory=lambda: [
            ("Market Up", "Value-Led"),
            ("Market Up", "Neutral Style"),
            ("Market Up", "Growth-Led"),
            ("Market Neutral", "Value-Led"),
            ("Market Neutral", "Neutral Style"),
            ("Market Neutral", "Growth-Led"),
            ("Market Down", "Value-Led"),
            ("Market Down", "Neutral Style"),
            ("Market Down", "Growth-Led"),
        ]
    )
    ff3_window_months: int = 36
    ff3_hac_lags: int = 3
    factor_portfolios: list = field(default_factory=lambda: ["MC", "S&P 500"])
    construction_methods: dict = field(
        default_factory=lambda: {
            "market_cap": "MC",
            "equal_weight": "EW",
            "buffered_20": "MC (UCITS)",
        }
    )
    construction_order: list = field(default_factory=lambda: ["MC", "EW", "MC (UCITS)"])
    cost_scenarios_bps: object = field(default_factory=lambda: list(range(0, 51, 5)))
    cost_methods: dict = field(
        default_factory=lambda: {
            "market_cap": "MC",
            "equal_weight": "EW",
            "buffered_20": "MC (UCITS)",
        }
    )
    cost_strategy_order: list = field(default_factory=lambda: ["MC", "EW", "MC (UCITS)"])
    robustness_top_ns: dict = field(default_factory=lambda: {10: "Top 10 MC", 20: "Top 20 MC"})
    robustness_order: list = field(default_factory=lambda: ["Top 10 MC", "Top 20 MC", "S&P 500"])
    rolling_win_months: int = 60
    attribution_top_n: int = 10
    attribution_method: str = "market_cap"
    attribution_tolerance: float = 1e-10
    a1_index_order: list = field(default_factory=lambda: ["S&P 500", "MC", "EW", "MC (UCITS)"])
    trading_days_per_year: int = 252
    a1_metrics: list = field(
        default_factory=lambda: [
            ("Cumulative Return", "cumulative_return"),
            ("CAGR", "cagr"),
            ("Annualized Volatility", "annualized_volatility"),
            ("Sharpe Ratio", "sharpe_ratio"),
            ("Sortino Ratio", "sortino_ratio"),
            ("Calmar Ratio", "calmar_ratio"),
            ("Max Drawdown", "max_drawdown"),
            ("Beta vs. S&P 500", "beta_vs_sp500"),
            ("CAPM Alpha", "capm_alpha"),
            ("Tracking Error", "tracking_error"),
            ("Information Ratio", "information_ratio"),
            ("Correlation vs. S&P 500", "correlation_vs_sp500"),
            ("Up Capture vs. S&P 500", "up_capture"),
            ("Down Capture vs. S&P 500", "down_capture"),
            ("Daily Return Skewness", "daily_return_skewness"),
            ("Daily Excess Kurtosis", "daily_excess_kurtosis"),
        ]
    )
    percent_metrics: set = field(
        default_factory=lambda: {
            "Cumulative Return",
            "CAGR",
            "Annualized Volatility",
            "Max Drawdown",
            "CAPM Alpha",
            "Tracking Error",
        }
    )
    capture_metrics: set = field(
        default_factory=lambda: {"Up Capture vs. S&P 500", "Down Capture vs. S&P 500"}
    )
    a5_index_order: list = field(default_factory=lambda: ["S&P 500", "MC", "EW", "MC (UCITS)"])
    concentration_start_date: pd.Timestamp = field(
        default_factory=lambda: pd.Timestamp("1998-12-31")
    )
    historical_periods: list = field(
        default_factory=lambda: [
            [1, "Drawdown", "1999-07-16", "1999-10-15", "1999 Fed Tightening / Inflation Scare"],
            [2, "Recovery", "1999-10-15", "1999-11-16", "Late-1999 Recovery Rally"],
            [3, "Drawdown", "2000-09-01", "2002-10-09", "Dot-Com Bust"],
            [4, "Recovery", "2002-10-09", "2006-10-23", "Post-Dot-Com Recovery"],
            [5, "Drawdown", "2007-10-09", "2009-03-09", "Global Financial Crisis"],
            [6, "Recovery", "2009-03-09", "2012-04-02", "Post-GFC Recovery"],
            [7, "Drawdown", "2015-07-20", "2016-02-11", "China & Oil Selloff"],
            [8, "Recovery", "2016-02-11", "2016-04-18", "2016 Risk-On Recovery"],
            [9, "Drawdown", "2018-09-20", "2018-12-24", "Q4 2018 Fed / Trade-War Selloff"],
            [10, "Recovery", "2018-12-24", "2019-04-12", "2019 Fed-Pivot Recovery"],
            [11, "Drawdown", "2020-02-19", "2020-03-23", "COVID-19 Crash"],
            [12, "Recovery", "2020-03-23", "2020-08-10", "Post-COVID Recovery"],
            [
                13,
                "Drawdown",
                "2022-01-03",
                "2022-10-12",
                "2022 Inflation & Fed-Tightening Bear Market",
            ],
            [14, "Recovery", "2022-10-12", "2023-12-13", "2022–23 Disinflation / AI-Led Recovery"],
            [15, "Drawdown", "2025-02-19", "2025-04-08", "2025 Tariff Shock Selloff"],
            [16, "Recovery", "2025-04-08", "2025-06-26", "Post-Tariff Relief Rally"],
        ]
    )


@dataclass(frozen=True)
class FactorsConfig:
    """Current factors calculation settings; defaults preserve notebook behavior."""

    core_top_n: int = 10
    tolerance: float = 1e-10
    exposure_window_months: int = 36
    recent_window_months: int = 120
    rolling_active_window_months: int = 60
    hac_lags: int = 3
    strategy_method_labels: dict = field(
        default_factory=lambda: {
            "market_cap": "MC",
            "equal_weight": "EW",
            "buffered_20": "MC (UCITS)",
        }
    )
    factor_portfolios: list = field(default_factory=lambda: ["MC", "S&P 500"])
    style_leadership_threshold: float = 0.01
    multifactor_factors: list = field(
        default_factory=lambda: ["ff5_mkt_rf", "ff5_smb", "ff5_hml", "rmw", "cma", "mom"]
    )
    multifactor_labels: dict = field(
        default_factory=lambda: {
            "ff5_mkt_rf": "Market",
            "ff5_smb": "SMB",
            "ff5_hml": "HML",
            "rmw": "RMW",
            "cma": "CMA",
            "mom": "Momentum",
        }
    )

    @property
    def model_specs(self):
        return {
            "CAPM": {"factors": ["mkt_rf"], "hml_factor": None, "mom_factor": None},
            "FF3": {"factors": ["mkt_rf", "smb", "hml"], "hml_factor": "hml", "mom_factor": None},
            "FF5": {
                "factors": ["ff5_mkt_rf", "ff5_smb", "ff5_hml", "rmw", "cma"],
                "hml_factor": "ff5_hml",
                "mom_factor": None,
            },
            "FF5 + Momentum": {
                "factors": self.multifactor_factors,
                "hml_factor": "ff5_hml",
                "mom_factor": "mom",
            },
        }

    strategy_active_return_columns: dict = field(
        default_factory=lambda: {
            "MC": "active_return",
            "EW": "ew_active_return",
            "MC (UCITS)": "ucits_active_return",
        }
    )


@dataclass(frozen=True)
class Paths:
    root: Path
    source: Path
    results: Path
    outputs: Path
    cache: Path
    logs: Path


@dataclass(frozen=True)
class Config:
    paths: Paths
    construction: ConstructionConfig = field(default_factory=ConstructionConfig)
    backtesting: BacktestingConfig = field(default_factory=BacktestingConfig)
    market_data: MarketDataConfig = field(default_factory=MarketDataConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    factors: FactorsConfig = field(default_factory=FactorsConfig)

    def validate(self) -> None:
        if self.paths.source.resolve() == self.paths.results.resolve():
            raise ValueError("Source and result databases must differ.")
        if (self.construction.core_top_n, self.construction.robustness_top_n) != (10, 20):
            raise ValueError("The compatible report set currently supports Top 10 and Top 20.")
        if (self.backtesting.core_top_n, self.backtesting.robustness_top_n) != (10, 20):
            raise ValueError("Backtesting must use the same Top 10 / Top 20 portfolios.")
        if self.backtesting.backtest_end_date != self.market_data.backtest_end_date:
            raise ValueError("Backtest and market-data end dates must agree.")
        if self.market_data.backtest_start_date >= self.market_data.backtest_end_date:
            raise ValueError("Start date must precede end date.")
        if not 0 < self.backtesting.calendar_coverage_threshold <= 1:
            raise ValueError("Calendar coverage must be in (0, 1].")
        for name in ["dominant_cap", "other_cap"]:
            cap = getattr(self.construction, name)
            if not 0 < cap <= 1 or cap != getattr(self.backtesting, name):
                raise ValueError("Construction and backtest caps must agree and be in (0, 1].")
        if (
            min(
                self.factors.exposure_window_months,
                self.factors.recent_window_months,
                self.factors.rolling_active_window_months,
            )
            <= 0
        ):
            raise ValueError("Factor windows must be positive.")


def load_config(project_root: Path) -> Config:
    root = project_root.resolve()
    profile = root / ".local/paths.json"
    local = json.loads(profile.read_text(encoding="utf-8")) if profile.exists() else {}
    defaults = {
        "source": "data/sp500.duckdb",
        "results": "data/sp500_results.duckdb",
        "outputs": "outputs",
        "cache": "cache",
        "logs": "logs",
    }
    env = {
        "source": "SP500_SOURCE_DB",
        "results": "SP500_RESULTS_DB",
        "outputs": "SP500_OUTPUT_ROOT",
        "cache": "SP500_CACHE_ROOT",
        "logs": "SP500_LOG_ROOT",
    }
    unknown = set(local) - set(defaults)
    if unknown:
        raise ValueError(f"Unknown local path settings: {sorted(unknown)}")
    values = {}
    for key, default in defaults.items():
        value = Path(os.environ.get(env[key], local.get(key, default))).expanduser()
        values[key] = (root / value).resolve() if not value.is_absolute() else value.resolve()
    config = Config(paths=Paths(root=root, **values))
    config.validate()
    return config
