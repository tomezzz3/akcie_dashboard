"""Factor scoring model for ValueRadar."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd
from math import erf, sqrt

from data import winsorize_by_sector

try:  # pragma: no cover - optional dependency
    from sklearn.preprocessing import RobustScaler
except Exception:  # pragma: no cover
    RobustScaler = None

# Prefer pydantic for config validation but fall back to dataclass if unavailable
try:  # pragma: no cover - optional dependency
    from pydantic import BaseModel, field_validator

    class ScoringConfig(BaseModel):
        """Configuration with validation for scoring parameters."""

        weights: Dict[str, float]
        winsor_limits: tuple[float, float]
        peg_bonus_band: tuple[float, float]
        peg_penalty_threshold: float

        @field_validator("weights")
        @classmethod
        def _validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
            expected = {f"M{i}" for i in range(1, 7)}
            missing = expected - v.keys()
            if missing:
                raise ValueError(f"Missing weights for: {sorted(missing)}")
            if sum(v.values()) <= 0:
                raise ValueError("Weights must sum to a positive value")
            return v

        @field_validator("winsor_limits")
        @classmethod
        def _validate_limits(cls, v: tuple[float, float]) -> tuple[float, float]:
            lo, hi = v
            if not (0 <= lo < hi <= 1):
                raise ValueError("winsor_limits must be within [0,1] and lo < hi")
            return v

        @classmethod
        def from_dict(cls, d: Dict) -> "ScoringConfig":
            return cls(**d)

except Exception:  # pragma: no cover

    @dataclass
    class ScoringConfig:
        weights: Dict[str, float]
        winsor_limits: tuple[float, float]
        peg_bonus_band: tuple[float, float]
        peg_penalty_threshold: float

        @classmethod
        def from_dict(cls, d: Dict) -> "ScoringConfig":
            return cls(
                weights=d.get("weights", {}),
                winsor_limits=tuple(d.get("winsor_limits", (0.05, 0.95))),
                peg_bonus_band=tuple(d.get("peg_bonus_band", (0.5, 1.5))),
                peg_penalty_threshold=d.get("peg_penalty_threshold", 2.5),
            )


def _robust_z(x: pd.Series) -> pd.Series:
    """Compute robust z-scores using RobustScaler if available."""
    arr = x.fillna(x.median()).to_numpy()
    if RobustScaler:
        scaler = RobustScaler(with_centering=True, with_scaling=True)
        scaled = scaler.fit_transform(arr.reshape(-1, 1)).ravel() * 1.349
    else:  # fallback using MAD
        median = np.nanmedian(arr)
        mad = np.nanmedian(np.abs(arr - median)) or 1.0
        scaled = (arr - median) / (1.4826 * mad)
    return pd.Series(scaled, index=x.index)


def _score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    z = _robust_z(series.fillna(series.median()))
    # normal CDF using error function (avoid SciPy dependency)
    s = np.array([0.5 * (1 + erf(val / sqrt(2))) * 100 for val in z])
    if not higher_is_better:
        s = 100 - s
    return pd.Series(s, index=series.index).clip(0, 100)


def score_M1(df: pd.DataFrame, cfg: ScoringConfig) -> pd.Series:
    limits = cfg.winsor_limits
    for col in ['ev_ebitda', 'pe', 'pb', 'fcf_yield', 'roe']:
        if col in df:
            df[col] = winsorize_by_sector(df, col, limits)
    df['roe_pb'] = df['roe'] / df['pb']
    metrics = [
        _score(df['ev_ebitda'], higher_is_better=False),
        _score(df['pe'], higher_is_better=False),
        _score(df['roe_pb'], higher_is_better=True),
        _score(df['fcf_yield'], higher_is_better=True),
    ]
    return np.nanmean(metrics, axis=0)


def score_M2(df: pd.DataFrame, cfg: ScoringConfig) -> pd.Series:
    metrics = [
        _score(df['rev_cagr'], True),
        _score(df['eps_cagr'], True),
        _score(df['fcf_cagr'], True),
    ]
    return np.nanmean(metrics, axis=0)


def score_M3(df: pd.DataFrame, cfg: ScoringConfig) -> pd.Series:
    metrics = [
        _score(df['roic'], True),
        _score(-df['gm_stability'], True),  # lower std better
        _score(df['int_cover'], True),
        _score(-df['accruals'], True),
    ]
    return np.nanmean(metrics, axis=0)


def score_M4(df: pd.DataFrame, cfg: ScoringConfig) -> pd.Series:
    perf = (
        0.2 * df['perf_1m'] +
        0.3 * df['perf_3m'] +
        0.3 * df['perf_6m'] +
        0.2 * df['perf_12m']
    )
    metrics = [
        _score(perf, True),
        _score(-df['dist_52w'], True),
    ]
    return np.nanmean(metrics, axis=0)


def score_M5(df: pd.DataFrame, cfg: ScoringConfig) -> pd.Series:
    metrics = [
        _score(df['beta'].sub(1).abs(), False),
        _score(df['max_dd'], False),
        _score(df['net_debt_ebitda'], False),
    ]
    return np.nanmean(metrics, axis=0)


def score_M6(df: pd.DataFrame, cfg: ScoringConfig) -> pd.Series:
    metrics = [
        _score(df['div_yield'], True),
        _score(df['payout_ratio'].pipe(lambda x: 1 - (x - 0.425).abs()), True),
        _score(df['div_cagr'], True),
    ]
    return np.nanmean(metrics, axis=0)


FACTOR_FUNCS = {
    'M1': score_M1,
    'M2': score_M2,
    'M3': score_M3,
    'M4': score_M4,
    'M5': score_M5,
    'M6': score_M6,
}


def compute_scores(df: pd.DataFrame, cfg: ScoringConfig) -> pd.DataFrame:
    out = df.copy()
    for m, func in FACTOR_FUNCS.items():
        out[m] = func(out, cfg)
    w = cfg.weights
    base = sum(out[m] * w.get(m, 0) for m in FACTOR_FUNCS.keys()) / sum(w.values())
    peg = out['pe'] / (out['eps_fwd_growth'] * 100).clip(lower=0.01)
    bonus_low, bonus_high = cfg.peg_bonus_band
    penalty_th = cfg.peg_penalty_threshold
    mult = np.where(peg > penalty_th, 0.9, 1.0)
    mult = np.where((peg >= bonus_low) & (peg <= bonus_high), 1.1, mult)
    out['PEG'] = peg
    out['Composite'] = (base * mult).clip(0, 100)
    return out


def assign_badges(df: pd.DataFrame) -> pd.Series:
    badges = []
    for _, r in df.iterrows():
        b: list[str] = []
        if r['Composite'] >= 75 and 0.5 <= r['PEG'] <= 1.8 and r['M3'] >= 60:
            b.append('GARP Buy')
        if r['M1'] >= 70 and r['M3'] >= 50:
            b.append('Undervalued')
        if r['M6'] >= 70 and 0.25 <= r.get('payout_ratio', 0) <= 0.60:
            b.append('Income')
        if r['M5'] <= 35:
            b.append('High Risk')
        if r['M4'] <= 40 and r['M1'] >= 65 and r['M3'] >= 60:
            b.append('Watchlist')
        badges.append(', '.join(b))
    return pd.Series(badges, index=df.index)


__all__ = [
    'ScoringConfig',
    'compute_scores',
    'assign_badges',
]
