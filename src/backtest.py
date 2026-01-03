from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    total_return: float
    volatility: float
    max_drawdown: float
    turnover: float


def walk_forward(scores: pd.DataFrame, prices: pd.DataFrame, cost_bp: float = 10) -> BacktestResult:
    weights = scores.set_index("ticker")["composite"].clip(lower=0)
    weights = weights / weights.sum()
    daily_ret = prices.pct_change().dropna()
    portfolio_ret = (daily_ret * weights).sum(axis=1) - cost_bp / 1e4
    cum = (1 + portfolio_ret).cumprod()
    total = float(cum.iloc[-1] - 1)
    vol = float(portfolio_ret.std() * np.sqrt(252))
    dd = float((cum / cum.cummax() - 1).min())
    return BacktestResult(total_return=total, volatility=vol, max_drawdown=dd, turnover=0.0)


__all__ = ["BacktestResult", "walk_forward"]
