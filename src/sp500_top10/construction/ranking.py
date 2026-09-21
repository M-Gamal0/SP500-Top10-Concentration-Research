"""Construction: ranking."""

from __future__ import annotations

from ..config import ConstructionConfig


def calculate_ranking(company_universe, *, config: ConstructionConfig):
    """Calculate ranking with explicit inputs; preserve legacy conventions."""
    quarterly_rankings = (
        company_universe.dropna(subset=["resolved_marketcap"])
        .sort_values(
            ["selection_date", "resolved_marketcap", "ticker"],
            ascending=[True, False, True],
        )
        .copy()
    )
    quarterly_rankings["rank"] = quarterly_rankings.groupby("selection_date").cumcount() + 1
    quarterly_rankings = quarterly_rankings[
        [
            "selection_date",
            "rank",
            "ticker",
            "name",
            "resolved_marketcap",
            "marketcap_source",
            "multi_class_company",
        ]
    ].reset_index(drop=True)
    ranking_check = quarterly_rankings.groupby("selection_date").agg(
        rows=("ticker", "size"),
        unique_tickers=("ticker", "nunique"),
        min_rank=("rank", "min"),
        max_rank=("rank", "max"),
        unique_ranks=("rank", "nunique"),
    )
    if not (ranking_check["rows"] == ranking_check["unique_tickers"]).all():
        raise ValueError(
            "Validation failed: (ranking_check['rows'] == ranking_check['unique_tickers']).all()"
        )
    if not (ranking_check["min_rank"] == 1).all():
        raise ValueError("Validation failed: (ranking_check['min_rank'] == 1).all()")
    if not (ranking_check["max_rank"] == ranking_check["rows"]).all():
        raise ValueError(
            "Validation failed: (ranking_check['max_rank'] == ranking_check['rows']).all()"
        )
    if not (ranking_check["unique_ranks"] == ranking_check["rows"]).all():
        raise ValueError(
            "Validation failed: (ranking_check['unique_ranks'] == ranking_check['rows']).all()"
        )
    marketcap_order_check = quarterly_rankings.groupby("selection_date")[
        "resolved_marketcap"
    ].apply(lambda x: x.is_monotonic_decreasing)
    if not marketcap_order_check.all():
        raise ValueError("Validation failed: marketcap_order_check.all()")
    return (quarterly_rankings,)
