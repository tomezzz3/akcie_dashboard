from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from .data import get_connection


@dataclass
class Memo:
    ticker: str
    thesis: List[str]
    catalysts: List[str]
    risks: List[str]
    kills: List[str]
    sizing: str
    exit_plan: str


MEMO_TEMPLATE = {
    "Thesis": ["produkt s pricing power", "disciplinovaná alokace kapitálu"],
    "Why now": ["valuace pod historickým průměrem", "relativně silný momentum"],
    "Key risks": ["zpomalení poptávky", "marge tlak"],
    "Kill reasons": ["diluce", "zadlužení roste", "porušení trendu"],
    "Exit plan": ["take-profit při 20%", "stop-loss při -10%"],
}


def peer_table(fundamentals: pd.DataFrame) -> pd.DataFrame:
    cols = ["ticker", "ev_ebitda", "fcf_yield", "earnings_yield", "roe_proxy"]
    return fundamentals[cols]


def memo_to_db(ticker: str, memo: str) -> None:
    conn = get_connection()
    conn.execute("INSERT INTO decision_log (ticker, memo) VALUES (?, ?)", (ticker, memo))
    conn.commit()
    conn.close()


__all__ = ["Memo", "peer_table", "memo_to_db", "MEMO_TEMPLATE"]
