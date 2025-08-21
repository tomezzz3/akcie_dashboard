import json
from pathlib import Path

import pandas as pd
import streamlit as st

from data import load_universe, get_fundamentals
from scoring import ScoringConfig, compute_scores, assign_badges
from ui_components import metric_card, badge
from report import export_pdf

CONFIG_PATH = Path('config/scoring.json')


def load_config() -> ScoringConfig:
    cfg = json.loads(Path(CONFIG_PATH).read_text())
    return ScoringConfig.from_dict(cfg)


def prepare_dataframe(fund: pd.DataFrame) -> pd.DataFrame:
    df = fund.copy()
    df['ev_ebitda'] = df['ev'] / df['ebitda']
    df['fcf_yield'] = df['fcf'] / df['marketCap']
    df['rev_cagr'] = df['eps_cagr'] = df['fcf_cagr'] = 0.0
    df['roic'] = df['gm_stability'] = df['int_cover'] = df['accruals'] = 0.0
    df['perf_1m'] = df['perf_3m'] = df['perf_6m'] = df['perf_12m'] = 0.0
    df['dist_52w'] = df['max_dd'] = df['net_debt_ebitda'] = 0.0
    df['div_yield'] = df['dividendYield'].fillna(0)
    df['payout_ratio'] = df['payoutRatio'].fillna(0)
    df['div_cagr'] = 0.0
    df['eps_fwd_growth'] = df['eps_fwd_growth'].fillna(0.1)
    df.rename(columns={'ticker': 'Ticker', 'sector': 'Sector'}, inplace=True)
    return df


def main():
    st.set_page_config(page_title="ValueRadar", layout="wide")
    st.title("ValueRadar")
    st.write("Multi-factor stock screener with GARP overlay")

    cfg = load_config()
    universe = load_universe()
    tickers = universe['Ticker'].head(50).tolist()
    with st.spinner("Downloading data..."):
        fundamentals = get_fundamentals(tickers)
    df = prepare_dataframe(fundamentals)
    scores = compute_scores(df, cfg)
    scores['badges'] = assign_badges(scores)

    col1, col2, col3, col4 = st.columns(4)
    metric_card("Universe size", str(len(scores)))
    metric_card("Median Composite", f"{scores['Composite'].median():.1f}")
    top = scores.sort_values('Composite', ascending=False).iloc[0]
    metric_card("Top pick", f"{top['ticker']} ({top['Composite']:.1f})")
    metric_card("% Undervalued", f"{(scores['M1']>=70).mean()*100:.0f}%")

    st.dataframe(scores[['ticker','Sector','Composite','M1','M2','M3','M4','M5','M6','PEG','badges']].round(2))

    if st.button("Export Top5 PDF"):
        top5 = scores.sort_values('Composite', ascending=False).head(5)
        path = export_pdf(top5, 'top5.pdf')
        with open(path, 'rb') as f:
            st.download_button("Download PDF", f, file_name='top5.pdf')


if __name__ == '__main__':
    main()
