from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


def export_report(scores: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(exist_ok=True, parents=True)
    content = scores.to_csv(index=False)
    path.write_text(content)
    return path


def memo_summary(row: pd.Series) -> str:
    bullets = [f"- {row['ticker']}: Composite {row['composite']:.2f}"]
    return "\n".join(bullets)


__all__ = ["export_report", "memo_summary"]
