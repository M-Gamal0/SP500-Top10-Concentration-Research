"""Construction: universe."""

from __future__ import annotations

from ..config import ConstructionConfig


def calculate_universe(company_universe_input, *, config: ConstructionConfig):
    """Calculate universe with explicit inputs; preserve legacy conventions."""
    company_universe = company_universe_input
    if not not company_universe.duplicated(["selection_date", "ticker"]).any():
        raise ValueError(
            "Validation failed: not company_universe.duplicated(['selection_date', 'ticker']).any()"
        )
    return (company_universe,)
