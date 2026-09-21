"""Construction: weighting."""

from __future__ import annotations

import pandas as pd

from ..config import ConstructionConfig


def apply_market_cap_weighting(selected: pd.DataFrame) -> pd.DataFrame:
    weighted = selected.copy()
    total_marketcap = weighted.groupby("selection_date")["resolved_marketcap"].transform("sum")
    if (total_marketcap <= 0).any():
        raise ValueError("At least one selection date has non-positive total market cap.")
    weighted["weighting_method"] = "market_cap"
    weighted["target_weight"] = weighted["resolved_marketcap"] / total_marketcap
    return weighted


def apply_equal_weighting(selected: pd.DataFrame) -> pd.DataFrame:
    weighted = selected.copy()
    holdings_per_date = weighted.groupby("selection_date")["ticker"].transform("count")
    weighted["weighting_method"] = "equal_weight"
    weighted["target_weight"] = 1 / holdings_per_date
    return weighted


def build_cap_schedule(
    selected: pd.DataFrame,
    dominant_cap: float = None,
    other_cap: float = None,
    *,
    config: ConstructionConfig,
) -> pd.Series:
    DOMINANT_CAP = config.dominant_cap
    OTHER_CAP = config.other_cap
    if dominant_cap is None:
        dominant_cap = DOMINANT_CAP
    if other_cap is None:
        other_cap = OTHER_CAP
    return pd.Series(
        [dominant_cap if rank == 1 else other_cap for rank in selected["rank"]],
        index=selected.index,
        dtype=float,
    )


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
            raise ValueError("No uncapped constituents available to receive excess weight.")
        receiver_weight_sum = float(weights.loc[receivers].sum())
        if receiver_weight_sum <= 0:
            raise ValueError("Remaining receiver weight is non-positive.")
        weights.loc[receivers] += weights.loc[receivers] / receiver_weight_sum * excess_weight
    else:
        raise RuntimeError("Capping did not converge.")
    if abs(weights.sum() - 1.0) > tolerance:
        raise ValueError(f"Final weights do not sum to 1. Sum = {weights.sum():.12f}")
    if (weights > caps + tolerance).any():
        raise ValueError("Final weights still exceed their caps.")
    return weights


def apply_buffered_20_weighting(
    selected: pd.DataFrame,
    dominant_cap: float = None,
    other_cap: float = None,
    *,
    config: ConstructionConfig,
) -> pd.DataFrame:
    DOMINANT_CAP = config.dominant_cap
    OTHER_CAP = config.other_cap
    WEIGHT_TOLERANCE = config.weight_tolerance
    if dominant_cap is None:
        dominant_cap = DOMINANT_CAP
    if other_cap is None:
        other_cap = OTHER_CAP
    weighted = apply_market_cap_weighting(selected)
    weighted = weighted.rename(columns={"target_weight": "base_weight"})
    capped_groups = []
    for _, group in weighted.groupby("selection_date", sort=True):
        group = group.copy()
        group["weight_cap"] = build_cap_schedule(
            group, dominant_cap=dominant_cap, other_cap=other_cap, config=config
        )
        group["target_weight"] = apply_iterative_caps(
            weights=group["base_weight"], caps=group["weight_cap"]
        )
        group["initial_cap_breach"] = group["base_weight"] > group["weight_cap"] + 1e-12
        group["cap_binding"] = (
            group["target_weight"] - group["weight_cap"]
        ).abs() <= WEIGHT_TOLERANCE
        group["weight_change"] = group["target_weight"] - group["base_weight"]
        group["weighting_method"] = "buffered_20"
        capped_groups.append(group)
    return pd.concat(capped_groups, ignore_index=True)
