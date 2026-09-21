"""Construction: selection."""

from __future__ import annotations

import pandas as pd

from ..config import ConstructionConfig


def select_top_n(rankings: pd.DataFrame, top_n: int) -> pd.DataFrame:
    if top_n <= 0:
        raise ValueError("top_n must be greater than zero.")
    selected = (
        rankings[rankings["rank"] <= top_n]
        .copy()
        .sort_values(["selection_date", "rank"])
        .reset_index(drop=True)
    )
    holdings = selected.groupby("selection_date")["ticker"].nunique()
    if (holdings != top_n).any():
        raise ValueError(f"Not every selection date has exactly {top_n} eligible companies.")
    return selected


def calculate_selection(quarterly_rankings, *, config: ConstructionConfig):
    """Calculate selection with explicit inputs; preserve legacy conventions."""
    CORE_TOP_N = config.core_top_n
    ROBUSTNESS_TOP_N = config.robustness_top_n
    selected_top10 = select_top_n(quarterly_rankings, top_n=CORE_TOP_N)
    selected_top20 = select_top_n(quarterly_rankings, top_n=ROBUSTNESS_TOP_N)
    return (selected_top10, selected_top20)
