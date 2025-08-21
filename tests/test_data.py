import pandas as pd
from pathlib import Path

from data import load_universe, compute_sector_medians


def test_load_universe():
    df = load_universe()
    assert 'Ticker' in df.columns and len(df) > 0


def test_compute_sector_medians(tmp_path):
    df = pd.DataFrame({
        'sector': ['A', 'A', 'B'],
        'metric': [1, 3, 2],
    })
    med = compute_sector_medians(df, ['metric'])
    assert med.loc['A', 'median_metric'] == 2
    assert med.loc['B', 'median_metric'] == 2
