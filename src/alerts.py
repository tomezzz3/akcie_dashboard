from __future__ import annotations

from typing import List

import pandas as pd


ALERT_RULES = {
    "regime_switch": "P(risk-off) > threshold",
    "score_drop": "Composite score drop > X",
    "red_flag": "Nový red flag",
    "risk_breach": "Portfolio risk breach",
    "earnings": "Earnings event" ,
}


def generate_alerts(scores: pd.DataFrame, regime_prob: float, red_flags: pd.DataFrame, threshold: float = 0.5) -> List[str]:
    alerts: List[str] = []
    if regime_prob > threshold:
        alerts.append("Režim: risk-off pravděpodobnost vysoká")
    drops = scores[scores["composite"] < scores["composite"].median() - 1]
    if not drops.empty:
        alerts.append(f"{len(drops)} tickerů má prudký pokles skóre")
    if red_flags["red_flag_score"].any():
        alerts.append("Byl detekován red flag, zkontroluj detaily")
    return alerts


__all__ = ["generate_alerts", "ALERT_RULES"]
