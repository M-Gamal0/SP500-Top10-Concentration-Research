"""Analytics: top contributors."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def calculate_top_contributors(quarterly_component_attribution, *, config: AnalyticsConfig):
    """Calculate top contributors with explicit inputs; preserve legacy conventions."""
    ATTRIBUTION_TOLERANCE = config.attribution_tolerance
    component_attribution_numeric = quarterly_component_attribution[
        [
            "quarter",
            "quarter_start",
            "quarter_end",
            "ticker",
            "company",
            "exact_contribution_pp",
            "portfolio_total_return_pct",
        ]
    ].copy()
    top_contributor_rows = []
    for (
        quarter,
        quarter_start,
        quarter_end,
    ), group in component_attribution_numeric.groupby(
        ["quarter", "quarter_start", "quarter_end"], sort=False
    ):
        group = group.sort_values(
            ["exact_contribution_pp", "ticker"], ascending=[False, True]
        ).reset_index(drop=True)
        portfolio_return_pct = float(group["portfolio_total_return_pct"].iloc[0])
        row = {
            "quarter": quarter,
            "quarter_start": quarter_start,
            "quarter_end": quarter_end,
            "portfolio_total_return_pct": portfolio_return_pct,
        }
        for top_k in [1, 3, 5]:
            leaders = group.head(top_k).copy()
            contribution_pp = float(leaders["exact_contribution_pp"].sum())
            if abs(portfolio_return_pct) > ATTRIBUTION_TOLERANCE * 100:
                share_pct = contribution_pp / portfolio_return_pct * 100
            else:
                share_pct = np.nan
            row[f"top{top_k}_contribution_pp"] = contribution_pp
            row[f"top{top_k}_share_of_portfolio_return_pct"] = share_pct
            row[f"top{top_k}_leaders"] = " | ".join(leaders["ticker"].tolist())
        top_contributor_rows.append(row)
    quarterly_top_contributor_share = (
        pd.DataFrame(top_contributor_rows).sort_values("quarter_end").reset_index(drop=True)
    )
    return (quarterly_top_contributor_share,)
