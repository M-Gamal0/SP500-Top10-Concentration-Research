# CSV output compatibility contract

Status: architecture companion; no exports have been regenerated.

This inventory combines the exact `csv_frames` mappings in notebooks 06 and 07 with the ordered headers read from all 38 existing local CSV files. It contains column names and source-frame mappings, not private data records. It is a structural reference, not a claim that the saved values have already been reproduced from current notebook source.

See [ARCHITECTURE.md](ARCHITECTURE.md) for migration stages, numerical comparison, and publication behavior.

## Required behavior

- Preserve the `analytics/` and `factor_attribution/` subdirectories and every filename below. Resolve their containing output root dynamically from the project location or an explicit configuration override.
- Preserve exact column spelling, capitalization, order, units, row ordering, and existing intentional rounding.
- Preserve UTF-8 with BOM, no index column, `%Y-%m-%d` date serialization, and empty fields for missing values.
- Keep full numeric analytical results separate from display formatting.
- Keep the two same-named exposure files in their separate directories. They may use different common samples; do not merge or overwrite one with the other.
- Freeze row counts, ordered values, and hashes in private baseline storage before implementation. Those values vary with inputs and do not belong in a universal public contract.
- Verify values and ordering during migration, in addition to the notebooks' existing header and row-count checks.

## Layouts requiring explicit adapters

| CSV | Behavior to preserve |
|---|---|
| Analytics `market_style_state_matrix.csv` | Pivot state counts into the configured market/style matrix. |
| Both `rolling_36m_hml_chart.csv` files | Pivot exposure results into MC estimates, MC confidence bounds, and S&P 500 estimates; preserve each notebook's own input sample. |
| Analytics `quarterly_sector_allocation_chart.csv` | Pivot sectors into columns and express weights in percent. Sector columns depend on the input data; the observed header below is the current reference. |
| Analytics `transaction_cost_sensitivity.csv` | Export the wide net-CAGR chart in percent, not the eight-column detailed sensitivity table. |
| Analytics `appendix_a1_metrics.csv` | Preserve the numeric metric-by-index table and its mixed, documented metric units. |
| Analytics `calendar_year_returns.csv` | Preserve percentage units, two-decimal rounding, benchmark label, and asterisk markers for partial years. |
| Analytics `rolling_cagr_chart.csv` | Preserve chart positions, percentile endpoints, and nonnegative custom error-bar magnitudes. |

For data-dependent columns, compatibility means matching the reference for identical inputs and preserving the existing pivot ordering rule for new inputs. Do not hard-code current sector names as the only supported sectors.

## analytics (28 files)

Portable default directory: `outputs/analytics/` under the project root. The original notebooks currently use `../outputs/analytics/`; migration can preserve that location through an explicit output-root override.

| File | Notebook source frame |
|---|---|
| `top10_concentration_monthly.csv` | `monthly_top10_concentration` |
| `holdings_first_latest.csv` | `holdings_first_latest` |
| `growth_1000_full_period.csv` | `growth_1000_full_period` |
| `growth_1000_summary.csv` | `growth_1000_summary` |
| `period_return_summary.csv` | `period_return_summary` |
| `rolling_cagr_distribution.csv` | `rolling_cagr_distribution` |
| `rolling_cagr_chart.csv` | `rolling_cagr_chart` |
| `rolling_60m_cagr_gap_monthly.csv` | `rolling_60m_cagr_gap_monthly` |
| `absolute_drawdown_daily.csv` | `absolute_drawdown_daily` |
| `absolute_drawdown_summary.csv` | `absolute_drawdown_summary` |
| `relative_drawdown_daily.csv` | `relative_drawdown_daily` |
| `relative_drawdown_summary.csv` | `relative_drawdown_summary` |
| `period_analysis.csv` | `period_analysis` |
| `monthly_market_style_states.csv` | `monthly_market_style_states` |
| `market_style_state_matrix.csv` | `market_style_state_matrix` |
| `market_style_performance.csv` | `market_style_performance_summary` |
| `rolling_36m_hml_chart.csv` | `rolling_36m_hml_chart` |
| `factor_exposure_summary.csv` | `factor_exposure_summary` |
| `quarterly_sector_allocation_chart.csv` | `quarterly_sector_allocation_chart` |
| `construction_summary.csv` | `construction_summary` |
| `transaction_cost_sensitivity.csv` | `transaction_cost_chart` |
| `topn_robustness_summary.csv` | `topn_robustness_summary` |
| `quarterly_component_returns.csv` | `quarterly_component_returns` |
| `quarterly_component_attribution.csv` | `quarterly_component_attribution` |
| `quarterly_sector_attribution.csv` | `quarterly_sector_attribution` |
| `quarterly_top_contributor_share.csv` | `quarterly_top_contributor_share` |
| `appendix_a1_metrics.csv` | `appendix_a1_metrics` |
| `calendar_year_returns.csv` | `calendar_year_returns` |

