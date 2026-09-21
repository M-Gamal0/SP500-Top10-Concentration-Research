"""Orchestrate analytics without notebook execution."""

from ..config import AnalyticsConfig
from ..data.results import StageResult
from .attribution_inputs import (
    prepare_attribution_index,
    prepare_attribution_weights,
    prepare_component_names,
    prepare_linked_contributions,
)
from .attribution_validation import calculate_attribution_validation
from .calendar_returns import calculate_calendar_returns
from .component_attribution import calculate_component_attribution
from .concentration import calculate_concentration
from .concentration_validation import calculate_concentration_validation
from .construction_comparison import compare_constructions, prepare_weight_metrics
from .cost_sensitivity import calculate_cost_sensitivity, prepare_cost_returns
from .drawdowns import calculate_drawdowns
from .factor_exposure import calculate_factor_exposure, prepare_exposure_returns
from .growth import calculate_growth, normalize_strategy_levels
from .historical_periods import calculate_historical_periods
from .holdings import build_holdings_snapshots, normalize_snapshot_dates
from .period_returns import calculate_period_returns
from .queries import (
    load_attribution_inputs_attribution_daily_index,
    load_attribution_inputs_attribution_daily_weights,
    load_attribution_inputs_component_names,
    load_attribution_inputs_component_sectors,
    load_concentration_monthly_top10_concentration,
    load_construction_comparison_daily_weight_metrics,
    load_construction_comparison_turnover_data,
    load_cost_sensitivity_cost_daily_returns,
    load_cost_sensitivity_cost_turnover,
    load_factor_exposure_ff3_monthly,
    load_growth_benchmark_levels,
    load_growth_strategy_levels,
    load_holdings_slide08_daily_weights,
    load_holdings_slide08_names,
    load_regimes_style_monthly,
    load_risk_metrics_risk_free_a1,
    load_robustness_max_issuer_weights,
    load_robustness_robustness_benchmark,
    load_robustness_robustness_strategy_levels,
    load_sector_allocation_quarterly_mc_holdings,
    load_sector_allocation_sector_metadata,
)
from .regime_performance import calculate_regime_performance
from .regimes import classify_market_style_regimes, prepare_benchmark_months
from .relative_drawdowns import calculate_relative_drawdowns
from .risk_metrics import calculate_risk_metrics, prepare_risk_returns
from .robustness import (
    calculate_robustness_returns,
    prepare_robustness_levels,
    summarize_robustness,
)
from .rolling_distribution import calculate_rolling_distribution
from .rolling_returns import calculate_rolling_returns
from .sector_allocation import calculate_sector_allocation, normalize_holdings_dates
from .sector_attribution import calculate_sector_attribution
from .top_contributors import calculate_top_contributors


