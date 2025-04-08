import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
import os

st.set_page_config(layout="wide")
st.title("📈 Investiční akcie – růst, zisk a hodnota")

HISTORY_FILE = "skore_history.csv"

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
        hist_div = stock.dividends
        last_div = hist_div[-1] if not hist_div.empty else 0
        payout_ratio = info.get("payoutRatio")
        return {
            "Ticker": ticker,
            "Název": info.get("longName"),
            "Burza": ticker.split(".")[-1] if "." in ticker else "USA",
            "Měna": info.get("currency", "USD"),
            "Sektor": info.get("sector"),
            "Cena": price,
            "P/E": info.get("trailingPE"),
            "ROE": info.get("returnOnEquity"),
            "EPS": info.get("trailingEps"),
            "Dividenda": last_div,
            "Payout Ratio": payout_ratio,
            "D/E poměr": info.get("debtToEquity"),
            "Free Cash Flow": info.get("freeCashflow"),
            "Market Cap": info.get("marketCap"),
            "Beta": info.get("beta"),
            "Fáze": classify_phase(info),
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
        score += 3
    if info.get("payoutRatio") and 0.2 < info["payoutRatio"] < 0.6:
        score += 2
    if info.get("trailingEps", 0) > 1 and info.get("dividendYield", 0) > 0:
        score += 2
    if info.get("freeCashflow") and info["freeCashflow"] > 0:
        score += 2
    beta = info.get("beta")
    if beta and 0.7 <= beta <= 1.3:
        score += 1
    return min(score, 10)

def log_score_history(df):
    today = datetime.today().strftime("%Y-%m-%d")
    log_df = df[["Ticker", "Skóre"]].copy()
    log_df["Datum"] = today
    if os.path.exists("skore_history.csv"):
        old = pd.read_csv("skore_history.csv")
        combined = pd.concat([old, log_df], ignore_index=True)
        combined.drop_duplicates(subset=["Ticker", "Datum"], inplace=True)
    else:
        combined = log_df
    combined.to_csv("skore_history.csv", index=False)

with st.spinner("Načítám data..."):
    tickers = get_all_tickers()
    data = [get_stock_info(t) for t in tickers]
    df = pd.DataFrame([d for d in data if d])
    log_score_history(df)

currency = df["Měna"].mode().values[0] if "Měna" in df.columns else "USD"
df["Cena"] = df["Cena"].map(lambda x: f"{currency} {x:.2f}")
df["ROE"] = df["ROE"] * 100
df["ROE"] = df["ROE"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
df["Dividenda"] = df["Dividenda"].map(lambda x: f"{currency} {x:.2f}" if pd.notnull(x) else "N/A")
df["Free Cash Flow"] = df["Free Cash Flow"].map(lambda x: f"{x/1e6:.0f} mil." if pd.notnull(x) else "N/A")
df["Market Cap"] = df["Market Cap"].map(lambda x: f"{x/1e9:.1f} mld." if pd.notnull(x) else "N/A")
df["Payout Ratio"] = df["Payout Ratio"].map(lambda x: f"{x:.0%}" if pd.notnull(x) else "N/A")

# Filtrování
st.sidebar.header("🔍 Filtrování")
sector = st.sidebar.multiselect("Sektor", sorted(df["Sektor"].dropna().unique()))
burza = st.sidebar.multiselect("Burza", sorted(df["Burza"].unique()))
faze = st.sidebar.multiselect("Fáze", sorted(df["Fáze"].unique()))
min_skore = st.sidebar.slider("Minimální skóre", 1, 10, 6)

filtered = df.copy()
if sector: filtered = filtered[filtered["Sektor"].isin(sector)]
if burza: filtered = filtered[filtered["Burza"].isin(burza)]
if faze: filtered = filtered[filtered["Fáze"].isin(faze)]
filtered = filtered[filtered["Skóre"] >= min_skore]

# 🏆 TOP akcie týdne
st.subheader("🏆 TOP akcie týdne (Skóre 9–10)")
top_stocks = df[df["Skóre"] >= 9].sort_values("Skóre", ascending=False)
if not top_stocks.empty:
    st.dataframe(top_stocks[["Ticker", "Název", "Skóre", "P/E", "Dividenda", "Fáze"]], use_container_width=True)
else:
    st.info("Tento týden nejsou žádné akcie se skóre 9–10.")

# 📊 Bublinový graf
st.subheader("📊 Vizualizace podle sektorů")
bubble_data = df.copy()
bubble_data["Market Cap (mld.)"] = pd.to_numeric(df["Market Cap"].str.replace(" mld.", "", regex=False), errors="coerce")
fig = px.scatter(
    bubble_data,
    x="P/E",
    y="ROE",
    size="Market Cap (mld.)",
    color="Sektor",
    hover_name="Název",
    custom_data=["Ticker"],
    title="Bublinový graf: P/E vs ROE podle sektorů",
    size_max=60,
    height=600
)
fig.update_traces(mode="markers", marker=dict(opacity=0.6), hovertemplate="Ticker: %{customdata[0]}<br>P/E: %{x}<br>ROE: %{y}%")
st.plotly_chart(fig, use_container_width=True)

# 📋 Tabulka a výběr
st.subheader("📋 Výběr akcií")
selected = st.dataframe(
    filtered.set_index("Ticker")[[
        "Název", "Cena", "P/E", "ROE", "EPS", "Dividenda", "Payout Ratio", "D/E poměr", "Free Cash Flow", "Market Cap", "Skóre"
    ]],
    use_container_width=True,
    height=500,
    on_select="select_row"
)

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

# 📈 Vývoj skóre v čase
if os.path.exists("skore_history.csv"):
    st.subheader("📈 Vývoj skóre – historie")
    history_df = pd.read_csv("skore_history.csv")
    tickers_in_table = filtered["Ticker"].tolist()
    chart_df = history_df[history_df["Ticker"].isin(tickers_in_table)]
    if not chart_df.empty:
        fig = px.line(chart_df, x="Datum", y="Skóre", color="Ticker", title="Vývoj skóre v čase")
        st.plotly_chart(fig, use_container_width=True)

# 📥 Export
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("📥 Export do CSV", data=csv, file_name="akcie_filtr.csv", mime="text/csv")

st.caption("Data: Yahoo Finance + Wikipedia")
