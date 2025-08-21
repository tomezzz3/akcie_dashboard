"""Data loading and preprocessing utilities for ValueRadar."""
from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Iterable, List

try:  # pragma: no cover - streamlit cache wrappers
    import streamlit as st
except Exception:  # pragma: no cover
    class Mock:
        def cache_data(self, *a, **k):
            def decorator(func):
                return func
            return decorator
    st = Mock()

import yfinance as yf


UNIVERSE_PATH = Path("config/universe.csv")


def load_universe(csv_path: str | Path = UNIVERSE_PATH) -> pd.DataFrame:
    """Load the initial universe of tickers."""
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    return df


@st.cache_data(ttl=60 * 60)
def get_prices(tickers: Iterable[str]) -> pd.DataFrame:
    """Download latest price data for tickers."""
    data = yf.download(list(tickers), period="1y", interval="1d", auto_adjust=True, progress=False, threads=False)
    if isinstance(data, pd.DataFrame) and 'Adj Close' in data:
        data = data['Adj Close']
    return data.tail(1).T.rename(columns=lambda x: 'price')


@st.cache_data(ttl=60 * 60 * 24)
def get_fundamentals(tickers: Iterable[str]) -> pd.DataFrame:
    """Download fundamental data for tickers using yfinance."""
    records: List[dict] = []
    tickers = list(tickers)
    info = yf.Tickers(tickers)
    for t in tickers:
        try:
            d = info.tickers[t].info
        except Exception:
            d = {}
        records.append({
            'ticker': t,
            'sector': d.get('sector'),
            'marketCap': d.get('marketCap'),
            'price': d.get('regularMarketPrice'),
            'pe': d.get('trailingPE'),
            'forward_pe': d.get('forwardPE'),
            'pb': d.get('priceToBook'),
            'ev': d.get('enterpriseValue'),
            'ebitda': d.get('ebitda'),
            'revenue': d.get('totalRevenue'),
            'eps_ttm': d.get('trailingEps'),
            'eps_fwd_growth': d.get('earningsQuarterlyGrowth'),
            'fcf': d.get('freeCashflow'),
            'dividendYield': d.get('dividendYield'),
            'payoutRatio': d.get('payoutRatio'),
            'beta': d.get('beta'),
        })
    return pd.DataFrame(records)


def winsorize_series(s: pd.Series, limits: tuple[float, float]) -> pd.Series:
    """Simple winsorization using quantiles to avoid SciPy dependency."""
    lower = s.quantile(limits[0])
    upper = s.quantile(limits[1])
    return s.clip(lower, upper)


def winsorize_by_sector(df: pd.DataFrame, column: str, limits: tuple[float, float]) -> pd.Series:
    return df.groupby('sector')[column].transform(lambda x: winsorize_series(x, limits))


def compute_sector_medians(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Compute median of columns by sector."""
    med = df.groupby('sector')[list(columns)].median()
    med.columns = [f"median_{c}" for c in med.columns]
    return med


__all__ = [
    'load_universe',
    'get_prices',
    'get_fundamentals',
    'winsorize_series',
    'winsorize_by_sector',
    'compute_sector_medians',
]
