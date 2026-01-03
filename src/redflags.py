from __future__ import annotations

from typing import Dict

import pandas as pd


RED_FLAG_RULES = {
    "fcf_negative": "Chronicky záporné FCF",
    "margin_deterioration": "Zhoršující se marže",
    "debt_spike": "Prudký růst dluhu",
    "dividend_trap": "Dividendová past",
    "dilution": "Rostoucí počet akcií",
    "data_gap": "Chybí klíčová data",
}


def evaluate_red_flags(df: pd.DataFrame) -> pd.DataFrame:
    flags = pd.DataFrame(index=df.index)
    flags["fcf_negative"] = df["fcf"] < 0
    flags["margin_deterioration"] = False
    flags["debt_spike"] = df["debt"] > df["cash"] * 3
    flags["dividend_trap"] = (df["div_yield"] > 0.05) & (df["payoutRatio"] > 0.9)
    flags["dilution"] = False
    flags["data_gap"] = df.isna().any(axis=1)
    flags["red_flag_score"] = flags.sum(axis=1)
    return flags.reset_index(drop=True)


def red_flag_penalty(red_flags: pd.DataFrame) -> pd.Series:
    return red_flags["red_flag_score"] * 0.5


def flag_descriptions(row: pd.Series) -> Dict[str, bool]:
    return {name: bool(row[name]) for name in RED_FLAG_RULES if name in row}


__all__ = ["evaluate_red_flags", "red_flag_penalty", "flag_descriptions", "RED_FLAG_RULES"]
