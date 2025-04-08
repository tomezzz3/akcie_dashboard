import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📈 Akciový přehled se skóre, grafem a filtrováním")

@st.cache_data(show_spinner=False)
def get_all_tickers():
    sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]["Symbol"].tolist()
    ceske = ["CEZ.PR", "KOMB.PR", "MONET.PR"]
    lse = ["HSBA.L", "TSCO.L", "BP.L"]
    return ceske + lse + sp500[:100]

@st.cache_data(show_spinner=False)
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = stock.history(period="1d")["Close"][-1]
        return {
            "Ticker": ticker,
            "Název": info.get("longName"),
            "Burza": ticker.split(".")[-1] if "." in ticker else "USA",
            "Sektor": info.get("sector"),
            "Cena": price,
            "P/E": info.get("trailingPE"),
            "ROE": info.get("returnOnEquity"),
            "EPS": info.get("trailingEps"),
            "Div. výnos (%)": info.get("dividendYield", 0) * 100,
            "D/E poměr": info.get("debtToEquity"),
            "Free Cash Flow": info.get("freeCashflow"),
            "Market Cap": info.get("marketCap"),
            "Skóre": calculate_score(info),
            "Fáze": classify_phase(info)
        }
    except:
        return None

def calculate_score(info):
    score = 0
    if info.get("trailingPE") and info["trailingPE"] < 15: score += 2
    if info.get("returnOnEquity") and info["returnOnEquity"] > 0.1: score += 2
    if info.get("dividendYield") and info["dividendYield"] > 0.03: score += 2
    if info.get("debtToEquity") and info["debtToEquity"] < 1: score += 2
    if info.get("freeCashflow") and info["freeCashflow"] > 0: score += 2
    return min(score, 10)

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

def add_icon(metric, value):
    if pd.isna(value): return "❔"
    if metric == "P/E": return "💰" if value < 15 else "⚠️"
    if metric == "ROE": return "📈" if value > 10 else "🔻"
    if metric == "Div. výnos (%)": return "💸" if value > 3 else "🔸"
    if metric == "D/E poměr": return "🟢" if value < 1 else "🔴"
    return ""

with st.spinner("Načítám data..."):
    tickers = get_all_tickers()
    data = [get_stock_info(t) for t in tickers]
    df = pd.DataFrame([d for d in data if d])

# Formátování
df["Cena"] = df["Cena"].map(lambda x: f"${x:.2f}")
df["ROE"] = df["ROE"] * 100
df["ROE"] = df["ROE"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
df["Div. výnos (%)"] = df["Div. výnos (%)"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
df["Free Cash Flow"] = df["Free Cash Flow"].map(lambda x: f"{x/1e6:.0f} mil." if pd.notnull(x) else "N/A")
df["Market Cap"] = df["Market Cap"].map(lambda x: f"{x/1e9:.1f} mld." if pd.notnull(x) else "N/A")

# Ikony
df["P/E"] = df["P/E"].combine(df["P/E"].map(lambda v: add_icon("P/E", v)), lambda val, icon: f"{icon} {val:.1f}" if pd.notnull(val) else "❔")
df["ROE"] = df["ROE"].combine(df["ROE"].map(lambda v: add_icon("ROE", float(v.replace('%','')))), lambda val, icon: f"{icon} {val}" if pd.notnull(val) else "❔")
df["Div. výnos (%)"] = df["Div. výnos (%)"].combine(df["Div. výnos (%)"].map(lambda v: add_icon("Div. výnos (%)", float(v.replace('%','')))), lambda val, icon: f"{icon} {val}" if pd.notnull(val) else "❔")
df["D/E poměr"] = df["D/E poměr"].combine(df["D/E poměr"].map(lambda v: add_icon("D/E poměr", v)), lambda val, icon: f"{icon} {val:.2f}" if pd.notnull(val) else "❔")

# Filtrování
st.sidebar.header("🔍 Filtrování")
sector = st.sidebar.multiselect("Sektor", sorted(df["Sektor"].dropna().unique()))
burza = st.sidebar.multiselect("Burza", sorted(df["Burza"].unique()))
faze = st.sidebar.multiselect("Fáze", sorted(df["Fáze"].unique()))
min_skore = st.sidebar.slider("Minimální skóre", 1, 10, 5)

filtered = df.copy()
if sector: filtered = filtered[filtered["Sektor"].isin(sector)]
if burza: filtered = filtered[filtered["Burza"].isin(burza)]
if faze: filtered = filtered[filtered["Fáze"].isin(faze)]
filtered = filtered[filtered["Skóre"] >= min_skore]

# Tabulka
st.subheader("📋 Seznam akcií")
selected = st.dataframe(
    filtered.set_index("Ticker")[["Název", "Cena", "P/E", "ROE", "EPS", "Div. výnos (%)", "D/E poměr", "Free Cash Flow", "Market Cap", "Skóre"]],
    use_container_width=True,
    height=500,
    on_select="select_row"
)

# Po kliknutí – vykreslit graf
clicked_ticker = st.session_state.get("select_row", {}).get("rowIndex")
if clicked_ticker is not None and clicked_ticker < len(filtered):
    ticker = filtered.iloc[clicked_ticker]["Ticker"]
    st.markdown("---")
    st.markdown(f"### 📊 Vývoj ceny pro: {ticker}")
    for label, period in {"ROK": "1y", "3 ROKY": "3y", "5 LET": "5y"}.items():
        hist = yf.Ticker(ticker).history(period=period)
        if not hist.empty:
            change = ((hist["Close"][-1] - hist["Close"][0]) / hist["Close"][0]) * 100
            trend = "🔺" if change >= 0 else "🔻"
            st.markdown(f"### {label}: {trend} {change:.2f}%")
            fig = px.line(hist, x=hist.index, y="Close", title=f"Vývoj ceny za {label}")
            st.plotly_chart(fig, use_container_width=True)

# Export
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("📥 Export do CSV", data=csv, file_name="akcie_prehlad.csv", mime="text/csv")

st.caption("Data: Yahoo Finance + Wikipedia")
