# ROZŠÍŘENÝ DASHBOARD S TOP AKCIEMI, HEATMAPOU A EXPORTEM
import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📈 Akciový přehled se skóre, grafem a filtrováním")

@st.cache_data(show_spinner=False)
def get_all_tickers():
    sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    sp500 = pd.read_html(sp500_url)[0]["Symbol"].tolist()
    ceske = ["CEZ.PR", "KOMB.PR", "MONET.PR"]
    lse = ["HSBA.L", "TSCO.L", "BP.L"]
    return ceske + lse + sp500[:100]

@st.cache_data(show_spinner=False)
def get_stock_info(ticker):
    try:
        data = yf.Ticker(ticker)
        info = data.info
        return {
            "Ticker": ticker,
            "Název": info.get("longName"),
            "Burza": ticker.split(".")[-1] if "." in ticker else "USA",
            "Sektor": info.get("sector"),
            "P/E": info.get("trailingPE"),
            "ROE": info.get("returnOnEquity"),
            "EPS": info.get("trailingEps"),
            "Div. výnos (%)": info.get("dividendYield", 0) * 100,
            "D/E poměr": info.get("debtToEquity"),
            "Free Cash Flow": info.get("freeCashflow"),
            "Beta": info.get("beta"),
            "Market Cap": info.get("marketCap"),
            "Popis": info.get("longBusinessSummary"),
            "Růstová fáze": classify_phase(info),
            "Skóre": calculate_score(info)
        }
    except:
        return None

def classify_phase(info):
    eps = info.get("trailingEps", 0)
    roe = info.get("returnOnEquity", 0)
    mc = info.get("marketCap", 0)
    if eps > 2 and roe > 0.15:
        return "📈 Růstová"
    elif mc > 5e10:
        return "🏦 Stabilní"
    else:
        return "💎 Hodnotová"

def calculate_score(info):
    score = 0
    if info.get("trailingPE") and info["trailingPE"] < 15:
        score += 1
    if info.get("returnOnEquity") and info["returnOnEquity"] > 0.1:
        score += 1
    if info.get("dividendYield") and info["dividendYield"] > 0.03:
        score += 1
    if info.get("debtToEquity") and info["debtToEquity"] < 1:
        score += 1
    if info.get("freeCashflow") and info["freeCashflow"] > 0:
        score += 1
    return score

with st.spinner("Načítám data o akciích..."):
    tickers = get_all_tickers()
    data = [get_stock_info(t) for t in tickers]
    df = pd.DataFrame([d for d in data if d])

# Formátování
df["ROE"] = df["ROE"] * 100
for col in ["ROE", "Div. výnos (%)"]:
    df[col] = df[col].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
df["Free Cash Flow"] = df["Free Cash Flow"].map(lambda x: f"{x/1e6:.0f} mil." if pd.notnull(x) else "N/A")
df["Market Cap"] = df["Market Cap"].map(lambda x: f"{x/1e9:.1f} mld." if pd.notnull(x) else "N/A")

# Filtrování
st.sidebar.header("🔍 Filtrování")
sector_filter = st.sidebar.multiselect("Sektor", options=sorted(df["Sektor"].dropna().unique()))
burza_filter = st.sidebar.multiselect("Burza", options=sorted(df["Burza"].unique()))
faze_filter = st.sidebar.multiselect("Fáze firmy", options=sorted(df["Růstová fáze"].unique()))
skore_min = st.sidebar.slider("Minimální skóre", 0, 5, 3)

filtered = df.copy()
if sector_filter:
    filtered = filtered[filtered["Sektor"].isin(sector_filter)]
if burza_filter:
    filtered = filtered[filtered["Burza"].isin(burza_filter)]
if faze_filter:
    filtered = filtered[filtered["Růstová fáze"].isin(faze_filter)]
filtered = filtered[filtered["Skóre"] >= skore_min]

# Tabulka
st.subheader("📋 Seznam akcií")
st.dataframe(filtered.set_index("Ticker"), use_container_width=True, height=500)

# TOP akcie
st.markdown("---")
st.markdown("### 🏆 TOP 10 akcií podle skóre")
top10 = df.sort_values("Skóre", ascending=False).head(10)
st.table(top10[["Ticker", "Název", "Skóre", "Sektor", "Burza"]])

# Výběr detailu
st.markdown("---")
ticker_select = st.selectbox("📌 Vyber akcii pro detaily:", options=filtered["Ticker"].tolist())
info = df[df["Ticker"] == ticker_select].iloc[0]

st.markdown(f"### {info['Název']} ({info['Ticker']})")
st.caption(info["Popis"])

# Graf vývoje ceny
st.subheader("📊 Vývoj ceny akcie")
period_map = {"1 rok": "1y", "6 měsíců": "6mo", "3 roky": "3y", "5 let": "5y", "10 let": "10y"}
period_option = st.selectbox("Zvol období:", options=list(period_map.keys()), index=0)

hist = yf.Ticker(ticker_select).history(period=period_map[period_option])
fig = px.line(hist, x=hist.index, y="Close", title="Vývoj ceny", labels={"Close": "Cena", "Date": "Datum"})
st.plotly_chart(fig, use_container_width=True)

# Export
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("📥 Export do CSV", data=csv, file_name="akcie_prehlad.csv", mime="text/csv")

st.caption("Data: Yahoo Finance + Wikipedia")
