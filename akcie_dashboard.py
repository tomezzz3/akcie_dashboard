import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

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
            "Free Cash Flow": info.get("freeCashflow")
        }
    except:
        return None

with st.spinner("Načítám data ze serveru..."):
    data = [get_stock_data(t) for t in tickers]
    df = pd.DataFrame([d for d in data if d])

    # Filtrování podle základních pravidel
    base_filtered = df[
        (df["P/E Ratio"] < 20) &
        (df["EPS"] > 0) &
        (df["Revenue"] > 1_000_000_000) &
        (df["Dividend Yield"] > 0)
    ]

# Layout
cols = st.columns([1, 3])

with cols[0]:
    st.subheader("🌐 Filtrování")
    min_pe = st.slider("Maximální P/E poměr", 5, 30, 20)
    min_dividend = st.slider("Minimální dividendový výnos (%)", 0.0, 10.0, 1.0)
    selected_sector = st.selectbox("Filtrovat podle sektoru", options=["Vše"] + sorted(df["Sector"].dropna().unique().tolist()))

# Dynamické filtrování
custom_filtered = df[
    (df["P/E Ratio"] < min_pe) &
    (df["EPS"] > 0) &
    (df["Revenue"] > 1_000_000_000) &
    (df["Dividend Yield"] > min_dividend)
]

if selected_sector != "Vše":
    custom_filtered = custom_filtered[custom_filtered["Sector"] == selected_sector]

with cols[1]:
    st.subheader(":bar_chart: Výsledky")
    st.dataframe(custom_filtered.sort_values("P/E Ratio"))

    # Export
    csv = custom_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Stáhnout výsledky jako CSV",
        data=csv,
        file_name='akcie_filtr.csv',
        mime='text/csv',
    )

    # Výběr a zobrazení grafu
    st.subheader("📊 Graf vývoje ceny akcie")
    if not custom_filtered.empty:
        selected_ticker = st.selectbox("Vyber akcii pro graf", options=custom_filtered["Ticker"])
        if selected_ticker:
            hist = yf.Ticker(selected_ticker).history(period="6mo")
            fig = go.Figure(data=[go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close']
            )])
            fig.update_layout(title=f"Vývoj ceny akcie: {selected_ticker}", xaxis_title="Datum", yaxis_title="Cena", height=500)
            st.plotly_chart(fig)

    st.markdown("---")
    st.caption("Zdroj dat: Yahoo Finance pomocí knihovny yfinance")
