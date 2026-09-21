"""Orchestrate factors without notebook execution."""

from ..config import FactorsConfig
from ..data.results import StageResult
from .attribution import calculate_attribution
from .exposure import calculate_exposure
from .model_comparison import calculate_model_comparison
from .persistence import calculate_persistence
from .queries import (
    load_samples_ff3_monthly,
    load_samples_ff5_momentum_monthly,
    load_samples_sp500_levels,
    load_samples_strategy_levels,
    load_samples_style_monthly,
)
from .regression_comparison import calculate_regression_comparison
from .samples import (
    calculate_samples,
    prepare_factor_monthly_data,
    prepare_ff3_monthly,
    prepare_ff5_momentum_monthly,
    prepare_monthly_portfolio_returns,
)
from .strategy_comparison import calculate_strategy_comparison
from .style_environment import calculate_style_environment


def run(repository, config: FactorsConfig) -> StageResult:
    strategy_levels_input = load_samples_strategy_levels(repository, config=config)
    (strategy_levels,) = calculate_samples(strategy_levels_input, config=config)
    sp500_levels_input = load_samples_sp500_levels(repository, config=config)
    (monthly_portfolio_returns,) = prepare_monthly_portfolio_returns(
        sp500_levels_input, strategy_levels, config=config
    )
    ff3_monthly_input = load_samples_ff3_monthly(repository, config=config)
    (ff3_monthly,) = prepare_ff3_monthly(ff3_monthly_input, config=config)
    ff5_momentum_monthly_input = load_samples_ff5_momentum_monthly(repository, config=config)
    (ff5_momentum_monthly,) = prepare_ff5_momentum_monthly(
        ff5_momentum_monthly_input, config=config
    )
    style_monthly_input = load_samples_style_monthly(repository, config=config)
    (factor_monthly_data,) = prepare_factor_monthly_data(
        ff3_monthly,
        ff5_momentum_monthly,
        monthly_portfolio_returns,
        style_monthly_input,
        config=config,
    )
    factor_exposure_summary, rolling_36m_hml_chart, rolling_hml_exposures = calculate_exposure(
        factor_monthly_data, config=config
    )
    style_environment_period_compare, style_environment_state_mix = calculate_style_environment(
        factor_monthly_data, config=config
    )
    (active_return_regression_by_period,) = calculate_regression_comparison(
        factor_monthly_data, config=config
    )
    (recent_factor_attribution,) = calculate_attribution(
        active_return_regression_by_period, factor_monthly_data, config=config
    )
    factor_adjusted_persistence_summary, rolling_factor_adjusted_performance = (
        calculate_persistence(factor_monthly_data, config=config)
    )
    (factor_model_robustness_recent_10y,) = calculate_model_comparison(
        active_return_regression_by_period, factor_monthly_data, config=config
    )
    (ff5_momentum_alpha_by_strategy_period,) = calculate_strategy_comparison(
        active_return_regression_by_period, factor_monthly_data, config=config
    )
    return StageResult(
        tables={
            "factor_attribution_rolling_36m_hml_exposures": rolling_hml_exposures,
            "factor_attribution_exposure_summary": factor_exposure_summary,
            "factor_attribution_style_environment_period_compare": style_environment_period_compare,
            "factor_attribution_style_environment_state_mix": style_environment_state_mix,
            "factor_attribution_active_return_regression_by_period": active_return_regression_by_period,
            "factor_attribution_recent_factor_attribution": recent_factor_attribution,
            "factor_attribution_rolling_factor_adjusted_performance": rolling_factor_adjusted_performance,
            "factor_attribution_factor_adjusted_persistence_summary": factor_adjusted_persistence_summary,
            "factor_attribution_factor_model_robustness_recent_10y": factor_model_robustness_recent_10y,
            "factor_attribution_ff5_momentum_alpha_by_strategy_period": ff5_momentum_alpha_by_strategy_period,
        },
        csvs={
            "rolling_36m_hml_chart.csv": rolling_36m_hml_chart,
            "factor_exposure_summary.csv": factor_exposure_summary,
            "style_environment_period_compare.csv": style_environment_period_compare,
            "style_environment_state_mix.csv": style_environment_state_mix,
            "active_return_regression_by_period.csv": active_return_regression_by_period,
            "recent_factor_attribution.csv": recent_factor_attribution,
            "rolling_factor_adjusted_performance.csv": rolling_factor_adjusted_performance,
            "factor_adjusted_persistence_summary.csv": factor_adjusted_persistence_summary,
            "factor_model_robustness_recent_10y.csv": factor_model_robustness_recent_10y,
            "ff5_momentum_alpha_by_strategy_period.csv": ff5_momentum_alpha_by_strategy_period,
        },
    )
