# ValueRadar

ValueRadar is a Streamlit application that ranks US equities using an interpretable multi-factor model with a GARP overlay.

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

Optional: set `OPENAI_API_KEY` for AI commentary.

## Project Structure
- `app.py` – Streamlit UI
- `data.py` – data download and preprocessing
- `scoring.py` – factor scoring model
- `ui_components.py` – reusable UI widgets
- `report.py` – PDF export utilities
- `config/` – default universe and scoring configuration
- `assets/` – CSS styles
- `tests/` – unit tests

## Tests

```bash
pytest
```

## Strategy Blueprint (CZ)

Komplexní návrh investiční/trading strategie a architektury aplikace je v `docs/INVESTMENT_SIGNAL_STRATEGY_CZ.md`.
