from __future__ import annotations

from typing import Dict, Tuple

import numpy as np


MACRO_REGIMES = ["risk_on", "neutral", "risk_off"]


def infer_regime(macro_features: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
    score = macro_features.get("vol", 0)
    if score > 0.25:
        regime = "risk_off"
    elif score > 0.15:
        regime = "neutral"
    else:
        regime = "risk_on"
    probs = {
        "risk_on": 0.2 if regime != "risk_on" else 0.55,
        "neutral": 0.25 if regime == "risk_on" else 0.45,
        "risk_off": 0.2 if regime == "risk_on" else 0.35,
    }
    return regime, probs


def macro_adjustment(regime: str) -> Dict[str, float]:
    if regime == "risk_on":
        return {"momentum": 0.2, "growth": 0.1, "risk_defensive": -0.15}
    if regime == "risk_off":
        return {"risk_defensive": 0.3, "quality": 0.2, "value": 0.1}
    return {"quality": 0.1}


def macro_sensitivity(beta_market: float) -> Dict[str, float]:
    return {
        "beta_market": beta_market,
        "beta_rates": -0.2 * beta_market,
        "beta_inflation": -0.1 * beta_market,
        "beta_usd": 0.05 * beta_market,
        "beta_credit": 0.15 * beta_market,
    }


__all__ = ["infer_regime", "macro_adjustment", "macro_sensitivity", "MACRO_REGIMES"]
