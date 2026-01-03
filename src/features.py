from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from .data import load_prices, load_fundamentals


def compute_price_features(tickers) -> pd.DataFrame:
    prices = load_prices(tickers)
    returns = prices.pct_change().dropna()
    feats = pd.DataFrame(index=tickers)
    feats["mom_6m"] = returns.tail(126).mean() * 126
    feats["mom_12m"] = returns.tail(252).mean() * 252
    feats["vol_1y"] = returns.tail(252).std() * np.sqrt(252)
    feats["max_dd"] = (prices / prices.cummax() - 1).min()
    feats["beta_proxy"] = feats["vol_1y"] / feats["vol_1y"].median()
    feats.index.name = "ticker"
    return feats.reset_index()


def compute_fundamental_features(tickers) -> pd.DataFrame:
    fund = load_fundamentals(tickers)
    fund["ev_ebitda"] = fund["ev"] / fund["ebitda"]
    fund["fcf_yield"] = fund["fcf"] / fund["market_cap"]
    fund["earnings_yield"] = fund["net_income"] / fund["market_cap"]
    fund["roe_proxy"] = fund["net_income"] / fund["market_cap"]
    fund["net_debt_ebitda"] = (fund["debt"] - fund["cash"]) / fund["ebitda"]
    fund["div_yield"] = fund["dividendYield"]
    return fund


def compute_macro_features() -> Dict[str, float]:
    return {
        "delta_rates": -0.05,
        "slope": -0.15,
        "inflation": 0.03,
        "usd": 0.01,
        "credit": 0.02,
        "vol": 0.18,
    }


__all__ = [
    "compute_price_features",
    "compute_fundamental_features",
    "compute_macro_features",
]
