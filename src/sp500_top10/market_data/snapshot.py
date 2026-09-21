"""Explicit, checksummed normalized provider snapshots for offline reproduction."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from ..data.database import identifier
from ..data.results import StageResult
from ..reporting.catalog import CATALOG
from ..run_context import digest_file, fingerprint, save_json


def save_snapshot(tables, directory: Path, config, origin: str):
    directory.mkdir(parents=True, exist_ok=True)
    records = {}
    with duckdb.connect() as connection:
        for name in CATALOG["market-data"]["tables"]:
            frame = tables[name]
            path = directory / (name + ".parquet")
            connection.register("snapshot_frame", frame)
            connection.execute("COPY snapshot_frame TO ? (FORMAT PARQUET)", [str(path)])
            connection.unregister("snapshot_frame")
            records[name] = {
                "file": path.name,
                "sha256": digest_file(path),
                "rows": len(frame),
            }
    save_json(
        directory / "manifest.json",
        {
            "format": 1,
            "origin": origin,
            "configuration": fingerprint(config),
            "tables": records,
        },
    )


def load_snapshot(directory: Path, config, calendar: pd.DataFrame) -> StageResult:
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Offline snapshot missing: {manifest_path}. Capture one or run market-data online."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["format"] != 1 or manifest["configuration"] != fingerprint(config):
        raise ValueError("Offline snapshot configuration does not match the requested run.")
    if set(manifest["tables"]) != set(CATALOG["market-data"]["tables"]):
        raise ValueError("Offline snapshot table inventory is incomplete.")
    tables = {}
    with duckdb.connect() as connection:
        for name, record in manifest["tables"].items():
            if record["file"] != name + ".parquet":
                raise ValueError("Invalid snapshot filename.")
            path = directory / record["file"]
            if digest_file(path) != record["sha256"]:
                raise ValueError(f"Snapshot checksum failed: {name}")
            tables[name] = connection.execute("SELECT * FROM read_parquet(?)", [str(path)]).df()
            if len(tables[name]) != record["rows"]:
                raise ValueError(f"Snapshot row count failed: {name}")
    dates = set(pd.to_datetime(calendar["date"]))
    if (
        not dates
        or min(dates) != config.backtest_start_date
        or max(dates) != config.backtest_end_date
    ):
        raise ValueError("Backtest calendar does not match the configured market-data window.")
    benchmark = tables["benchmark_daily"]
    if (
        set(benchmark["ticker"]) != set(config.benchmark_tickers)
        or benchmark.duplicated(["date", "ticker"]).any()
    ):
        raise ValueError("Invalid benchmark snapshot.")
    for ticker in config.benchmark_tickers:
        group = benchmark.loc[benchmark["ticker"].eq(ticker)]
        if (
            set(pd.to_datetime(group["date"])) != dates
            or group["close"].isna().any()
            or group["daily_return"].isna().sum() != 1
        ):
            raise ValueError(f"Incomplete benchmark snapshot: {ticker}")
    risk = tables["risk_free_daily"]
    if (
        risk["date"].duplicated().any()
        or set(pd.to_datetime(risk["date"])) != dates
        or risk.isna().any().any()
    ):
        raise ValueError("Risk-free snapshot does not match the backtest calendar.")
    if not np.allclose(
        risk["daily_risk_free_return"],
        risk["annual_rate_percent"] / 100 / config.trading_days_per_year,
        atol=1e-12,
        rtol=0,
    ):
        raise ValueError("Risk-free conversion mismatch.")
    for name in CATALOG["market-data"]["tables"][2:]:
        frame = tables[name]
        date_column = "date" if name.endswith("_daily") else "month_end"
        if (
            frame[date_column].duplicated().any()
            or not frame[date_column].is_monotonic_increasing
            or frame.isna().any().any()
        ):
            raise ValueError(f"Invalid factor snapshot: {name}")
        if (
            frame.empty
            or frame[date_column].min() < config.backtest_start_date
            or frame[date_column].max() > config.backtest_end_date
        ):
            raise ValueError(f"Factor snapshot is outside configured coverage: {name}")
    if len(tables["fama_french_5_momentum_monthly"]) < 120:
        raise ValueError("Insufficient FF5 + momentum history.")
    if len(set(tables["fama_french_style_daily"]["date"]) & dates) < config.trading_days_per_year:
        raise ValueError("Insufficient daily style overlap.")
    return StageResult(tables=tables)


def capture_database(source: Path, directory: Path, config):
    """Capture existing normalized tables; do not claim they are raw downloads."""
    if (directory / "manifest.json").exists():
        raise FileExistsError("Snapshot already exists; use a new directory.")
    with duckdb.connect(str(source), read_only=True) as connection:
        tables = {
            name: connection.execute(f"SELECT * FROM {identifier(name)}").df()
            for name in CATALOG["market-data"]["tables"]
        }
    save_snapshot(
        tables,
        directory,
        config,
        "normalized tables from source database sha256:" + digest_file(source),
    )
