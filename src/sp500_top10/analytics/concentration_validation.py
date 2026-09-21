"""Analytics: concentration validation."""

from __future__ import annotations

import pandas as pd

from ..config import AnalyticsConfig


def calculate_concentration_validation(monthly_top10_concentration, *, config: AnalyticsConfig):
    """Calculate concentration validation with explicit inputs; preserve legacy conventions."""
    monthly_concentration_validation = pd.DataFrame(
        [
            {
                "check": "Unique monthly observation dates",
                "status": "PASS"
                if not monthly_top10_concentration["observation_date"].duplicated().any()
                else "FAIL",
            },
            {
                "check": "Top 10 share between 0% and 100%",
                "status": "PASS"
                if monthly_top10_concentration["top10_market_cap_share"].between(0, 1).all()
                else "FAIL",
            },
            {
                "check": "Top 10 market cap <= total market cap",
                "status": "PASS"
                if (
                    monthly_top10_concentration["top10_total_market_cap"]
                    <= monthly_top10_concentration["sp500_total_market_cap"]
                ).all()
                else "FAIL",
            },
            {
                "check": "No missing concentration values",
                "status": "PASS"
                if monthly_top10_concentration["top10_market_cap_share"].notna().all()
                else "FAIL",
            },
        ]
    )
    if monthly_concentration_validation["status"].eq("FAIL").any():
        raise ValueError("Monthly Top 10 concentration validation failed.")
    return ()
