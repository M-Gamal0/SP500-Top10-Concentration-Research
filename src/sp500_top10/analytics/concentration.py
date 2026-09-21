"""Analytics: concentration."""

from __future__ import annotations

from ..config import AnalyticsConfig


def calculate_concentration(monthly_top10_concentration_input, *, config: AnalyticsConfig):
    """Calculate concentration with explicit inputs; preserve legacy conventions."""
    monthly_top10_concentration = monthly_top10_concentration_input
    monthly_top10_concentration["top10_market_cap_share_pct"] = (
        monthly_top10_concentration["top10_market_cap_share"] * 100
    )
    return (monthly_top10_concentration,)
