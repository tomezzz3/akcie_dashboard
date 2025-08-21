import json
import pandas as pd
from scoring import ScoringConfig, compute_scores


def sample_df():
    return pd.DataFrame({
        'ticker': ['GOOD', 'BAD'],
        'sector': ['Tech', 'Tech'],
        'ev_ebitda': [5, 15],
        'pe': [10, 40],
        'pb': [2, 8],
        'roe': [0.2, 0.05],
        'fcf_yield': [0.08, 0.01],
        'rev_cagr': [0.15, -0.05],
        'eps_cagr': [0.20, -0.10],
        'fcf_cagr': [0.10, 0.00],
        'roic': [0.18, 0.04],
        'gm_stability': [0.02, 0.10],
        'int_cover': [15, 2],
        'accruals': [0.02, 0.15],
        'perf_1m': [0.05, -0.02],
        'perf_3m': [0.10, -0.05],
        'perf_6m': [0.20, -0.10],
        'perf_12m': [0.30, -0.15],
        'dist_52w': [0.05, 0.30],
        'beta': [1.0, 1.8],
        'max_dd': [0.10, 0.40],
        'net_debt_ebitda': [1.0, 5.0],
        'div_yield': [0.02, 0.00],
        'payout_ratio': [0.40, 0.90],
        'div_cagr': [0.05, -0.02],
        'eps_fwd_growth': [0.15, 0.05],
    })


def peg_df():
    return pd.DataFrame({
        'ticker': ['A', 'B'],
        'sector': ['Tech', 'Tech'],
        'ev_ebitda': [10, 10],
        'pe': [10, 10],
        'pb': [3, 3],
        'roe': [0.15, 0.15],
        'fcf_yield': [0.05, 0.05],
        'rev_cagr': [0.10, 0.10],
        'eps_cagr': [0.10, 0.10],
        'fcf_cagr': [0.10, 0.10],
        'roic': [0.12, 0.12],
        'gm_stability': [0.05, 0.05],
        'int_cover': [10, 10],
        'accruals': [0.05, 0.05],
        'perf_1m': [0.02, 0.02],
        'perf_3m': [0.04, 0.04],
        'perf_6m': [0.06, 0.06],
        'perf_12m': [0.08, 0.08],
        'dist_52w': [0.10, 0.10],
        'beta': [1.0, 1.0],
        'max_dd': [0.20, 0.20],
        'net_debt_ebitda': [2.0, 2.0],
        'div_yield': [0.02, 0.02],
        'payout_ratio': [0.40, 0.40],
        'div_cagr': [0.03, 0.03],
        'eps_fwd_growth': [0.10, 0.20],
    })


def test_composite_ordering():
    cfg = ScoringConfig.from_dict(json.load(open('config/scoring.json')))
    df = sample_df()
    scores = compute_scores(df, cfg)
    assert scores.loc[0, 'Composite'] > scores.loc[1, 'Composite']


def test_peg_penalty_bonus():
    cfg = ScoringConfig.from_dict(json.load(open('config/scoring.json')))
    df = peg_df()
    # stock A high PEG -> penalty, stock B low PEG -> bonus
    df.loc[0, 'pe'] = 40
    df.loc[0, 'eps_fwd_growth'] = 0.05  # PEG = 8
    df.loc[1, 'pe'] = 10
    df.loc[1, 'eps_fwd_growth'] = 0.20  # PEG = 0.5
    scores = compute_scores(df, cfg)
    assert scores.loc[0, 'Composite'] < scores.loc[1, 'Composite']


def test_missing_values_does_not_crash():
    cfg = ScoringConfig.from_dict(json.load(open('config/scoring.json')))
    df = sample_df()
    df.loc[0, 'fcf_yield'] = None
    scores = compute_scores(df, cfg)
    assert not scores['Composite'].isna().any()
