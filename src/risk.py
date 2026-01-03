from __future__ import annotations

import numpy as np
import pandas as pd


def max_drawdown(series: pd.Series) -> float:
    cummax = series.cummax()
    dd = (series / cummax - 1).min()
    return float(dd)


def var_cvar(returns: pd.Series, alpha: float = 0.95) -> tuple[float, float]:
    var = -np.percentile(returns, (1 - alpha) * 100)
    cvar = -returns[returns <= -var].mean()
    return float(var), float(cvar)


def stress_scenarios(price_series: pd.Series) -> pd.DataFrame:
    scenarios = {
        "market_-20": price_series.iloc[-1] * 0.8,
        "rates_+100bp": price_series.iloc[-1] * 0.95,
        "credit_+200": price_series.iloc[-1] * 0.9,
        "usd_+5": price_series.iloc[-1] * 0.97,
        "oil_+20": price_series.iloc[-1] * 1.05,
        "oil_-20": price_series.iloc[-1] * 0.95,
    }
    return pd.DataFrame.from_dict(scenarios, orient="index", columns=["price_projection"])


__all__ = ["max_drawdown", "var_cvar", "stress_scenarios"]
