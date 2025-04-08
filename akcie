import yfinance as yf
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("📈 Podhodnocené akcie s dividendou")

# Seznam tickerů z různých sektorů
tickers = ["AAPL", "MSFT", "JNJ", "PG", "KO", "XOM", "CVX", "JPM", "V", "PFE"]

@st.cache_data(show_spinner=False)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "Ticker": ticker,
            "Sector": info.get("sector", "N/A"),
            "P/E Ratio": info.get("trailingPE"),
            "EPS": info.get("trailingEps"),
            "Revenue": info.get("totalRevenue"),
            "Dividend Yield": info.get("dividendYield", 0) * 100
        }
    except:
        return None

# Stažení a filtrování dat
with st.spinner("Načítám data ze serveru..."):
    data = [get_stock_data(t) for t in tickers]
    df = pd.DataFrame([d for d in data if d])

    # Filtrování podle pravidel
    filtered = df[
        (df["P/E Ratio"] < 20) &
        (df["EPS"] > 0) &
        (df["Revenue"] > 1_000_000_000) &
        (df["Dividend Yield"] > 0)
    ]

# Dashboard layout
cols = st.columns([1, 3])

with cols[0]:
    st.subheader("🌐 Filtrování")
    min_pe = st.slider("Maximální P/E poměr", 5, 30, 20)
    min_dividend = st.slider("Minimální dividendový výnos (%)", 0.0, 10.0, 1.0)

# Dynamické filtrování podle vstupů
custom_filtered = df[
    (df["P/E Ratio"] < min_pe) &
    (df["EPS"] > 0) &
    (df["Revenue"] > 1_000_000_000) &
    (df["Dividend Yield"] > min_dividend)
]

with cols[1]:
    st.subheader(":bar_chart: Výsledky")
    st.dataframe(custom_filtered.sort_values("P/E Ratio"))

    st.markdown("---")
    st.caption("Zdroj dat: Yahoo Finance pomocí knihovny yfinance")
