from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation

from .config import FactorWeights, ToggleSettings


def robust_zscore(series: pd.Series) -> pd.Series:
    med = series.median()
    mad = median_abs_deviation(series, scale="normal") or 1e-6
    return (series - med) / mad


def compute_factor_scores(df: pd.DataFrame, weights: FactorWeights, toggles: ToggleSettings) -> Tuple[pd.DataFrame, Dict[str, float]]:
    scores = pd.DataFrame()
    scores["ticker"] = df["ticker"]
    scores["value"] = robust_zscore(-df["ev_ebitda"]) + robust_zscore(df["fcf_yield"]) + robust_zscore(df["earnings_yield"])
    scores["quality"] = robust_zscore(df["roe_proxy"]) + robust_zscore(df["ebitda"])
    scores["earnings_quality"] = robust_zscore(df["fcf"]) - robust_zscore(df["debt"])
    scores["momentum"] = robust_zscore(df["mom_6m"]) + robust_zscore(df["mom_12m"]) - robust_zscore(df["vol_1y"])
    scores["risk_defensive"] = -robust_zscore(df["beta_proxy"]) - robust_zscore(df["max_dd"])
    scores["shareholder_yield"] = robust_zscore(df["div_yield"]) - robust_zscore(df["shares"].pct_change().fillna(0))
    scores["growth"] = robust_zscore(df["revenue"].pct_change().fillna(0))

    adjustments = preference_adjustments(weights, toggles)
    composite = sum(scores[col] * adjustments[col] for col in adjustments)
    scores["composite"] = composite
    return scores, adjustments


def preference_adjustments(weights: FactorWeights, toggles: ToggleSettings) -> Dict[str, float]:
    adj = {
        "value": weights.value,
        "quality": weights.quality,
        "earnings_quality": weights.earnings_quality,
        "momentum": weights.momentum,
        "risk_defensive": weights.risk_defensive,
        "shareholder_yield": weights.shareholder_yield,
        "growth": weights.growth,
    }
    if toggles.prefer_dividends:
        adj["shareholder_yield"] += 0.25
    if toggles.low_beta:
        adj["risk_defensive"] += 0.3
    if toggles.low_volatility:
        adj["risk_defensive"] += 0.2
    if toggles.hate_debt:
        adj["quality"] += 0.2
    if toggles.prefer_pricing_power:
        adj["quality"] += 0.15
    if toggles.prefer_moat:
        adj["quality"] += 0.2
    return adj


__all__ = ["compute_factor_scores", "preference_adjustments", "robust_zscore"]
