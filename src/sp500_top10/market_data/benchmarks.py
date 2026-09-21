"""Market Data: benchmarks."""

from __future__ import annotations

from ..config import MarketDataConfig


def calculate_benchmarks(yahoo_data_input, *, config: MarketDataConfig):
    """Calculate benchmarks with explicit inputs; preserve legacy conventions."""
    BENCHMARK_TYPES = config.benchmark_types
    yahoo_data = yahoo_data_input
    benchmark_daily = yahoo_data[["date", "ticker", "close"]].copy()
    benchmark_daily["benchmark_type"] = benchmark_daily["ticker"].map(BENCHMARK_TYPES)
    if benchmark_daily["benchmark_type"].isna().any():
        unknown_tickers = (
            benchmark_daily.loc[benchmark_daily["benchmark_type"].isna(), "ticker"]
            .unique()
            .tolist()
        )
        raise ValueError(f"Unknown benchmark tickers: {unknown_tickers}")
    benchmark_daily = benchmark_daily.sort_values(["ticker", "date"]).reset_index(drop=True)
    benchmark_daily["daily_return"] = benchmark_daily.groupby("ticker")["close"].pct_change(
        fill_method=None
    )
    benchmark_daily = benchmark_daily[["date", "ticker", "benchmark_type", "close", "daily_return"]]
    return (benchmark_daily,)
