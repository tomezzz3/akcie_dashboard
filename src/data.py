from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
DB_PATH = CACHE_DIR / "founderquant.db"


@dataclass
class DataQualityReport:
    coverage_ratio: float
    missing_fields: Dict[str, float]
    last_updated: datetime


UNIVERSE_COLUMNS = [
    "ticker",
    "sector",
    "market_cap",
    "adv",
    "country",
]


FAKE_UNIVERSE = pd.DataFrame(
    [
        ("AAPL", "Technology", 2500e9, 80e6, "US"),
        ("MSFT", "Technology", 2200e9, 60e6, "US"),
        ("JNJ", "Healthcare", 450e9, 15e6, "US"),
        ("NESN.SW", "Consumer Staples", 300e9, 5e6, "CH"),
        ("RDSA", "Energy", 180e9, 10e6, "UK"),
    ],
    columns=UNIVERSE_COLUMNS,
)


FAKE_FUNDAMENTALS = pd.DataFrame(
    {
        "ticker": FAKE_UNIVERSE["ticker"],
        "revenue": [380e9, 210e9, 95e9, 93e9, 260e9],
        "ebitda": [130e9, 95e9, 30e9, 25e9, 60e9],
        "fcf": [110e9, 75e9, 20e9, 12e9, 30e9],
        "net_income": [99e9, 70e9, 18e9, 10e9, 25e9],
        "dividend": [15e9, 18e9, 11e9, 8e9, 12e9],
        "shares": [15.8e9, 7.5e9, 2.6e9, 3.1e9, 7.8e9],
        "debt": [110e9, 90e9, 45e9, 25e9, 95e9],
        "cash": [65e9, 40e9, 22e9, 15e9, 30e9],
    }
)
FAKE_PRICES = pd.DataFrame(
    {
        "date": pd.date_range(datetime.today() - timedelta(days=365), periods=252, freq="B"),
        "AAPL": np.cumprod(1 + np.random.default_rng(1).normal(0.0005, 0.02, 252)),
        "MSFT": np.cumprod(1 + np.random.default_rng(2).normal(0.0004, 0.018, 252)),
        "JNJ": np.cumprod(1 + np.random.default_rng(3).normal(0.0003, 0.015, 252)),
        "NESN.SW": np.cumprod(1 + np.random.default_rng(4).normal(0.00025, 0.014, 252)),
        "RDSA": np.cumprod(1 + np.random.default_rng(5).normal(0.00035, 0.022, 252)),
    }
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS decision_log (
            ticker TEXT,
            memo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def load_universe() -> pd.DataFrame:
    return FAKE_UNIVERSE.copy()


def load_prices(tickers: Iterable[str]) -> pd.DataFrame:
    df = FAKE_PRICES[["date", *tickers]].copy()
    df.set_index("date", inplace=True)
    return df


def load_fundamentals(tickers: Iterable[str]) -> pd.DataFrame:
    df = FAKE_FUNDAMENTALS.copy()
    df = df[df["ticker"].isin(tickers)].reset_index(drop=True)
    mcap = dict(zip(FAKE_UNIVERSE["ticker"], FAKE_UNIVERSE["market_cap"]))
    df["market_cap"] = df["ticker"].map(mcap)
    df["ev"] = df["market_cap"] + df["debt"] - df["cash"]
    df["dividendYield"] = df["dividend"] / df["market_cap"]
    df["payoutRatio"] = df["dividend"] / df["net_income"]
    return df


def data_quality(df: pd.DataFrame) -> DataQualityReport:
    missing = df.isna().mean().to_dict()
    coverage = 1 - float(pd.Series(missing).mean())
    return DataQualityReport(
        coverage_ratio=coverage,
        missing_fields=missing,
        last_updated=datetime.utcnow(),
    )


def purge_old_cache(days: int = 30) -> None:
    cutoff = datetime.utcnow() - timedelta(days=days)
    for path in CACHE_DIR.glob("*.parquet"):
        if datetime.utcfromtimestamp(path.stat().st_mtime) < cutoff:
            path.unlink()


__all__ = [
    "load_universe",
    "load_prices",
    "load_fundamentals",
    "data_quality",
    "purge_old_cache",
    "DataQualityReport",
    "get_connection",
]
