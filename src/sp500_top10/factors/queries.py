"""Factors: queries."""

from __future__ import annotations

from ..config import FactorsConfig
from ..data.sql_resources import read_sql


def load_samples_strategy_levels(repository, *, config: FactorsConfig):
    """Load samples with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("factors_load_samples_strategy_levels.sql"))


def load_samples_sp500_levels(repository, *, config: FactorsConfig):
    """Load samples with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("factors_load_samples_sp500_levels.sql"))


def load_samples_ff3_monthly(repository, *, config: FactorsConfig):
    """Load samples with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("factors_load_samples_ff3_monthly.sql"))


def load_samples_ff5_momentum_monthly(repository, *, config: FactorsConfig):
    """Load samples with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("factors_load_samples_ff5_momentum_monthly.sql"))


def load_samples_style_monthly(repository, *, config: FactorsConfig):
    """Load samples with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("factors_load_samples_style_monthly.sql"))
