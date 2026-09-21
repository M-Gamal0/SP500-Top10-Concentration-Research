"""Small independently checkable examples for the preserved methodology."""

import unittest

import numpy as np
import pandas as pd

from sp500_top10.analytics.attribution_inputs import add_quarter_linking_factor
from sp500_top10.backtesting.calendar import get_next_trading_date, get_previous_trading_date
from sp500_top10.backtesting.engine import run_backtest
from sp500_top10.backtesting.rebalancing import review_buffered_20_weights
from sp500_top10.config import BacktestingConfig
from sp500_top10.construction.weighting import apply_iterative_caps
from sp500_top10.market_data.french import clean_french_return, extract_french_table


class CalculationTests(unittest.TestCase):
    def test_cap_redistribution(self):
        result = apply_iterative_caps(pd.Series([0.6, 0.2, 0.2]), pd.Series([0.4, 0.4, 0.4]))
        np.testing.assert_allclose(result, [0.4, 0.3, 0.3], atol=1e-12, rtol=0)
        with self.assertRaises(ValueError):
            apply_iterative_caps(pd.Series([0.5, 0.5]), pd.Series([0.4, 0.4]))

    def test_trading_dates_are_strict(self):
        dates = pd.DatetimeIndex(["2024-03-28", "2024-04-01", "2024-04-02"])
        self.assertEqual(get_next_trading_date("2024-03-28", dates), pd.Timestamp("2024-04-01"))
        self.assertEqual(get_previous_trading_date("2024-04-01", dates), pd.Timestamp("2024-03-28"))

    def test_monthly_threshold_and_reset(self):
        config = BacktestingConfig()
        weights = pd.Series([0.2] + [0.8 / 9] * 9)
        self.assertFalse(review_buffered_20_weights(weights, config=config)[0])
        weights = pd.Series([0.25] + [0.75 / 9] * 9)
        breached, reset, _ = review_buffered_20_weights(weights, config=config)
        self.assertTrue(breached)
        self.assertAlmostEqual(reset.iloc[0], 0.18)
        self.assertAlmostEqual(reset.sum(), 1.0)

    def test_price_drift_and_total_returns_share_beginning_weights(self):
        dates = pd.DatetimeIndex(["2024-01-02", "2024-01-03", "2024-01-04"])
        price = pd.DataFrame([[0, 0], [0.1, -0.1], [0, 0]], index=dates, columns=["A", "B"])
        total = pd.DataFrame([[0, 0], [0.2, 0], [0.1, 0]], index=dates, columns=["A", "B"])
        daily, weights, _, events = run_backtest(
            dates[1:],
            {dates[1]: pd.Series({"A": 0.5, "B": 0.5})},
            price,
            total,
            dates[0],
            dates,
            set(),
            config=BacktestingConfig(),
        )
        self.assertAlmostEqual(daily.iloc[1]["price_return"], 0)
        self.assertAlmostEqual(daily.iloc[1]["total_return"], 0.1)
        self.assertAlmostEqual(daily.iloc[2]["total_return"], 0.055)
        self.assertAlmostEqual(
            weights.loc[
                (weights["date"] == dates[1]) & (weights["ticker"] == "A"), "ending_weight"
            ].iloc[0],
            0.55,
        )
        self.assertTrue(events.empty)  # Initial establishment is excluded.

    def test_geometric_linking(self):
        data = pd.DataFrame(
            {"date": pd.to_datetime(["2024-01-02", "2024-01-03"]), "total_return": [0.1, 0.2]}
        )
        linked = add_quarter_linking_factor(data)
        np.testing.assert_allclose(linked["linking_factor"], [1.2, 1])
        self.assertAlmostEqual(
            (linked["total_return"] * linked["linking_factor"]).sum(), 1.1 * 1.2 - 1
        )

    def test_french_sections_and_missing_values(self):
        text = "Monthly\n,Mkt-RF,SMB,HML,RF\n202401,1,2,3,.4\n202402,2,-99.99,4,.4\nAnnual\n2024,9,9,9,9"
        frame = extract_french_table(text, r"\d{6}", ["Mkt-RF", "SMB", "HML", "RF"])
        self.assertEqual(len(frame), 2)
        cleaned = clean_french_return(frame["SMB"])
        self.assertAlmostEqual(cleaned.iloc[0], 0.02)
        self.assertTrue(pd.isna(cleaned.iloc[1]))


if __name__ == "__main__":
    unittest.main()
