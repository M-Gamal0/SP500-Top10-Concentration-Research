"""Market Data: fred."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

from ..config import MarketDataConfig
from .transport import retrieve


def download_fred_series(
    series_id: str, start_date, end_date, *, config: MarketDataConfig, raw_dir: Path | None = None
) -> pd.DataFrame:
    FRED_CSV_URL_TEMPLATE = config.fred_csv_url_template
    url = FRED_CSV_URL_TEMPLATE.format(series_id=series_id)
    data = pd.read_csv(io.BytesIO(retrieve(url, raw_dir)))
    expected_columns = {"observation_date", series_id}
    if not expected_columns.issubset(data.columns):
        raise ValueError(f"Unexpected FRED columns for {series_id}: {data.columns.tolist()}")
    data = data.rename(columns={"observation_date": "date", series_id: "value"})
    data["date"] = pd.to_datetime(data["date"], errors="coerce").astype("datetime64[ns]")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data = data.dropna(subset=["date", "value"])
    data = data[
        (data["date"] >= pd.Timestamp(start_date)) & (data["date"] <= pd.Timestamp(end_date))
    ].copy()
    if data.empty:
        raise ValueError(f"No valid {series_id} data found between {start_date} and {end_date}.")
    data["series_id"] = series_id
    data = data[["date", "series_id", "value"]].sort_values("date").reset_index(drop=True)
    return data