### Ordered headers observed in existing files

**top10_concentration_monthly.csv**

`observation_date`, `universe_date`, `sp500_company_count`, `companies_with_market_cap`, `sp500_total_market_cap`, `top10_total_market_cap`, `top10_market_cap_share`, `top10_market_cap_share_pct`

**holdings_first_latest.csv**

`snapshot`, `date`, `rank`, `ticker`, `company`, `mc_weight_pct`

**growth_1000_full_period.csv**

`Date`, `S&P 500`, `MC`, `EW`, `MC (UCITS)`

**growth_1000_summary.csv**

`index`, `ending_value`, `cagr`, `cagr_gap_vs_sp500_pp`

**period_return_summary.csv**

`period`, `index`, `total_return`, `cagr`, `cagr_gap_vs_sp500_pp`

**rolling_cagr_distribution.csv**

`horizon`, `horizon_months`, `strategy`, `median_cagr_gap_pp`, `p10_cagr_gap_pp`, `p90_cagr_gap_pp`, `win_rate_pct`, `n_windows`

**rolling_cagr_chart.csv**

`horizon`, `strategy`, `y_position`, `median_x`, `p10_cagr_gap_pp`, `p90_cagr_gap_pp`, `negative_error`, `positive_error`, `win_rate_pct`, `n_windows`

**rolling_60m_cagr_gap_monthly.csv**

`Date`, `MC`, `EW`, `MC (UCITS)`

**absolute_drawdown_daily.csv**

`Date`, `S&P 500`, `MC`, `EW`, `MC (UCITS)`

**absolute_drawdown_summary.csv**

`index`, `max_loss_pct`, `peak`, `trough`, `recovery`

**relative_drawdown_daily.csv**

`Date`, `MC Relative Wealth`, `MC Relative Drawdown`, `EW Relative Wealth`, `EW Relative Drawdown`, `MC (UCITS) Relative Wealth`, `MC (UCITS) Relative Drawdown`

**relative_drawdown_summary.csv**

`strategy`, `worst_relative_drawdown_pct`, `peak`, `trough`, `recovery`, `longest_completed_underperformance_days`, `current_open_underperformance_days`, `current_open_censored`, `longest_completed_underperformance_years`, `current_open_underperformance_years`

**period_analysis.csv**

`period_number`, `phase`, `period_name`, `start_date`, `end_date`, `calendar_days`, `index`, `total_return`, `annualized_return`, `total_return_gap_vs_sp500_pp`, `annualized_return_gap_vs_sp500_pp`

**monthly_market_style_states.csv**

`month_end`, `sp500_return`, `big_growth_return`, `big_value_return`, `style_spread_pp`, `market_state`, `style_state`, `combined_state`

**market_style_state_matrix.csv**

`Market State`, `Value-Led`, `Neutral Style`, `Growth-Led`

**market_style_performance.csv**

`state`, `months_num`, `MC_mean_active_return_pp`, `MC_win_frequency_pct`, `EW_mean_active_return_pp`, `EW_win_frequency_pct`, `MC (UCITS)_mean_active_return_pp`, `MC (UCITS)_win_frequency_pct`

**rolling_36m_hml_chart.csv**

`Date`, `MC`, `MC CI Low`, `MC CI High`, `S&P 500`

**factor_exposure_summary.csv**

`index`, `first_hml_beta`, `latest_hml_beta`, `median_hml_beta`, `minimum_hml_beta`, `maximum_hml_beta`, `pct_windows_growth_sensitive`, `latest_hml_ci95_low`, `latest_hml_ci95_high`

**quarterly_sector_allocation_chart.csv**

`Date`, `Communication Services`, `Consumer Cyclical`, `Consumer Defensive`, `Energy`, `Financial Services`, `Healthcare`, `Industrials`, `Technology`

**construction_summary.csv**

`index`, `cagr`, `max_issuer_weight_pct`, `worst_relative_drawdown_pct`, `annualized_one_way_turnover_pct`, `cagr_gap_vs_mc_pp`

**transaction_cost_sensitivity.csv**

`Cost (bps)`, `MC`, `EW`, `MC (UCITS)`

**topn_robustness_summary.csv**

`portfolio`, `top_n`, `full_period_cagr`, `cagr_gap_vs_sp500_pp`, `five_year_win_frequency_pct`, `worst_relative_drawdown_pct`, `max_issuer_weight_pct`

