"""Analytics: attribution validation."""

from __future__ import annotations

import numpy as np

from ..config import AnalyticsConfig


def calculate_attribution_validation(
    quarterly_component_attribution,
    quarterly_sector_attribution,
    *,
    config: AnalyticsConfig,
):
    """Calculate attribution validation with explicit inputs; preserve legacy conventions."""
    ATTRIBUTION_TOLERANCE = config.attribution_tolerance
    component_reconciliation = quarterly_component_attribution.groupby(
        ["quarter", "quarter_end"], as_index=False
    ).agg(
        component_contribution_pp=("exact_contribution_pp", "sum"),
        portfolio_return_pct=("portfolio_total_return_pct", "first"),
    )
    component_reconciliation["difference_pp"] = (
        component_reconciliation["component_contribution_pp"]
        - component_reconciliation["portfolio_return_pct"]
    )
    if component_reconciliation["difference_pp"].abs().max() > ATTRIBUTION_TOLERANCE * 100:
        raise ValueError("Quarterly component attribution does not reconcile to portfolio return.")
    sector_reconciliation = quarterly_sector_attribution.groupby(
        ["quarter", "quarter_end"], as_index=False
    ).agg(
        sector_contribution_pp=("exact_contribution_pp", "sum"),
        portfolio_return_pct=("portfolio_total_return_pct", "first"),
    )
    sector_reconciliation["difference_pp"] = (
        sector_reconciliation["sector_contribution_pp"]
        - sector_reconciliation["portfolio_return_pct"]
    )
    if sector_reconciliation["difference_pp"].abs().max() > ATTRIBUTION_TOLERANCE * 100:
        raise ValueError("Quarterly sector attribution does not reconcile to portfolio return.")
    start_weight_check = quarterly_component_attribution.groupby("quarter_end")[
        "start_weight_pct"
    ].sum()
    if not np.allclose(start_weight_check, 100.0, atol=ATTRIBUTION_TOLERANCE * 100, rtol=0):
        raise ValueError("Quarter-start component weights do not sum to 100%.")
    sector_start_weight_check = quarterly_sector_attribution.groupby("quarter_end")[
        "start_sector_weight_pct"
    ].sum()
    if not np.allclose(sector_start_weight_check, 100.0, atol=ATTRIBUTION_TOLERANCE * 100, rtol=0):
        raise ValueError("Quarter-start sector weights do not sum to 100%.")
    return ()
