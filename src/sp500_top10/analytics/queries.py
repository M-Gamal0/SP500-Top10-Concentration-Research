"""Analytics: queries."""

from __future__ import annotations

from ..config import AnalyticsConfig
from ..data.sql_resources import read_sql


def load_concentration_monthly_top10_concentration(repository, *, config: AnalyticsConfig):
    """Load concentration with explicit inputs; preserve legacy conventions."""
    return repository.query(
        read_sql("analytics_load_concentration_monthly_top10_concentration.sql"),
        [config.concentration_start_date],
    )


def load_holdings_slide08_daily_weights(repository, *, config: AnalyticsConfig):
    """Load holdings with explicit inputs; preserve legacy conventions."""
    return repository.query(
        read_sql("analytics_load_holdings_slide08_daily_weights.sql"), [sorted(config.slide8_dates)]
    )


def load_holdings_slide08_names(repository, *, config: AnalyticsConfig):
    """Load holdings with explicit inputs; preserve legacy conventions."""
    return repository.query(
        read_sql("analytics_load_holdings_slide08_names.sql"), [sorted(config.slide8_dates)]
    )


def load_growth_strategy_levels(repository, *, config: AnalyticsConfig):
    """Load growth with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_growth_strategy_levels.sql"))


def load_growth_benchmark_levels(repository, *, config: AnalyticsConfig):
    """Load growth with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_growth_benchmark_levels.sql"))


def load_regimes_style_monthly(repository, *, config: AnalyticsConfig):
    """Load regimes with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_regimes_style_monthly.sql"))


def load_factor_exposure_ff3_monthly(repository, *, config: AnalyticsConfig):
    """Load factor exposure with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_factor_exposure_ff3_monthly.sql"))


def load_sector_allocation_quarterly_mc_holdings(repository, *, config: AnalyticsConfig):
    """Load sector allocation with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_sector_allocation_quarterly_mc_holdings.sql"))


def load_sector_allocation_sector_metadata(repository, *, config: AnalyticsConfig):
    """Load sector allocation with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_sector_allocation_sector_metadata.sql"))


def load_construction_comparison_daily_weight_metrics(repository, *, config: AnalyticsConfig):
    """Load construction comparison with explicit inputs; preserve legacy conventions."""
    return repository.query(
        read_sql("analytics_load_construction_comparison_daily_weight_metrics.sql")
    )


def load_construction_comparison_turnover_data(repository, *, config: AnalyticsConfig):
    """Load construction comparison with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_construction_comparison_turnover_data.sql"))


def load_cost_sensitivity_cost_daily_returns(repository, *, config: AnalyticsConfig):
    """Load cost sensitivity with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_cost_sensitivity_cost_daily_returns.sql"))


def load_cost_sensitivity_cost_turnover(repository, *, config: AnalyticsConfig):
    """Load cost sensitivity with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_cost_sensitivity_cost_turnover.sql"))


def load_robustness_robustness_strategy_levels(repository, *, config: AnalyticsConfig):
    """Load robustness with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_robustness_robustness_strategy_levels.sql"))


def load_robustness_robustness_benchmark(repository, *, config: AnalyticsConfig):
    """Load robustness with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_robustness_robustness_benchmark.sql"))


def load_robustness_max_issuer_weights(repository, *, config: AnalyticsConfig):
    """Load robustness with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_robustness_max_issuer_weights.sql"))


def load_attribution_inputs_attribution_daily_index(repository, *, config: AnalyticsConfig):
    """Load attribution inputs with explicit inputs; preserve legacy conventions."""
    return repository.query(
        read_sql("analytics_load_attribution_inputs_attribution_daily_index.sql")
    )


def load_attribution_inputs_attribution_daily_weights(repository, *, config: AnalyticsConfig):
    """Load attribution inputs with explicit inputs; preserve legacy conventions."""
    return repository.query(
        read_sql("analytics_load_attribution_inputs_attribution_daily_weights.sql")
    )


def load_attribution_inputs_component_names(repository, *, config: AnalyticsConfig):
    """Load attribution inputs with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_attribution_inputs_component_names.sql"))


def load_attribution_inputs_component_sectors(repository, *, config: AnalyticsConfig):
    """Load attribution inputs with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_attribution_inputs_component_sectors.sql"))


def load_risk_metrics_risk_free_a1(repository, *, config: AnalyticsConfig):
    """Load risk metrics with explicit inputs; preserve legacy conventions."""
    return repository.query(read_sql("analytics_load_risk_metrics_risk_free_a1.sql"))
