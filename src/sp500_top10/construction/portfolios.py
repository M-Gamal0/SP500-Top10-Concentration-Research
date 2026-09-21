"""Construction: portfolios."""

from __future__ import annotations

from ..config import ConstructionConfig
from .weighting import (
    apply_buffered_20_weighting,
    apply_equal_weighting,
    apply_market_cap_weighting,
)


def calculate_portfolios(selected_top10, selected_top20, *, config: ConstructionConfig):
    """Calculate portfolios with explicit inputs; preserve legacy conventions."""
    top10_market_cap_weights = apply_market_cap_weighting(selected_top10)
    top10_equal_weights = apply_equal_weighting(selected_top10)
    top10_buffered_20_weights = apply_buffered_20_weighting(selected_top10, config=config)
    top20_market_cap_weights = apply_market_cap_weighting(selected_top20)
    return (
        top10_buffered_20_weights,
        top10_equal_weights,
        top10_market_cap_weights,
        top20_market_cap_weights,
    )
