from __future__ import annotations

from dataclasses import asdict
from typing import Dict

import pandas as pd

from .config import AppConfig, FilterSettings, PresetProfile, ToggleSettings


def list_presets(cfg: AppConfig) -> Dict[str, str]:
    return {key: preset.description for key, preset in cfg.presets.items()}


def preset_effects(preset: PresetProfile) -> pd.DataFrame:
    rows = []
    toggles = asdict(preset.toggles)
    filters = asdict(preset.filters)
    for key, val in toggles.items():
        rows.append({"type": "toggle", "name": key, "value": val})
    for key, val in filters.items():
        rows.append({"type": "filter", "name": key, "value": val})
    rows.append({"type": "risk", "name": "rules", "value": asdict(preset.risk)})
    return pd.DataFrame(rows)


def update_filters(base: FilterSettings, overrides: Dict) -> FilterSettings:
    data = asdict(base)
    data.update(overrides)
    return FilterSettings(**data)


def toggle_summary(toggles: ToggleSettings) -> str:
    enabled = [k for k, v in asdict(toggles).items() if v]
    if not enabled:
        return "Bez speciálních preferencí"
    return ", ".join(enabled)


__all__ = [
    "list_presets",
    "preset_effects",
    "update_filters",
    "toggle_summary",
]
