"""Provider boundaries use controlled payloads, never internet access in tests."""

import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from sp500_top10.config import MarketDataConfig
from sp500_top10.market_data.fred import download_fred_series
from sp500_top10.market_data.french import download_french_zip_csv
from sp500_top10.market_data.transport import retry
from sp500_top10.market_data.yahoo import download_yahoo_data


class ProviderTests(unittest.TestCase):
    def test_fred_parses_missing_and_filters_dates(self):
        payload = b"observation_date,DGS3MO\n2024-01-01,5.0\n2024-01-02,.\n2024-01-03,4.9\n"
        with patch("sp500_top10.market_data.fred.retrieve", return_value=payload):
            frame = download_fred_series(
                "DGS3MO", "2024-01-02", "2024-01-03", config=MarketDataConfig()
            )
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["date"], pd.Timestamp("2024-01-03"))
        self.assertEqual(frame.iloc[0]["value"], 4.9)

    def test_french_zip_has_exactly_one_csv(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("factors.csv", "header\n202401,1,2,3,4")
        with patch("sp500_top10.market_data.french.retrieve", return_value=data.getvalue()):
            self.assertIn("202401", download_french_zip_csv("https://example.invalid/factors.zip"))

    def test_yahoo_retains_unadjusted_download_setting(self):
        source = pd.DataFrame(
            {"Close": [100.0, 101.0], "Adj Close": [100.0, 102.0]},
            index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"], name="Date"),
        )
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch(
                "sp500_top10.market_data.yahoo.yf.download", return_value=source.copy()
            ) as download,
            patch("sp500_top10.market_data.yahoo.yf.set_tz_cache_location"),
        ):
            frame = download_yahoo_data(
                "^GSPC", "2024-01-02", "2024-01-04", raw_dir=Path(temporary)
            )
            self.assertFalse(download.call_args.kwargs["auto_adjust"])
            self.assertEqual(download.call_args.kwargs["timeout"], 30)
            self.assertEqual(frame["close"].tolist(), [100.0, 101.0])
            self.assertTrue(list(Path(temporary).glob("*.json")))

    def test_retries_are_bounded(self):
        with patch("sp500_top10.market_data.transport.time.sleep") as sleep:
            from unittest.mock import Mock

            operation = Mock(side_effect=OSError("temporary network failure"))
            with self.assertRaises(OSError):
                retry(operation, attempts=3)
            self.assertEqual(operation.call_count, 3)
            self.assertEqual(sleep.call_count, 2)


if __name__ == "__main__":
    unittest.main()