def run(repository, config: AnalyticsConfig) -> StageResult:
    monthly_top10_concentration_input = load_concentration_monthly_top10_concentration(
        repository, config=config
    )
    (monthly_top10_concentration,) = calculate_concentration(
        monthly_top10_concentration_input, config=config
    )
    calculate_concentration_validation(monthly_top10_concentration, config=config)
    slide08_daily_weights_input = load_holdings_slide08_daily_weights(repository, config=config)
    (slide08_daily_weights,) = normalize_snapshot_dates(slide08_daily_weights_input, config=config)
    slide08_names_input = load_holdings_slide08_names(repository, config=config)
    (holdings_first_latest,) = build_holdings_snapshots(
        slide08_daily_weights, slide08_names_input, config=config
    )
    strategy_levels_input = load_growth_strategy_levels(repository, config=config)
    (strategy_levels,) = normalize_strategy_levels(strategy_levels_input, config=config)
    benchmark_levels_input = load_growth_benchmark_levels(repository, config=config)
    growth_1000_full_period, growth_1000_summary, growth_1000_wide = calculate_growth(
        benchmark_levels_input, strategy_levels, config=config
    )
    (period_return_summary,) = calculate_period_returns(growth_1000_wide, config=config)
    rolling_cagr_chart, rolling_cagr_distribution = calculate_rolling_distribution(
        growth_1000_wide, config=config
    )
    (rolling_60m_cagr_gap_monthly,) = calculate_rolling_returns(growth_1000_wide, config=config)
    absolute_drawdown_daily, absolute_drawdown_summary = calculate_drawdowns(
        growth_1000_wide, config=config
    )
    relative_drawdown_daily, relative_drawdown_summary = calculate_relative_drawdowns(
        growth_1000_wide, config=config
    )
    (period_analysis,) = calculate_historical_periods(growth_1000_wide, config=config)
    (sp500_monthly,) = prepare_benchmark_months(growth_1000_wide, config=config)
    style_monthly_input = load_regimes_style_monthly(repository, config=config)
    (
        market_style_state_counts,
        market_style_state_matrix,
        monthly_market_style_states,
    ) = classify_market_style_regimes(sp500_monthly, style_monthly_input, config=config)
    (market_style_performance_summary,) = calculate_regime_performance(
        growth_1000_wide, monthly_market_style_states, config=config
    )
    (factor_monthly_returns,) = prepare_exposure_returns(growth_1000_wide, config=config)
    ff3_monthly_input = load_factor_exposure_ff3_monthly(repository, config=config)
    factor_exposure_summary, rolling_36m_hml_chart, rolling_hml_exposures = (
        calculate_factor_exposure(factor_monthly_returns, ff3_monthly_input, config=config)
    )
    quarterly_mc_holdings_input = load_sector_allocation_quarterly_mc_holdings(
        repository, config=config
    )
    (quarterly_mc_holdings,) = normalize_holdings_dates(quarterly_mc_holdings_input, config=config)
    sector_metadata_input = load_sector_allocation_sector_metadata(repository, config=config)
    quarterly_sector_allocation, quarterly_sector_allocation_chart = calculate_sector_allocation(
        quarterly_mc_holdings, sector_metadata_input, config=config
    )
    daily_weight_metrics_input = load_construction_comparison_daily_weight_metrics(
        repository, config=config
    )
    (daily_weight_metrics,) = prepare_weight_metrics(daily_weight_metrics_input, config=config)
    turnover_data_input = load_construction_comparison_turnover_data(repository, config=config)
    (construction_summary,) = compare_constructions(
        daily_weight_metrics,
        growth_1000_summary,
        growth_1000_wide,
        relative_drawdown_summary,
        turnover_data_input,
        config=config,
    )
    cost_daily_returns_input = load_cost_sensitivity_cost_daily_returns(repository, config=config)
    (cost_daily_returns,) = prepare_cost_returns(cost_daily_returns_input, config=config)
    cost_turnover_input = load_cost_sensitivity_cost_turnover(repository, config=config)
    transaction_cost_chart, transaction_cost_sensitivity = calculate_cost_sensitivity(
        cost_daily_returns, cost_turnover_input, config=config
    )
    robustness_strategy_levels_input = load_robustness_robustness_strategy_levels(
        repository, config=config
    )
    (robustness_strategy_levels,) = prepare_robustness_levels(
        robustness_strategy_levels_input, config=config
    )
    robustness_benchmark_input = load_robustness_robustness_benchmark(repository, config=config)
    (
        benchmark_cagr,
        five_year_win_frequency_pct,
        full_period_cagr,
        worst_relative_drawdown_pct,
    ) = calculate_robustness_returns(
        robustness_benchmark_input, robustness_strategy_levels, config=config
    )
    max_issuer_weights_input = load_robustness_max_issuer_weights(repository, config=config)
    (topn_robustness_summary,) = summarize_robustness(
        benchmark_cagr,
        five_year_win_frequency_pct,
        full_period_cagr,
        max_issuer_weights_input,
        worst_relative_drawdown_pct,
        config=config,
    )
    attribution_daily_index_input = load_attribution_inputs_attribution_daily_index(
        repository, config=config
    )
    (attribution_daily_index,) = prepare_attribution_index(
        attribution_daily_index_input, config=config
    )
    attribution_daily_weights_input = load_attribution_inputs_attribution_daily_weights(
        repository, config=config
    )
    (attribution_daily_weights,) = prepare_attribution_weights(
        attribution_daily_weights_input, config=config
    )
    component_names_input = load_attribution_inputs_component_names(repository, config=config)
    (component_names,) = prepare_component_names(component_names_input, config=config)
    component_sectors_input = load_attribution_inputs_component_sectors(repository, config=config)
    attribution_daily_components, quarterly_portfolio_meta = prepare_linked_contributions(
        attribution_daily_index,
        attribution_daily_weights,
        component_names,
        component_sectors_input,
        config=config,
    )
    quarterly_component_attribution, quarterly_component_returns = calculate_component_attribution(
        attribution_daily_components, quarterly_portfolio_meta, config=config
    )
    (quarterly_sector_attribution,) = calculate_sector_attribution(
        attribution_daily_components, quarterly_portfolio_meta, config=config
    )
    (quarterly_top_contributor_share,) = calculate_top_contributors(
        quarterly_component_attribution, config=config
    )
    calculate_attribution_validation(
        quarterly_component_attribution, quarterly_sector_attribution, config=config
    )
    a1_levels, a1_returns = prepare_risk_returns(growth_1000_wide, config=config)
    risk_free_a1_input = load_risk_metrics_risk_free_a1(repository, config=config)
    (appendix_a1_metrics,) = calculate_risk_metrics(
        a1_levels, a1_returns, risk_free_a1_input, config=config
    )
    (calendar_year_returns,) = calculate_calendar_returns(growth_1000_wide, config=config)
    return StageResult(
        tables={
            "analytics_top10_concentration_monthly": monthly_top10_concentration,
            "analytics_holdings_first_latest": holdings_first_latest,
            "analytics_growth_1000_full_period": growth_1000_full_period,
            "analytics_growth_1000_summary": growth_1000_summary,
            "analytics_period_return_summary": period_return_summary,
            "analytics_rolling_cagr_distribution": rolling_cagr_distribution,
            "analytics_rolling_cagr_chart": rolling_cagr_chart,
            "analytics_rolling_60m_cagr_gap_monthly": rolling_60m_cagr_gap_monthly,
            "analytics_absolute_drawdown_daily": absolute_drawdown_daily,
            "analytics_absolute_drawdown_summary": absolute_drawdown_summary,
            "analytics_relative_drawdown_daily": relative_drawdown_daily,
            "analytics_relative_drawdown_summary": relative_drawdown_summary,
            "analytics_period_analysis": period_analysis,
            "analytics_monthly_market_style_states": monthly_market_style_states,
            "analytics_market_style_state_counts": market_style_state_counts,
            "analytics_market_style_performance": market_style_performance_summary,
            "analytics_rolling_36m_hml_exposures": rolling_hml_exposures,
            "analytics_factor_exposure_summary": factor_exposure_summary,
            "analytics_quarterly_sector_allocation": quarterly_sector_allocation,
            "analytics_construction_summary": construction_summary,
            "analytics_transaction_cost_sensitivity": transaction_cost_sensitivity,
            "analytics_topn_robustness_summary": topn_robustness_summary,
            "analytics_quarterly_component_returns": quarterly_component_returns,
            "analytics_quarterly_component_attribution": quarterly_component_attribution,
            "analytics_quarterly_sector_attribution": quarterly_sector_attribution,
            "analytics_quarterly_top_contributor_share": quarterly_top_contributor_share,
            "analytics_appendix_a1_metrics": appendix_a1_metrics,
            "analytics_calendar_year_returns": calendar_year_returns,
        },
        csvs={
            "top10_concentration_monthly.csv": monthly_top10_concentration,
            "holdings_first_latest.csv": holdings_first_latest,
            "growth_1000_full_period.csv": growth_1000_full_period,
            "growth_1000_summary.csv": growth_1000_summary,
            "period_return_summary.csv": period_return_summary,
            "rolling_cagr_distribution.csv": rolling_cagr_distribution,
            "rolling_cagr_chart.csv": rolling_cagr_chart,
            "rolling_60m_cagr_gap_monthly.csv": rolling_60m_cagr_gap_monthly,
            "absolute_drawdown_daily.csv": absolute_drawdown_daily,
            "absolute_drawdown_summary.csv": absolute_drawdown_summary,
            "relative_drawdown_daily.csv": relative_drawdown_daily,
            "relative_drawdown_summary.csv": relative_drawdown_summary,
            "period_analysis.csv": period_analysis,
            "monthly_market_style_states.csv": monthly_market_style_states,
            "market_style_state_matrix.csv": market_style_state_matrix,
            "market_style_performance.csv": market_style_performance_summary,
            "rolling_36m_hml_chart.csv": rolling_36m_hml_chart,
            "factor_exposure_summary.csv": factor_exposure_summary,
            "quarterly_sector_allocation_chart.csv": quarterly_sector_allocation_chart,
            "construction_summary.csv": construction_summary,
            "transaction_cost_sensitivity.csv": transaction_cost_chart,
            "topn_robustness_summary.csv": topn_robustness_summary,
            "quarterly_component_returns.csv": quarterly_component_returns,
            "quarterly_component_attribution.csv": quarterly_component_attribution,
            "quarterly_sector_attribution.csv": quarterly_sector_attribution,
            "quarterly_top_contributor_share.csv": quarterly_top_contributor_share,
            "appendix_a1_metrics.csv": appendix_a1_metrics,
            "calendar_year_returns.csv": calendar_year_returns,
        },
    )
