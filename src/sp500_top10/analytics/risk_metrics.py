"""Analytics: risk metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import AnalyticsConfig


def safe_ratio(numerator, denominator):
    if not np.isfinite(numerator) or not np.isfinite(denominator) or abs(denominator) <= 1e-14:
        return np.nan
    return float(numerator / denominator)


def max_drawdown_from_wealth(wealth):
    wealth = np.asarray(wealth, dtype=float)
    running_peak = np.maximum.accumulate(wealth)
    drawdown = wealth / running_peak - 1
    return float(drawdown.min())


def monthly_capture(strategy_returns, benchmark_returns):
    aligned = pd.concat(
        [strategy_returns.rename("strategy"), benchmark_returns.rename("benchmark")],
        axis=1,
    ).dropna()
    up_months = aligned.loc[aligned["benchmark"] > 0]
    down_months = aligned.loc[aligned["benchmark"] < 0]
    up_capture = safe_ratio(up_months["strategy"].mean(), up_months["benchmark"].mean())
    down_capture = safe_ratio(down_months["strategy"].mean(), down_months["benchmark"].mean())
    return (up_capture, down_capture)


def prepare_risk_returns(growth_1000_wide, *, config: AnalyticsConfig):
    """Calculate risk metrics with explicit inputs; preserve legacy conventions."""
    A1_INDEX_ORDER = config.a1_index_order
    a1_levels = (
        growth_1000_wide[["date", "S&P 500", "MC", "EW", "MC (UCITS)"]]
        .sort_values("date")
        .reset_index(drop=True)
        .copy()
    )
    a1_returns = a1_levels.set_index("date")[A1_INDEX_ORDER].pct_change()
    return (a1_levels, a1_returns)


def calculate_risk_metrics(a1_levels, a1_returns, risk_free_a1_input, *, config: AnalyticsConfig):
    """Calculate risk metrics with explicit inputs; preserve legacy conventions."""
    A1_INDEX_ORDER = config.a1_index_order
    A1_METRICS = config.a1_metrics
    CAPTURE_METRICS = config.capture_metrics
    PERCENT_METRICS = config.percent_metrics
    TRADING_DAYS_PER_YEAR = config.trading_days_per_year
    risk_free_a1 = risk_free_a1_input
    risk_free_a1["date"] = pd.to_datetime(risk_free_a1["date"])
    if risk_free_a1["date"].duplicated().any():
        raise ValueError("Duplicate dates detected in risk_free_daily.")
    risk_free_a1 = risk_free_a1.set_index("date")["daily_risk_free_return"]
    daily_analysis = a1_returns.join(risk_free_a1.rename("rf"), how="left").dropna(
        subset=A1_INDEX_ORDER
    )
    if daily_analysis["rf"].isna().any():
        missing_rf_dates = daily_analysis.loc[daily_analysis["rf"].isna()].index.tolist()
        raise ValueError(
            f"Missing daily risk-free return on {len(missing_rf_dates)} analysis dates."
        )
    monthly_levels_a1 = a1_levels.set_index("date")[A1_INDEX_ORDER].resample("ME").last()
    monthly_returns_a1 = monthly_levels_a1.pct_change().dropna()
    start_date_a1 = a1_levels["date"].iloc[0]
    end_date_a1 = a1_levels["date"].iloc[-1]
    years_a1 = (end_date_a1 - start_date_a1).days / 365.25
    if years_a1 <= 0:
        raise ValueError("Invalid Appendix A1 analysis period.")
    benchmark_return = daily_analysis["S&P 500"]
    benchmark_excess = benchmark_return - daily_analysis["rf"]
    metric_rows = []
    for index_name in A1_INDEX_ORDER:
        daily_return = daily_analysis[index_name]
        excess_return = daily_return - daily_analysis["rf"]
        active_return = daily_return - benchmark_return
        start_value = float(a1_levels[index_name].iloc[0])
        end_value = float(a1_levels[index_name].iloc[-1])
        cumulative_return = end_value / start_value - 1
        cagr = (end_value / start_value) ** (1 / years_a1) - 1
        annualized_volatility = daily_return.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
        sharpe_ratio = safe_ratio(excess_return.mean(), excess_return.std(ddof=1)) * np.sqrt(
            TRADING_DAYS_PER_YEAR
        )
        downside_excess = np.minimum(excess_return.to_numpy(dtype=float), 0)
        downside_deviation = np.sqrt(np.mean(downside_excess**2))
        sortino_ratio = safe_ratio(excess_return.mean(), downside_deviation) * np.sqrt(
            TRADING_DAYS_PER_YEAR
        )
        max_drawdown = max_drawdown_from_wealth(a1_levels[index_name])
        calmar_ratio = safe_ratio(cagr, abs(max_drawdown))
        benchmark_variance = benchmark_excess.var(ddof=1)
        if np.isfinite(benchmark_variance) and benchmark_variance > 1e-14:
            beta = np.cov(excess_return, benchmark_excess, ddof=1)[0, 1] / benchmark_variance
        else:
            beta = np.nan
        daily_capm_alpha = (
            excess_return.mean() - beta * benchmark_excess.mean() if np.isfinite(beta) else np.nan
        )
        annualized_capm_alpha = (
            daily_capm_alpha * TRADING_DAYS_PER_YEAR if np.isfinite(daily_capm_alpha) else np.nan
        )
        tracking_error = active_return.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
        information_ratio = safe_ratio(active_return.mean(), active_return.std(ddof=1)) * np.sqrt(
            TRADING_DAYS_PER_YEAR
        )
        correlation = daily_return.corr(benchmark_return)
        up_capture, down_capture = monthly_capture(
            monthly_returns_a1[index_name], monthly_returns_a1["S&P 500"]
        )
        daily_skewness = daily_return.skew()
        daily_excess_kurtosis = daily_return.kurt()
        metric_rows.append(
            {
                "index": index_name,
                "cumulative_return": cumulative_return,
                "cagr": cagr,
                "annualized_volatility": annualized_volatility,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "calmar_ratio": calmar_ratio,
                "max_drawdown": max_drawdown,
                "beta_vs_sp500": beta,
                "capm_alpha": annualized_capm_alpha,
                "tracking_error": tracking_error,
                "information_ratio": information_ratio,
                "correlation_vs_sp500": correlation,
                "up_capture": up_capture,
                "down_capture": down_capture,
                "daily_return_skewness": daily_skewness,
                "daily_excess_kurtosis": daily_excess_kurtosis,
            }
        )
    a1_metric_summary = pd.DataFrame(metric_rows)
    benchmark_mask = a1_metric_summary["index"].eq("S&P 500")
    a1_metric_summary.loc[benchmark_mask, "beta_vs_sp500"] = 1.0
    a1_metric_summary.loc[benchmark_mask, "capm_alpha"] = 0.0
    a1_metric_summary.loc[benchmark_mask, "tracking_error"] = 0.0
    a1_metric_summary.loc[benchmark_mask, "information_ratio"] = np.nan
    a1_metric_summary.loc[benchmark_mask, "correlation_vs_sp500"] = 1.0
    a1_metric_summary.loc[benchmark_mask, "up_capture"] = 1.0
    a1_metric_summary.loc[benchmark_mask, "down_capture"] = 1.0
    a1_rows = []
    for metric_label, metric_column in A1_METRICS:
        row = {"Metric": metric_label}
        for index_name in A1_INDEX_ORDER:
            row[index_name] = a1_metric_summary.loc[
                a1_metric_summary["index"].eq(index_name), metric_column
            ].iloc[0]
        a1_rows.append(row)
    appendix_a1_metrics = pd.DataFrame(a1_rows)
    if len(appendix_a1_metrics) != len(A1_METRICS):
        raise ValueError("Appendix A1 metric count mismatch.")
    if list(appendix_a1_metrics.columns) != [
        "Metric",
        "S&P 500",
        "MC",
        "EW",
        "MC (UCITS)",
    ]:
        raise ValueError("Appendix A1 column order is incorrect.")
    appendix_a1_metrics_display = appendix_a1_metrics.copy()
    appendix_a1_metrics_display[A1_INDEX_ORDER] = appendix_a1_metrics_display[
        A1_INDEX_ORDER
    ].astype(object)
    for row_idx, row in appendix_a1_metrics_display.iterrows():
        metric = row["Metric"]
        for index_name in A1_INDEX_ORDER:
            value = row[index_name]
            if pd.isna(value):
                formatted = "—"
            elif metric in PERCENT_METRICS:
                formatted = f"{value:.2%}"
            elif metric in CAPTURE_METRICS:
                formatted = f"{value:.1%}"
            else:
                formatted = f"{value:.2f}"
            appendix_a1_metrics_display.loc[row_idx, index_name] = formatted
    return (appendix_a1_metrics,)