**quarterly_component_returns.csv**

`quarter`, `quarter_start`, `quarter_end`, `ticker`, `company`, `sector`, `held_days`, `quarter_trading_days`, `start_weight_pct`, `average_weight_pct`, `end_weight_pct`, `component_total_return_pct`, `return_rank`, `portfolio_total_return_pct`

**quarterly_component_attribution.csv**

`quarter`, `quarter_start`, `quarter_end`, `ticker`, `company`, `sector`, `start_weight_pct`, `average_weight_pct`, `end_weight_pct`, `component_total_return_pct`, `exact_contribution_pp`, `contribution_rank`, `share_of_portfolio_return_pct`, `portfolio_total_return_pct`

**quarterly_sector_attribution.csv**

`quarter`, `quarter_start`, `quarter_end`, `sector`, `component_count`, `start_sector_weight_pct`, `average_sector_weight_pct`, `end_sector_weight_pct`, `exact_contribution_pp`, `sector_contribution_rank`, `share_of_portfolio_return_pct`, `portfolio_total_return_pct`

**quarterly_top_contributor_share.csv**

`quarter`, `quarter_start`, `quarter_end`, `portfolio_total_return_pct`, `top1_contribution_pp`, `top1_share_of_portfolio_return_pct`, `top1_leaders`, `top3_contribution_pp`, `top3_share_of_portfolio_return_pct`, `top3_leaders`, `top5_contribution_pp`, `top5_share_of_portfolio_return_pct`, `top5_leaders`

**appendix_a1_metrics.csv**

`Metric`, `S&P 500`, `MC`, `EW`, `MC (UCITS)`

**calendar_year_returns.csv**

`Year`, `S&P 500 TR`, `MC`, `EW`, `MC (UCITS)`

## factor_attribution (10 files)

Portable default directory: `outputs/factor_attribution/` under the project root. The original notebooks currently use `../outputs/factor_attribution/`; migration can preserve that location through an explicit output-root override.

| File | Notebook source frame |
|---|---|
| `rolling_36m_hml_chart.csv` | `rolling_36m_hml_chart` |
| `factor_exposure_summary.csv` | `factor_exposure_summary` |
| `style_environment_period_compare.csv` | `style_environment_period_compare` |
| `style_environment_state_mix.csv` | `style_environment_state_mix` |
| `active_return_regression_by_period.csv` | `active_return_regression_by_period` |
| `recent_factor_attribution.csv` | `recent_factor_attribution` |
| `rolling_factor_adjusted_performance.csv` | `rolling_factor_adjusted_performance` |
| `factor_adjusted_persistence_summary.csv` | `factor_adjusted_persistence_summary` |
| `factor_model_robustness_recent_10y.csv` | `factor_model_robustness_recent_10y` |
| `ff5_momentum_alpha_by_strategy_period.csv` | `ff5_momentum_alpha_by_strategy_period` |

### Ordered headers observed in existing files

**rolling_36m_hml_chart.csv**

`Date`, `MC`, `MC CI Low`, `MC CI High`, `S&P 500`

**factor_exposure_summary.csv**

`index`, `first_hml_beta`, `latest_hml_beta`, `median_hml_beta`, `minimum_hml_beta`, `maximum_hml_beta`, `pct_windows_growth_sensitive`, `latest_hml_ci95_low`, `latest_hml_ci95_high`

**style_environment_period_compare.csv**

`period`, `start_date`, `end_date`, `n_months`, `big_growth_cagr`, `big_value_cagr`, `growth_minus_value_cagr_gap`, `growth_minus_value_ann_mean`, `hml_ann_mean`, `mc_cagr`, `sp500_cagr`, `cagr_gap`, `active_return_ann_mean`, `value_led_months`, `neutral_style_months`, `growth_led_months`, `pct_value_led_months`, `pct_neutral_style_months`, `pct_growth_led_months`

**style_environment_state_mix.csv**

`Period`, `Value-Led`, `Neutral Style`, `Growth-Led`

**active_return_regression_by_period.csv**

