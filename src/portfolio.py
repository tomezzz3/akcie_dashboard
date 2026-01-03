from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from .config import RiskRules


def construct_portfolio(scores: pd.DataFrame, risk: RiskRules, top_n: int = 10) -> pd.DataFrame:
    ranked = scores.sort_values("composite", ascending=False).head(top_n)
    weights = ranked["composite"].clip(lower=0)
    if weights.sum() == 0:
        weights = pd.Series(1.0, index=ranked.index)
    weights = weights / weights.sum()
    weights = weights.clip(upper=risk.single_name_cap)
    weights = weights / weights.sum()
    ranked["weight"] = weights.values
    ranked["defense_cash"] = risk.defense_mode_cash_buffer
    return ranked


def turnover(prev: pd.Series, new: pd.Series) -> float:
    idx = prev.index.union(new.index)
    prev, new = prev.reindex(idx, fill_value=0), new.reindex(idx, fill_value=0)
    return float((prev - new).abs().sum() / 2)


__all__ = ["construct_portfolio", "turnover"]
