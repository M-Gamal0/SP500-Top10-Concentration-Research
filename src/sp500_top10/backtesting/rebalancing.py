"""Backtesting: rebalancing."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import BacktestingConfig


def apply_iterative_caps(
    weights: pd.Series,
    caps: pd.Series,
    tolerance: float = 1e-12,
    max_iterations: int = 100,
) -> pd.Series:
    weights = weights.astype(float).copy()
    caps = caps.astype(float).copy()
    if (weights < 0).any():
        raise ValueError("Weights cannot be negative.")
    if (caps <= 0).any():
        raise ValueError("Caps must be positive.")
    if caps.sum() < 1 - tolerance:
        raise ValueError(f"Cap schedule is infeasible. Total capacity = {caps.sum():.2%}")
    weights = weights / weights.sum()
    locked = pd.Series(False, index=weights.index)
    for _ in range(max_iterations):
        overweight = (weights > caps + tolerance) & ~locked
        if not overweight.any():
            break
        excess_weight = float((weights.loc[overweight] - caps.loc[overweight]).sum())
        weights.loc[overweight] = caps.loc[overweight]
        locked.loc[overweight] = True
        receivers = ~locked
        if not receivers.any():
            raise ValueError("No uncapped constituents are available to receive excess weight.")
        receiver_weight_sum = float(weights.loc[receivers].sum())
        if receiver_weight_sum <= 0:
            raise ValueError("Remaining receiver weight is non-positive.")
        weights.loc[receivers] += weights.loc[receivers] / receiver_weight_sum * excess_weight
    else:
        raise RuntimeError("Capping did not converge.")
    if abs(weights.sum() - 1.0) > tolerance:
        raise ValueError("Final capped weights do not sum to 100%.")
    if (weights > caps + tolerance).any():
        raise ValueError("Final capped weights still exceed their caps.")
    return weights


def review_buffered_20_weights(
    current_weights: pd.Series,
    dominant_breach: float = None,
    other_breach: float = None,
    dominant_cap: float = None,
    other_cap: float = None,
    *,
    config: BacktestingConfig,
):
    DOMINANT_BREACH = config.dominant_breach
    DOMINANT_CAP = config.dominant_cap
    OTHER_BREACH = config.other_breach
    OTHER_CAP = config.other_cap
    if dominant_breach is None:
        dominant_breach = DOMINANT_BREACH
    if other_breach is None:
        other_breach = OTHER_BREACH
    if dominant_cap is None:
        dominant_cap = DOMINANT_CAP
    if other_cap is None:
        other_cap = OTHER_CAP
    current_weights = current_weights.astype(float).copy()
    dominant_ticker = current_weights.idxmax()
    dominant_weight = current_weights.loc[dominant_ticker]
    other_weights = current_weights.drop(index=dominant_ticker)
    breach_detected = dominant_weight > dominant_breach or (other_weights > other_breach).any()
    if not breach_detected:
        return (False, current_weights, dominant_ticker)
    caps = pd.Series(other_cap, index=current_weights.index, dtype=float)
    caps.loc[dominant_ticker] = dominant_cap
    target_weights = apply_iterative_caps(weights=current_weights, caps=caps)
    return (True, target_weights, dominant_ticker)


def build_rebalance_weight_map(
    weights: pd.DataFrame,
    top_n: int,
    weighting_method: str,
    *,
    config: BacktestingConfig,
):
    VALIDATION_TOLERANCE = config.validation_tolerance
    strategy_weights = weights.loc[
        weights["top_n"].eq(top_n) & weights["weighting_method"].eq(weighting_method)
    ].copy()
    if strategy_weights.empty:
        raise ValueError(f"No active weights found for Top {top_n} | {weighting_method}.")
    rebalance_weight_map = {
        effective_date: group.set_index("ticker")["target_weight"].astype(float).sort_index()
        for effective_date, group in strategy_weights.groupby("effective_rebalance_date")
    }
    for date, target_weights in rebalance_weight_map.items():
        if not np.isclose(target_weights.sum(), 1.0, atol=VALIDATION_TOLERANCE):
            raise ValueError(
                f"Target weights do not sum to 100% on {date} for Top {top_n} | {weighting_method}."
            )
    return (strategy_weights, rebalance_weight_map)
