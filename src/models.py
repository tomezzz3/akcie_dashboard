from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy.special import expit


def probability_from_score(score: pd.Series) -> pd.Series:
    calibrated = expit(0.5 * score)
    return pd.Series(calibrated, index=score.index)


def bootstrap_confidence(returns: pd.Series, horizon_days: int = 63, n_boot: int = 200) -> Tuple[float, Tuple[float, float]]:
    rng = np.random.default_rng(42)
    boot = []
    for _ in range(n_boot):
        sample = returns.sample(n=horizon_days, replace=True, random_state=rng)
        boot.append(sample.mean())
    mean = float(np.mean(boot))
    lower, upper = np.percentile(boot, [5, 95]).tolist()
    return mean, (lower, upper)


def confidence_score(data_quality: float, liquidity: float, stability: float) -> float:
    return float(0.4 * data_quality + 0.3 * liquidity + 0.3 * stability)


__all__ = ["probability_from_score", "bootstrap_confidence", "confidence_score"]
