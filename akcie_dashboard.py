import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Akciový Dashboard", layout="wide")

st.title("📊 Přehled akcií")
st.markdown("Interaktivní nástroj pro analýzu akcií podle sektorů, burz a růstových fází.")

# -------------------------------
# Simulovaná data
# -------------------------------
def generate_fake_stock_data():
    np.random.seed(42)
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA']
    names = ['Apple', 'Microsoft', 'Alphabet', 'Tesla', 'Amazon', 'NVIDIA']
    sectors = ['Technology', 'Technology', 'Technology', 'Automotive', 'Retail', 'Technology']
    exchanges = ['NASDAQ', 'NASDAQ', 'NASDAQ', 'NASDAQ', 'NASDAQ', 'NASDAQ']
    growth_phases = ['Růst', 'Zralost', 'Růst', 'Expanze', 'Zralost', 'Růst']

    data = []
    for i in range(len(tickers)):
        data.append({
            "Ticker": tickers[i],
            "Společnost": names[i],
            "Sektor": sectors[i],
            "Burza": exchanges[i],
            "Fáze růstu": growth_phases[i],
            "Roční výnos (%)": round(np.random.uniform(-20, 60), 2),
            "Beta": round(np.random.uniform(0.8, 1.6), 2)
        })

    return pd.DataFrame(data)

stocks_df = generate_fake_stock_data()

# -------------------------------
# Boční panel - filtry
# -------------------------------
st.sidebar.header("🔎 Filtr")
selected_sector = st.sidebar.multiselect("Sektor", options=stocks_df["Sektor"].unique(), default=stocks_df["Sektor"].unique())
selected_exchange = st.sidebar.multiselect("Burza", options=stocks_df["Burza"].unique(), default=stocks_df["Burza"].unique())

filtered_df = stocks_df[
    (stocks_df["Sektor"].isin(selected_sector)) &
    (stocks_df["Burza"].isin(selected_exchange))
]

# -------------------------------
# Zobrazení tabulky
# -------------------------------
st.subheader("📋 Přehled akcií")
if filtered_df.empty:
    st.warning("Žádné akcie neodpovídají vybraným filtrům.")
else:
    # Formátování sloupců
    display_df = filtered_df.copy()
    display_df["Roční výnos (%)"] = display_df["Roční výnos (%)"].astype(str) + " %"
    st.dataframe(display_df, use_container_width=True)

# -------------------------------
# Detail akcie po výběru
# -------------------------------
st.markdown("---")
st.subheader("📈 Detailní vývoj ceny akcie")

selected_ticker = st.selectbox("Vyber akcii:", options=filtered_df["Ticker"].tolist())

def get_stock_price_data(ticker):
    dates = pd.date_range(end=datetime.today(), periods=365)
    prices = np.cumsum(np.random.randn(365)) + 100  # fake price data
    return pd.DataFrame({"Datum": dates, "Cena": prices})

if selected_ticker:
    chart_df = get_stock_price_data(selected_ticker)
    fig = px.line(chart_df, x="Datum", y="Cena", title=f"Vývoj ceny akcie {selected_ticker}", labels={"Cena": "Cena ($)"})
    st.plotly_chart(fig, use_container_width=True)