`model`, `period`, `start_date`, `end_date`, `n_months`, `active_return_monthly_mean`, `active_return_ann_mean`, `alpha_monthly`, `alpha_annualized`, `alpha_hac3_se`, `alpha_tstat`, `alpha_pvalue`, `alpha_ci95_low_annualized`, `alpha_ci95_high_annualized`, `r_squared`, `adjusted_r_squared`, `beta_mkt`, `mkt_hac3_se`, `mkt_tstat`, `mkt_pvalue`, `mkt_ci95_low`, `mkt_ci95_high`, `beta_smb`, `smb_hac3_se`, `smb_tstat`, `smb_pvalue`, `smb_ci95_low`, `smb_ci95_high`, `beta_hml`, `hml_hac3_se`, `hml_tstat`, `hml_pvalue`, `hml_ci95_low`, `hml_ci95_high`, `beta_rmw`, `rmw_hac3_se`, `rmw_tstat`, `rmw_pvalue`, `rmw_ci95_low`, `rmw_ci95_high`, `beta_cma`, `cma_hac3_se`, `cma_tstat`, `cma_pvalue`, `cma_ci95_low`, `cma_ci95_high`, `beta_mom`, `mom_hac3_se`, `mom_tstat`, `mom_pvalue`, `mom_ci95_low`, `mom_ci95_high`, `alpha_significant_5pct`, `hml_significant_5pct`, `mom_significant_5pct`

**recent_factor_attribution.csv**

`component_order`, `component`, `factor`, `component_type`, `coefficient`, `coefficient_hac3_se`, `coefficient_tstat`, `coefficient_pvalue`, `driver_monthly_mean`, `driver_annualized_mean`, `monthly_contribution`, `annualized_contribution`, `is_total`, `model`, `period`, `start_date`, `end_date`, `n_months`, `r_squared`, `adjusted_r_squared`, `alpha_annualized`, `alpha_tstat`, `alpha_pvalue`, `observed_active_return_annualized`, `reconciliation_difference_annualized`

**rolling_factor_adjusted_performance.csv**

`model`, `window_start`, `window_end`, `n_months`, `raw_active_return_monthly_mean`, `raw_active_return_annualized`, `alpha_monthly`, `alpha_annualized`, `alpha_hac3_se`, `alpha_tstat`, `alpha_pvalue`, `alpha_ci95_low_annualized`, `alpha_ci95_high_annualized`, `r_squared`, `adjusted_r_squared`, `systematic_contribution_annualized`, `model_implied_active_return_annualized`, `reconciliation_difference`, `beta_mkt`, `mkt_tstat`, `mkt_pvalue`, `beta_smb`, `smb_tstat`, `smb_pvalue`, `beta_hml`, `hml_tstat`, `hml_pvalue`, `beta_rmw`, `rmw_tstat`, `rmw_pvalue`, `beta_cma`, `cma_tstat`, `cma_pvalue`, `beta_mom`, `mom_tstat`, `mom_pvalue`, `raw_active_return_positive`, `alpha_positive`, `alpha_significant_positive_5pct`, `alpha_significant_negative_5pct`

**factor_adjusted_persistence_summary.csv**

`model`, `rolling_window_months`, `n_windows`, `first_window_end`, `latest_window_end`, `pct_windows_raw_active_positive`, `pct_windows_alpha_positive`, `pct_windows_alpha_significant_positive_5pct`, `pct_windows_alpha_significant_negative_5pct`, `median_raw_active_return_annualized`, `median_alpha_annualized`, `latest_raw_active_return_annualized`, `latest_alpha_annualized`, `latest_alpha_tstat`, `latest_adjusted_r_squared`

**factor_model_robustness_recent_10y.csv**

`model_order`, `model`, `period`, `start_date`, `end_date`, `n_months`, `n_factors`, `active_return_ann_mean`, `alpha_monthly`, `alpha_annualized`, `alpha_hac3_se`, `alpha_tstat`, `alpha_pvalue`, `alpha_ci95_low_annualized`, `alpha_ci95_high_annualized`, `r_squared`, `adjusted_r_squared`, `hml_beta`, `hml_tstat`, `hml_pvalue`, `mom_beta`, `mom_tstat`, `mom_pvalue`

**ff5_momentum_alpha_by_strategy_period.csv**

`model`, `period`, `strategy`, `start_date`, `end_date`, `n_months`, `active_return_ann_mean`, `alpha_monthly`, `alpha_annualized`, `alpha_hac3_se`, `alpha_tstat`, `alpha_pvalue`, `alpha_ci95_low_annualized`, `alpha_ci95_high_annualized`, `r_squared`, `adjusted_r_squared`, `beta_mkt`, `beta_smb`, `beta_hml`, `beta_rmw`, `beta_cma`, `beta_mom`, `alpha_significant_5pct`

## Completion gate

For a fixed input snapshot, a successful migration produces exactly the 28 registered analytics CSVs and 10 registered factor-attribution CSVs with these contracts. Unrelated files already present in the output directories are not deleted. Legacy CSVs not declared by these notebook versions are not silently added to the production registry.

The architecture stage inspected only existing filenames and headers. It did not execute notebooks, export new analytical data, or overwrite existing files.
