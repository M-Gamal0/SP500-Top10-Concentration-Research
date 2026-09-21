"""Create fictional data for the full offline workflow. No paid data is used."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sp500_top10.config import MarketDataConfig
from sp500_top10.market_data.snapshot import save_snapshot


def create(destination: Path, end="2026-08-31") -> Path:
    destination = destination.resolve()
    source = destination / "data/sp500.duckdb"
    if source.exists():
        raise FileExistsError(f"Refusing to replace existing data: {source}")
    source.parent.mkdir(parents=True, exist_ok=True)
    dates = pd.bdate_range("1998-12-31", end)
    rng = np.random.default_rng(410)
    returns = rng.normal(0.0003, 0.011, (len(dates), 20))
    returns[0] = 0
    prices = 100 * np.cumprod(1 + returns, axis=0)
    adjusted = 100 * np.cumprod(
        1 + returns + np.where(np.arange(len(dates))[:, None] == 0, 0, 0.00004), axis=0
    )
    tickers = [f"SYN{i:02}" for i in range(1, 21)]
    stocks = pd.DataFrame(
        {
            "date": np.repeat(dates, 20),
            "ticker": np.tile(tickers, len(dates)),
            "close": prices.reshape(-1),
            "closeadj": adjusted.reshape(-1),
        }
    )
    daily = stocks[["date", "ticker"]].copy()
    shares = np.arange(20, 0, -1) * 1_000_000
    daily["marketcap"] = (prices * shares).reshape(-1)
    selections = pd.date_range("1998-12-31", end, freq="QE-DEC")
    rows = []
    for date in selections:
        position = dates.searchsorted(date, side="right") - 1
        for i, ticker in enumerate(tickers):
            rows.append(
                {
                    "selection_date": date,
                    "ticker": ticker,
                    "name": f"Fictional Company {i + 1}",
                    "resolved_marketcap": float(prices[position, i] * shares[i]),
                    "marketcap_source": "synthetic",
                    "multi_class_company": False,
                }
            )
    universe = pd.DataFrame(rows)
    membership = universe[["selection_date", "ticker", "name"]].rename(
        columns={"selection_date": "date"}
    )
    membership["action"] = "historical"
    metadata = pd.DataFrame(
        {
            "ticker": tickers,
            "sector": ["Synthetic Sector A" if i % 2 else "Synthetic Sector B" for i in range(20)],
            "lastupdated": pd.Timestamp(end),
        }
    )
    with duckdb.connect(str(source)) as connection:
        for name, frame in {
            "quarterly_company_universe": universe,
            "stocks": stocks,
            "daily": daily,
            "sp500": membership,
            "tickers": metadata,
        }.items():
            connection.register("input_frame", frame)
            connection.execute(f'CREATE TABLE "{name}" AS SELECT * FROM input_frame')
            connection.unregister("input_frame")
    benchmark_returns = returns.mean(axis=1) + rng.normal(0, 0.003, len(dates))
    benchmark_returns[0] = 0
    benchmark = []
    for ticker, kind, dividend in [("^GSPC", "PR_index", 0), ("^SP500TR", "TR_index", 0.00004)]:
        ret = benchmark_returns + dividend
        ret[0] = 0
        levels = 1000 * np.cumprod(1 + ret)
        frame = pd.DataFrame(
            {
                "date": dates,
                "ticker": ticker,
                "benchmark_type": kind,
                "close": levels,
                "daily_return": pd.Series(levels).pct_change(),
            }
        )
        benchmark.append(frame)
    risk = pd.DataFrame(
        {
            "date": dates,
            "series_id": "DGS3MO",
            "annual_rate_percent": 3.0,
            "daily_risk_free_return": 0.03 / 252,
        }
    )
    months = pd.date_range("1998-12-31", end, freq="ME")
    values = rng.normal(0.002, 0.025, (len(months), 6))
    ff3 = pd.DataFrame(
        {
            "month_end": months,
            "mkt_rf": values[:, 0],
            "smb": values[:, 1],
            "hml": values[:, 2],
            "rf": 0.0025,
        }
    )
    ff5 = pd.DataFrame(
        {
            "month_end": months,
            "mkt_rf": values[:, 0],
            "smb": values[:, 1],
            "hml": values[:, 2],
            "rmw": values[:, 3],
            "cma": values[:, 4],
            "mom": values[:, 5],
            "rf": 0.0025,
        }
    )
    style = pd.DataFrame(
        {
            "month_end": months,
            "big_growth_return": values[:, 0] - values[:, 2] / 2,
            "big_value_return": values[:, 0] + values[:, 2] / 2,
        }
    )
    daily_style = pd.DataFrame(
        {"date": dates, "big_growth_return": returns[:, 0], "big_value_return": returns[:, 1]}
    )
    tables = {
        "benchmark_daily": pd.concat(benchmark, ignore_index=True)
        .sort_values(["ticker", "date"])
        .reset_index(drop=True),
        "risk_free_daily": risk,
        "fama_french_3_monthly": ff3,
        "fama_french_5_momentum_monthly": ff5,
        "fama_french_style_monthly": style,
        "fama_french_style_daily": daily_style,
    }
    save_snapshot(
        tables,
        destination / "cache/market_data",
        MarketDataConfig(backtest_end_date=pd.Timestamp(end)),
        "deterministic fictional demonstration; not investment results",
    )
    return source


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT / ".local/synthetic")
    args = parser.parse_args()
    print("Created fictional source:", create(args.destination))
