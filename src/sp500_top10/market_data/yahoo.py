"""Market Data: yahoo."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

from ..run_context import digest_file, save_json
from .transport import retry


def download_yahoo_data(
    tickers: str | list[str], start_date, end_date, *, raw_dir: Path | None = None
) -> pd.DataFrame:
    if isinstance(tickers, str):
        tickers = [tickers]
    tickers = sorted({str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()})
    if not tickers:
        raise ValueError("At least one valid ticker is required.")
    if raw_dir is not None:
        yf.set_tz_cache_location(str(raw_dir / "yfinance_cache"))
    downloaded_data = []
    for ticker in tickers:

        def download():
            result = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                auto_adjust=False,
                multi_level_index=False,
                progress=False,
                timeout=30,
            )
            if result.empty:
                raise OSError(f"No Yahoo Finance data returned for {ticker}.")
            return result

        data = retry(download)
        if raw_dir is not None:
            raw_dir.mkdir(parents=True, exist_ok=True)
            path = raw_dir / (ticker.replace("^", "index_") + ".csv")
            data.to_csv(path)
            save_json(
                path.with_suffix(".json"),
                {
                    "ticker": ticker,
                    "start": str(start_date),
                    "end": str(end_date),
                    "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                    "sha256": digest_file(path),
                    "format": "yfinance provider-returned frame",
                },
            )
        data = data.reset_index()
        data["ticker"] = ticker
        downloaded_data.append(data)
    yahoo_data = pd.concat(downloaded_data, ignore_index=True)
    yahoo_data.columns = yahoo_data.columns.str.strip().str.lower().str.replace(" ", "_")
    yahoo_data["date"] = pd.to_datetime(yahoo_data["date"]).astype("datetime64[ns]")
    yahoo_data = yahoo_data.sort_values(["date", "ticker"]).reset_index(drop=True)
    return yahoo_data
