import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("📈 Podhodnocené akcie s dividendou")

# Výchozí seznam tickerů (uživatel může upravit)
def get_default_tickers():
    return ["AAPL", "MSFT", "JNJ", "PG", "KO", "XOM", "CVX", "JPM", "V", "PFE"]

user_input = st.text_input("Zadej vlastní tickery oddělené čárkou (např. AAPL,MSFT,GOOGL):", value="")
if user_input.strip():
    tickers = [t.strip().upper() for t in user_input.split(",")]
else:
    tickers = get_default_tickers()

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
            "Dividend Yield": info.get("dividendYield", 0) * 100,
            "Debt/Equity": info.get("debtToEquity"),
            "ROE": info.get("returnOnEquity"),
            "Free Cash Flow": info.get("freeCashflow"),
            "Beta": info.get("beta"),
            "Market Cap": info.get("marketCap")
        }
    except:
        return None

with st.spinner("Načítám data ze serveru..."):
    data = [get_stock_data(t) for t in tickers]
    df = pd.DataFrame([d for d in data if d])

    base_filtered = df[
        (df["P/E Ratio"] < 20) &
        (df["EPS"] > 0) &
        (df["Revenue"] > 1_000_000_000) &
        (df["Dividend Yield"] > 0)
    ]

cols = st.columns([1, 3])

with cols[0]:
    st.subheader("🌐 Filtrování")
    min_pe = st.slider("Maximální P/E poměr", 5, 30, 20)
    min_dividend = st.slider("Minimální dividendový výnos (%)", 0.0, 10.0, 1.0)
    selected_sector = st.selectbox("Filtrovat podle sektoru", options=["Vše"] + sorted(df["Sector"].dropna().unique().tolist()))

custom_filtered = df[
    (df["P/E Ratio"] < min_pe) &
    (df["EPS"] > 0) &
    (df["Revenue"] > 1_000_000_000) &
    (df["Dividend Yield"] > min_dividend)
]

if selected_sector != "Vše":
    custom_filtered = custom_filtered[custom_filtered["Sector"] == selected_sector]

with cols[1]:
    st.subheader("📋 Výsledky")
    for i, row in custom_filtered.iterrows():
        with st.expander(f"📌 {row['Ticker']} ({row['Sector']})"):
            st.write("**P/E Ratio:**", row["P/E Ratio"])
            st.write("**EPS:**", row["EPS"])
            st.write("**Revenue:**", f"{row['Revenue']:,}")
            st.write("**Dividend Yield:**", f"{row['Dividend Yield']:.2f}%")
            st.write("**Debt/Equity:**", row["Debt/Equity"])
            st.write("**ROE:**", row["ROE"])
            st.write("**Free Cash Flow:**", row["Free Cash Flow"])
            st.write("**Beta:**", row["Beta"])
            st.write("**Market Cap:**", f"{row['Market Cap']:,}")

            stock = yf.Ticker(row['Ticker'])
            hist = stock.history(period="20y")

            fig = go.Figure(data=[go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close']
            )])
            fig.update_layout(title=f"Vývoj ceny akcie: {row['Ticker']}", xaxis_title="Datum", yaxis_title="Cena", height=500)
            st.plotly_chart(fig)

            st.subheader("📈 Vývoj ceny v %")

            def calc_return(period_days):
                try:
                    past_price = hist.iloc[-period_days]["Close"]
                    current_price = hist.iloc[-1]["Close"]
                    return round(((current_price - past_price) / past_price) * 100, 2)
                except:
                    return "N/A"

            returns = {
                "YTD": calc_return((datetime.now() - datetime(datetime.now().year, 1, 1)).days),
                "3 měsíce": calc_return(63),
                "6 měsíců": calc_return(126),
                "1 rok": calc_return(252),
                "3 roky": calc_return(756),
                "5 let": calc_return(1260),
                "10 let": calc_return(2520),
                "20 let": calc_return(5040),
            }

            st.table(pd.DataFrame.from_dict(returns, orient='index', columns=['Změna (%)']))

    csv = custom_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Stáhnout výsledky jako CSV",
        data=csv,
        file_name='akcie_filtr.csv',
        mime='text/csv',
    )

    st.markdown("---")
    st.caption("Zdroj dat: Yahoo Finance pomocí knihovny yfinance")
