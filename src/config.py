from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


CONFIG_PATH = Path(__file__).resolve().parent.parent / "sample_config.yaml"


@dataclass
class FilterSettings:
    region: Optional[str] = None
    exchanges: List[str] = field(default_factory=list)
    sectors_include: List[str] = field(default_factory=list)
    sectors_exclude: List[str] = field(default_factory=list)
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    adv_min: Optional[float] = None
    dividend_yield_min: Optional[float] = None
    dividend_growth_min: Optional[float] = None
    positive_net_income: bool = True
    positive_fcf: bool = True
    debt_to_equity_max: Optional[float] = None
    net_debt_ebitda_max: Optional[float] = None
    interest_coverage_min: Optional[float] = None
    pe_min: Optional[float] = None
    pe_max: Optional[float] = None
    ev_ebitda_max: Optional[float] = None
    fcf_yield_min: Optional[float] = None
    peg_max: Optional[float] = None
    momentum_12m_min: Optional[float] = None
    trend_filter: bool = True
    beta_cap: Optional[float] = None
    vol_cap: Optional[float] = None
    max_dd_cap: Optional[float] = None
    min_history_years: int = 3
    min_fundamental_completeness: float = 0.7
    exclude_adrs: bool = True
    exclude_penny_stocks: bool = True


@dataclass
class ToggleSettings:
    prefer_dividends: bool = False
    prefer_buybacks: bool = False
    low_beta: bool = False
    low_volatility: bool = False
    hate_debt: bool = False
    avoid_losses: bool = True
    avoid_quality_traps: bool = True
    prefer_pricing_power: bool = False
    avoid_micro_caps: bool = True
    avoid_event_risk: bool = False
    prefer_moat: bool = False
    region_focus: Optional[str] = None
    esg_filter: bool = False


@dataclass
class FactorWeights:
    value: float = 1.0
    quality: float = 1.0
    earnings_quality: float = 1.0
    momentum: float = 1.0
    risk_defensive: float = 1.0
    shareholder_yield: float = 1.0
    growth: float = 0.8


@dataclass
class RiskRules:
    single_name_cap: float = 0.1
    sector_cap: float = 0.3
    turnover_cap: float = 0.3
    defense_mode_cash_buffer: float = 0.1
    dd_kill_switch: float = 0.2
    var_limit: float = 0.1
    cvar_limit: float = 0.15
    beta_cap: float = 1.5


@dataclass
class PresetProfile:
    name: str
    description: str
    weights: FactorWeights
    toggles: ToggleSettings
    filters: FilterSettings
    risk: RiskRules


@dataclass
class AppConfig:
    presets: Dict[str, PresetProfile]
    default_preset: str
    language: str = "cz"

    @staticmethod
    def from_dict(raw: Dict) -> "AppConfig":
        presets: Dict[str, PresetProfile] = {}
        for key, val in raw["presets"].items():
            presets[key] = PresetProfile(
                name=val.get("name", key),
                description=val.get("description", ""),
                weights=FactorWeights(**val.get("weights", {})),
                toggles=ToggleSettings(**val.get("toggles", {})),
                filters=FilterSettings(**val.get("filters", {})),
                risk=RiskRules(**val.get("risk", {})),
            )
        return AppConfig(presets=presets, default_preset=raw.get("default_preset", list(presets)[0]))


def load_app_config(path: Path = CONFIG_PATH) -> AppConfig:
    content = yaml.safe_load(path.read_text())
    return AppConfig.from_dict(content)


__all__ = [
    "FilterSettings",
    "ToggleSettings",
    "FactorWeights",
    "RiskRules",
    "PresetProfile",
    "AppConfig",
    "load_app_config",
    "CONFIG_PATH",
]
