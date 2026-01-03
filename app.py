import sys
from pathlib import Path

import pandas as pd
import streamlit as st

SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.append(str(SRC_DIR))

from config import load_app_config
from data import data_quality, load_fundamentals, load_prices, load_universe
from features import compute_fundamental_features, compute_macro_features, compute_price_features
from factors import compute_factor_scores
from preferences import list_presets, preset_effects, toggle_summary
from macro import infer_regime, macro_adjustment, macro_sensitivity
from redflags import RED_FLAG_RULES, evaluate_red_flags, flag_descriptions, red_flag_penalty
from models import bootstrap_confidence, confidence_score, probability_from_score
from portfolio import construct_portfolio
from risk import max_drawdown, stress_scenarios, var_cvar
from backtest import walk_forward
from analyst import MEMO_TEMPLATE, memo_to_db, peer_table
from report import export_report
from alerts import generate_alerts


st.set_page_config(page_title="FounderQuant", layout="wide")


def sidebar_preferences(cfg):
    st.sidebar.header("Preference Layer")
    preset_key = st.sidebar.selectbox("Preset profil", options=list(cfg.presets.keys()), format_func=lambda k: cfg.presets[k].name)
    preset = cfg.presets[preset_key]
    st.sidebar.caption(preset.description)
    st.sidebar.write("Toggles:")
    for name, enabled in preset.toggles.__dict__.items():
        st.sidebar.checkbox(name, value=enabled, key=f"toggle_{name}", disabled=True)
    st.sidebar.write("Risk pravidla")
    st.sidebar.json(preset.risk.__dict__)
    st.sidebar.write("Filtry")
    st.sidebar.json(preset.filters.__dict__)
    return preset


def prepare_dataset(tickers):
    fundamentals = compute_fundamental_features(tickers)
    price_feats = compute_price_features(tickers)
    df = pd.merge(fundamentals, price_feats, on="ticker")
    return df


def apply_filters(df: pd.DataFrame, preset):
    f = preset.filters
    if f.market_cap_min:
        df = df[df["market_cap"] >= f.market_cap_min]
    if f.market_cap_max:
        df = df[df["market_cap"] <= f.market_cap_max]
    if f.dividend_yield_min:
        df = df[df["div_yield"] >= f.dividend_yield_min]
    if f.fcf_yield_min:
        df = df[df["fcf_yield"] >= f.fcf_yield_min]
    if f.ev_ebitda_max:
        df = df[df["ev_ebitda"] <= f.ev_ebitda_max]
    if f.momentum_12m_min:
        df = df[df["mom_12m"] >= f.momentum_12m_min]
    return df


def main():
    cfg = load_app_config()
    preset = sidebar_preferences(cfg)

    st.title("FounderQuant")
    st.write("Probabilistický multi-faktorový radar s ochranou proti biasům")

    universe = load_universe()
    tickers = universe["ticker"].tolist()
    df = prepare_dataset(tickers)
    dq = data_quality(df)
    macro_feats = compute_macro_features()
    regime, regime_probs = infer_regime(macro_feats)

    df = apply_filters(df, preset)
    factor_scores, weights = compute_factor_scores(df, preset.weights, preset.toggles)
    macro_adj = macro_adjustment(regime)
    for k, v in macro_adj.items():
        factor_scores[k] = factor_scores[k] + v
    factor_scores["macro_regime"] = regime
    factor_scores["composite_adj"] = factor_scores["composite"] + sum(macro_adj.values())

    red_flags = evaluate_red_flags(df)
    factor_scores["red_flag_penalty"] = red_flag_penalty(red_flags)
    factor_scores["composite_final"] = factor_scores["composite_adj"] - factor_scores["red_flag_penalty"]
    factor_scores["p_outperform"] = probability_from_score(factor_scores["composite_final"])

    prices = load_prices(df["ticker"])
    returns = prices.pct_change().dropna().mean(axis=1)
    mean_ret, (ci_low, ci_high) = bootstrap_confidence(returns)
    factor_scores["confidence"] = confidence_score(dq.coverage_ratio, liquidity=0.8, stability=0.7)

    portfolio = construct_portfolio(factor_scores, preset.risk, top_n=5)
    bt = walk_forward(factor_scores, prices)
    alerts = generate_alerts(factor_scores, regime_prob=regime_probs.get("risk_off", 0.0), red_flags=red_flags)

    radar, screener, analyst_tab, portfolio_tab, backtest_tab, report_tab, preferences_tab = st.tabs(
        [
            "Market Radar",
            "Screener & Ranking",
            "Analyst Workspace",
            "Portfolio Builder",
            "Backtest Lab",
            "Report & Decision Log",
            "Preferences & Filters",
        ]
    )

    with radar:
        st.subheader("Makro režim a riziko")
        st.metric("Režim", regime)
        st.json(regime_probs)
        st.write("Makro vstupy")
        st.json(macro_feats)
        st.write("Beta citlivost proxy")
        st.json(macro_sensitivity(factor_scores["risk_defensive"].median()))

    with screener:
        st.subheader("Top kandidáti")
        st.write("Composite score = faktorové skóre + makro úprava - risk/red flags")
        display_cols = ["ticker", "composite_final", "p_outperform", "confidence", "macro_regime"]
        st.dataframe(factor_scores[display_cols].sort_values("composite_final", ascending=False))
        st.caption(f"Data coverage: {dq.coverage_ratio:.2f}. Chybějící pole zvyšují nejistotu.")
        st.write("Red flags")
        st.dataframe(red_flags.join(df["ticker"], how="left").set_index("ticker"))

    with analyst_tab:
        st.subheader("Detail tickeru")
        selected = st.selectbox("Ticker", df["ticker"])
        row = df[df["ticker"] == selected].iloc[0]
        st.write("Snapshot")
        st.json({"sector": row.get("sector"), "market_cap": row.get("market_cap"), "beta": row.get("beta_proxy"), "vol": row.get("vol_1y")})
        st.write("Peers & multiples")
        st.dataframe(peer_table(df))
        st.write("Investment memo")
        memo_text = st.text_area("Memo", value="\n".join(MEMO_TEMPLATE["Thesis"]))
        if st.button("Uložit memo"):
            memo_to_db(selected, memo_text)
            st.success("Uloženo do decision logu")

    with portfolio_tab:
        st.subheader("Návrh portfolia")
        st.dataframe(portfolio[["ticker", "weight", "composite_final"]])
        portfolio_prices = prices[portfolio["ticker"]]
        agg_series = (portfolio_prices * portfolio["weight"].values).sum(axis=1)
        st.write("Stress scénáře")
        st.dataframe(stress_scenarios(agg_series))

    with backtest_tab:
        st.subheader("Walk-forward backtest (synthetic)")
        st.metric("Total return", f"{bt.total_return:.1%}")
        st.metric("Volatilita", f"{bt.volatility:.1%}")
        st.metric("Max drawdown", f"{bt.max_drawdown:.1%}")

    with report_tab:
        st.subheader("Export a decision log")
        export_path = export_report(factor_scores, Path("reports/top_candidates.csv"))
        st.download_button("Stáhnout CSV", data=export_path.read_bytes(), file_name="top_candidates.csv")
        st.write("Alerty")
        st.write(alerts)

    with preferences_tab:
        st.subheader("Efekt preferencí")
        st.write("Aktivní preset:", preset.name)
        st.dataframe(preset_effects(preset))
        st.write("Aktuální váhy faktorů")
        st.json(weights)
        st.write("Makro úprava")
        st.json(macro_adj)
        st.caption(toggle_summary(preset.toggles))


if __name__ == "__main__":
    main()
