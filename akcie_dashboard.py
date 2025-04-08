import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from streamlit.components.v1 import html

st.set_page_config(layout="wide")
st.title("📈 Podhodnocené akcie s dividendou")

@st.cache_data(show_spinner=False)
def get_all_tickers():
    sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    sp500_table = pd.read_html(sp500_url)
    sp500 = sp500_table[0]["Symbol"].tolist()

    ceske = ["CEZ.PR", "KOMB.PR", "MONET.PR", "ERB.PR", "GENEZA.PR"]
    londynske = ["HSBA.L", "TSCO.L", "BP.L", "BARC.L", "LLOY.L", "VOD.L"]

    return list(set(ceske + londynske + sp500[:50]))  # zrychlené načítání

@st.cache_data(show_spinner=False)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "Ticker": ticker,
            "Name": info.get("longName", "N/A"),
            "Description": info.get("longBusinessSummary", "Není dostupné."),
            "Sector": info.get("sector", "N/A"),
            "P/E Ratio": info.get("trailingPE"),
            "EPS": info.get("trailingEps"),
            "Revenue": info.get("totalRevenue"),
            "Dividend Yield": info.get("dividendYield", 0) * 100,
            "Debt/Equity": info.get("debtToEquity"),
            "ROE": info.get("returnOnEquity"),
            "Free Cash Flow": info.get("freeCashflow"),
            "Beta": info.get("beta"),
            "Market Cap": info.get("marketCap"),
            "Alpha": info.get("alpha", None)
        }
    except:
        return None

@st.cache_data(show_spinner=False)
def calculate_sector_pe_averages(df):
    return df.groupby("Sector")["P/E Ratio"].mean().to_dict()

@st.cache_data(show_spinner=False)
def calculate_score(row, sector_pe_avg):
    weights = {
        "P/E": 0.2,
        "Dividend": 0.2,
        "EPS": 0.1,
        "ROE": 0.15,
        "Debt/Equity": 0.15,
        "Free Cash Flow": 0.1,
        "Beta": 0.05,
        "Alpha": 0.05
    }
    score = 0
    sector_avg = sector_pe_avg.get(row["Sector"], None)

    if row["P/E Ratio"] and sector_avg and row["P/E Ratio"] < sector_avg:
        score += weights["P/E"]
    if row["Dividend Yield"] and row["Dividend Yield"] > 2:
        score += weights["Dividend"]
    if row["EPS"] and row["EPS"] > 0:
        score += weights["EPS"]
    if row["ROE"] and row["ROE"] > 0.1:
        score += weights["ROE"]
    if row["Debt/Equity"] and row["Debt/Equity"] < 1:
        score += weights["Debt/Equity"]
    if row["Free Cash Flow"] and row["Free Cash Flow"] > 0:
        score += weights["Free Cash Flow"]
    if row["Beta"] and 0.5 <= row["Beta"] <= 1.5:
        score += weights["Beta"]
    if row["Alpha"] and row["Alpha"] > 0:
        score += weights["Alpha"]
    return round(score, 2)

def get_color(value, param):
    if param == "P/E Ratio":
        if value < 10: return "darkgreen"
        elif value < 15: return "green"
        elif value < 20: return "yellow"
        else: return "red"
    elif param == "Dividend Yield":
        if value > 5: return "darkgreen"
        elif value > 3: return "green"
        elif value > 1: return "yellow"
        else: return "red"
    elif param == "ROE":
        if value > 0.2: return "darkgreen"
        elif value > 0.1: return "green"
        elif value > 0.05: return "yellow"
        else: return "red"
    elif param == "Debt/Equity":
        if value < 0.3: return "darkgreen"
        elif value < 0.7: return "green"
        elif value < 1.5: return "yellow"
        else: return "red"
    else:
        return "lightgray"

with st.spinner("Načítám data o akciích..."):
    tickers = get_all_tickers()
    data = [get_stock_data(t) for t in tickers]
    df = pd.DataFrame([d for d in data if d])

    sector_pe_avg = calculate_sector_pe_averages(df)
    df["Skóre"] = df.apply(lambda row: calculate_score(row, sector_pe_avg), axis=1)
    df_sorted = df.sort_values("Skóre", ascending=False)

st.sidebar.header("🔎 Filtrování")
min_score = st.sidebar.slider("Minimální skóre", 0.0, 1.0, 0.3, 0.05)
selected_sector = st.sidebar.selectbox("Sektor", options=["Vše"] + sorted(df["Sector"].dropna().unique().tolist()))

filtered_df = df_sorted[df_sorted["Skóre"] >= min_score]
if selected_sector != "Vše":
    filtered_df = filtered_df[filtered_df["Sector"] == selected_sector]

st.subheader("📋 Výsledky podle investičního skóre")

for _, row in filtered_df.iterrows():
    st.markdown(f"### {row['Name']} ({row['Ticker']})")
    st.caption(row['Description'])

    cols = st.columns(6)
    metrics = ["P/E Ratio", "Dividend Yield", "ROE", "Debt/Equity", "Free Cash Flow", "Skóre"]
    for i, metric in enumerate(metrics):
        val = row.get(metric, "N/A")
        color = get_color(val, metric) if metric in ["P/E Ratio", "Dividend Yield", "ROE", "Debt/Equity"] else "lightgray"
        with cols[i]:
            st.markdown(f"<div style='background-color:{color};padding:10px;border-radius:10px;text-align:center'>"
                        f"<b>{metric}</b><br>{round(val, 2) if isinstance(val, (int, float)) else val}</div>", unsafe_allow_html=True)

selected_ticker = st.selectbox("📈 Zobrazit graf pro akcii:", options=filtered_df["Ticker"].tolist())
period_option = st.selectbox("Období pro vývoj ceny:", ["1 měsíc", "3 měsíce", "6 měsíců", "1 rok", "3 roky", "5 let", "10 let", "20 let"])
period_map = {"1 měsíc": "1mo", "3 měsíce": "3mo", "6 měsíců": "6mo", "1 rok": "1y", "3 roky": "3y", "5 let": "5y", "10 let": "10y", "20 let": "20y"}

if selected_ticker:
    st.subheader(f"📊 Vývoj ceny: {selected_ticker} - {period_option}")
    hist = yf.Ticker(selected_ticker).history(period=period_map[period_option])
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
    fig.update_layout(title=f"Vývoj ceny akcie: {selected_ticker}", xaxis_title="Datum", yaxis_title="Cena", height=500)
    st.plotly_chart(fig)

    try:
        start_price = hist.iloc[0]['Close']
        end_price = hist.iloc[-1]['Close']
        price_change = ((end_price - start_price) / start_price) * 100
        st.metric(label="Změna ceny v %", value=f"{price_change:.2f}%")
    except:
        st.warning("Nepodařilo se vypočítat změnu ceny.")

csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Stáhnout výsledky jako CSV",
    data=csv,
    file_name='akcie_filtr_score.csv',
    mime='text/csv'
)

st.caption("Zdroj dat: Yahoo Finance + Wikipedia (S&P 500) + PSE + LSE")
