"""Construction: queries."""

from __future__ import annotations

from ..config import ConstructionConfig


def load_universe_company_universe(repository, *, config: ConstructionConfig):
    """Load universe with explicit inputs; preserve legacy conventions."""
    INPUT_TABLE = config.input_table
    return repository.query(
        f"\n    SELECT\n        selection_date,\n        ticker,\n        name,\n        resolved_marketcap,\n        marketcap_source,\n        multi_class_company\n    FROM {INPUT_TABLE}\n    ORDER BY\n        selection_date,\n        ticker\n"
    )
