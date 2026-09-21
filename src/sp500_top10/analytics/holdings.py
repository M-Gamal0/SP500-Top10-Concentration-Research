"""Analytics: holdings."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def normalize_snapshot_dates(slide08_daily_weights_input, *, config: AnalyticsConfig):
    """Calculate holdings with explicit inputs; preserve legacy conventions."""
    slide08_daily_weights = slide08_daily_weights_input
    slide08_daily_weights["date"] = pd.to_datetime(slide08_daily_weights["date"])
    return (slide08_daily_weights,)


def build_holdings_snapshots(
    slide08_daily_weights, slide08_names_input, *, config: AnalyticsConfig
):
    """Calculate holdings with explicit inputs; preserve legacy conventions."""
    SLIDE8_DATES = config.slide8_dates
    TOLERANCE = config.tolerance
    slide08_names = slide08_names_input
    slide08_names["date"] = pd.to_datetime(slide08_names["date"])
    holdings_first_latest = (
        slide08_daily_weights.merge(
            slide08_names, on=["date", "ticker"], how="left", validate="one_to_one"
        )
        .sort_values(["date", "ending_weight"], ascending=[True, False])
        .reset_index(drop=True)
    )
    holdings_first_latest["rank"] = holdings_first_latest.groupby("date").cumcount().add(1)
    holdings_first_latest["snapshot"] = holdings_first_latest["date"].map(SLIDE8_DATES)
    holdings_first_latest["mc_weight_pct"] = holdings_first_latest["ending_weight"] * 100
    holdings_first_latest = holdings_first_latest[
        ["snapshot", "date", "rank", "ticker", "name", "mc_weight_pct"]
    ].rename(columns={"name": "company"})
    validation = holdings_first_latest.groupby("date").agg(
        holdings=("ticker", "size"), weight_sum=("mc_weight_pct", "sum")
    )
    if not validation["holdings"].eq(10).all():
        raise ValueError("Slide 8 does not contain exactly 10 holdings per date.")
    if not np.allclose(validation["weight_sum"], 100.0, atol=TOLERANCE * 100, rtol=0):
        raise ValueError("Slide 8 weights do not sum to 100%.")
    if holdings_first_latest["company"].isna().any():
        raise ValueError("Missing company name in Slide 8 output.")
    for snapshot in SLIDE8_DATES.values():
        pass
    return (holdings_first_latest,)
