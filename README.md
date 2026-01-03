# FounderQuant

FounderQuant je osobní buy-side nástroj (Streamlit) zaměřený na transparentní, pravděpodobnostní signály pro akcie. Návrh respektuje capital-preservation, vyhýbá se biasům a všechny výstupy jsou "kandidáti k dalšímu zkoumání" s jasnými důvody i kill reasons.

## Hlavní stavební bloky
- **Preference layer**: preset profily, toggly, filtry a risk pravidla s transparentními dopady na váhy faktorů.
- **Data a bias kontrola**: lokální cache/SQLite decision log, syntetická data pro offline demo (nahraditelné yfinance/FRED), data-quality report zvyšuje/nižuje confidence.
- **Multi-faktor + makro + risk**: robustní z-score, red flags, makro režimy a úpravy vah, penalizace rizika a nákladů.
- **Probabilistické výstupy**: kalibrovaná P(outperform), bootstrap CI, confidence skóre.
- **Portfolio & defense mode**: sizing s capy, cash buffer, stress scénáře, kill-switch metriky.
- **Analyst workspace**: peers & multiples, memo šablona a uložení do decision logu.

## Struktura repozitáře
- `app.py` – Streamlit UI (CZ/EN copy-ready), obsahuje Market Radar, Screener & Ranking, Analyst Workspace, Portfolio Builder, Backtest Lab, Report & Decision Log a Preferences & Filters.
- `sample_config.yaml` – preset profily a výchozí váhy/filtry/risk pravidla.
- `src/config.py` – datové třídy a loader konfigurace.
- `src/data.py` – ingest + syntetický offline dataset, cache/SQLite decision log, data-quality report.
- `src/features.py` – výpočet cenových/fundamentálních/makro feature proxy.
- `src/factors.py` – robustní z-score a multi-faktor skóre s úpravou podle preferencí.
- `src/preferences.py` – přehled presetů a efektů toggle/filtrů.
- `src/redflags.py` – red flag detekce + penalizace.
- `src/macro.py` – makro režimy a citlivostní proxy.
- `src/models.py` – převod skóre na pravděpodobnost, bootstrap intervaly, confidence.
- `src/portfolio.py` – návrh vah s capy a cash bufferem.
- `src/risk.py` – VaR/CVaR, drawdown a stress scénáře proxy.
- `src/backtest.py` – jednoduchý walk-forward backtest (synthetic demo).
- `src/analyst.py` – peers tabulka a memo persistence do SQLite.
- `src/report.py` – export reportu (CSV placeholder) a memo shrnutí.
- `src/alerts.py` – alert rules engine stub.

## Spuštění lokálně
```bash
pip install -r requirements.txt
streamlit run app.py
```

> Poznámka: Aktuálně běží na syntetických datech pro offline demo. Pro produkční nasazení nahraď ingestion ve `src/data.py` (yfinance/FRED) a přidej realné risk kontroly (embargo/purged split, likvidita, náklady).

## Streamlit Cloud
1. Forkni repozitář a propoj ho ve Streamlit Cloud.
2. Ujisti se, že `requirements.txt` obsahuje všechny závislosti.
3. V `sample_config.yaml` můžeš upravit výchozí preset a risk pravidla.

## Limity a bias guardrails
- Žádné jistoty: všude zobrazujeme P(outperform) + CI + confidence.
- Pokud chybí data, confidence klesá a red flag „data_gap“ penalizuje skóre.
- Syntetický backtest je pouze ilustrativní – pro reálné testy přidej walk-forward s purged/embargo split a nákladovým modelem.
- Defense mode: sleduj max drawdown/VAR/CVAR a capy vah; alerty upozorní na risk-off režim nebo red flagy.
