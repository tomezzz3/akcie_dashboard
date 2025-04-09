# STABILNÍ DASHBOARD (barevné skóre + top 5 + PDF a email)

import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt
import pdfkit
from jinja2 import Environment, FileSystemLoader
import smtplib
from email.message import EmailMessage

st.set_page_config(layout="wide")
st.title("📈 Investiční akcie – růst, zisk a hodnota")

HISTORY_FILE = "skore_history.csv"

@st.cache_data(show_spinner=False)
def get_all_tickers():
    sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]["Symbol"].tolist()
    dax_table = pd.read_html("https://en.wikipedia.org/wiki/DAX")[1]
    dax_symbols = dax_table[dax_table.columns[0]].tolist()
    ceske = ["CEZ.PR", "KOMB.PR", "MONET.PR"]
    polske = ["PKN.OL", "PKOBP.OL", "PEKAO.OL"]
    lse = ["HSBA.L", "TSCO.L", "BP.L"]
    nasdaq_tables = pd.read_html("https://en.wikipedia.org/wiki/NASDAQ-100")
    for table in nasdaq_tables:
        if any(isinstance(col, str) and col.lower() in ["ticker", "symbol"] for col in table.columns):
            nasdaq = table[table.columns[0]].tolist()
            break
    else:
        nasdaq = []
    nyse = ["JNJ", "PG", "KO", "DIS", "BA", "CAT", "MMM"]
    tokyo = ["7203.T", "6758.T", "9984.T"]
    xetra = ["SAP.DE", "DTE.DE", "BAS.DE", "ALV.DE"]
    bse = ["RELIANCE.BO", "TCS.BO", "INFY.BO"]
    tsx = ["RY.TO", "TD.TO", "BNS.TO"]
    asx = ["CBA.AX", "BHP.AX", "WES.AX"]
    return sp500 + dax_symbols + ceske + polske + lse + nasdaq + nyse + tokyo + xetra + bse + tsx + asx

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
    payout_ratio = info.get("payoutRatio") or 0
    eps = info.get("trailingEps", 0)
    phase = classify_phase(info)
    if info.get("trailingPE") and info["trailingPE"] < 15:
        score += 3
    if payout_ratio > 0:
        if phase == "📈 Růstová" and 0.1 < payout_ratio < 0.4:
            score += 2
        elif phase == "🏦 Stabilní" and 0.3 < payout_ratio < 0.7:
            score += 2
        elif phase == "💎 Hodnotová" and 0.5 < payout_ratio < 0.8:
            score += 2
    if eps > 1 and info.get("dividendYield", 0) > 0:
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
    if os.path.exists(HISTORY_FILE):
        old = pd.read_csv(HISTORY_FILE)
        combined = pd.concat([old, log_df], ignore_index=True)
        combined.drop_duplicates(subset=["Ticker", "Datum"], inplace=True)
    else:
        combined = log_df
    combined.to_csv(HISTORY_FILE, index=False)
    # záloha
    backup_filename = f"backup_skore_{today}.csv"
    combined.to_csv(backup_filename, index=False)

def generate_historical_scores(start="2020-01"):
    start_date = pd.to_datetime(start)
    today = pd.to_datetime(datetime.today().date())
    months = pd.date_range(start=start_date, end=today, freq="M")
    history_records = []

    for date in months:
        tickers = get_all_tickers()
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                eps = info.get("trailingEps", 0)
                roe = info.get("returnOnEquity", 0)
                mc = info.get("marketCap", 0)
                pe = info.get("trailingPE")
                payout_ratio = info.get("payoutRatio") or 0
                fcf = info.get("freeCashflow")
                beta = info.get("beta")
                dividend_yield = info.get("dividendYield", 0)

                # klasifikace fáze firmy
                if eps > 2 and roe > 0.15:
                    phase = "📈 Růstová"
                elif mc and mc > 5e10:
                    phase = "🏦 Stabilní"
                else:
                    phase = "💎 Hodnotová"

                score = 0
                if pe and pe < 15: score += 3
                if payout_ratio > 0:
                    if phase == "📈 Růstová" and 0.1 < payout_ratio < 0.4: score += 2
                    elif phase == "🏦 Stabilní" and 0.3 < payout_ratio < 0.7: score += 2
                    elif phase == "💎 Hodnotová" and 0.5 < payout_ratio < 0.8: score += 2
                if eps > 1 and dividend_yield > 0: score += 2
                if fcf and fcf > 0: score += 2
                if beta and 0.7 <= beta <= 1.3: score += 1

                score = min(score, 10)
                ultimo_date = date + pd.offsets.MonthEnd(0)
                history_records.append({"Ticker": ticker, "Skóre": score, "Datum": ultimo_date.strftime("%Y-%m-%d")})

            except Exception:
                continue

    hist_df = pd.DataFrame(history_records)
    hist_df.to_csv("skore_history.csv", index=False)
    return hist_df

# === Hlavní stránka a logika dashboardu ===

page = st.sidebar.radio("📄 Stránka", ["📋 Dashboard", "⭐ Top výběr", "🧮 Kalkulačka investic"])

with st.spinner("Načítám data..."):
    if not os.path.exists(HISTORY_FILE):
        with st.spinner("Generuji historické skóre..."):
            generate_historical_scores()
    tickers = get_all_tickers()
    data = [get_stock_info(t) for t in tickers]
    log_score_history(pd.DataFrame([d for d in data if d]))
    df = pd.DataFrame([d for d in data if d])

currency = df["Měna"].mode().values[0] if "Měna" in df.columns else "USD"
df["Cena"] = df["Cena"].map(lambda x: f"{currency} {x:.2f}")
df["ROE"] = df["ROE"] * 100
df["ROE"] = df["ROE"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
df["Dividenda"] = df["Dividenda"].map(lambda x: f"{currency} {x:.2f}" if pd.notnull(x) else "N/A")
df["Free Cash Flow"] = df["Free Cash Flow"].map(lambda x: f"{x/1e6:.0f} mil." if pd.notnull(x) else "N/A")
df["Market Cap"] = df["Market Cap"].map(lambda x: f"{x/1e9:.1f} mld." if pd.notnull(x) else "N/A")
df["Payout Ratio"] = df["Payout Ratio"].map(lambda x: f"{x:.0%}" if pd.notnull(x) else "N/A")

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

if page == "⭐ Top výběr":
    st.subheader("⭐ TOP 50 akcií podle skóre")
    top50 = filtered.sort_values("Skóre", ascending=False).head(50)
    st.dataframe(top50.set_index("Ticker"), use_container_width=True)

elif page == "📋 Dashboard":
    st.subheader("📋 Výběr akcie")
    ticker = st.selectbox("Vyber akcii", options=filtered["Ticker"].unique())
    selected = filtered[filtered["Ticker"] == ticker].iloc[0]

    styled_df = filtered.copy()
    styled_df["Skóre"] = styled_df["Skóre"].astype(int)
    styled_df["ROE"] = df["ROE"]
    styled_df["Dividenda"] = df["Dividenda"]

    st.dataframe(styled_df.style.format(precision=2), use_container_width=True)

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

elif page == "🧮 Kalkulačka investic":
    st.title("💰 Investiční kalkulačka – simulace pravidelného nákupu akcií")
    invest_per_month = st.number_input("Měsíční investice (USD)", min_value=10, value=1000, step=10)
    start_date = st.date_input("Začátek investování", value=datetime(2020, 1, 1))
    top_n = st.selectbox("Počet TOP akcií (podle skóre 10–8)", [10, 30, 50])

    @st.cache_data
    def load_history():
        df = pd.read_csv("skore_history.csv")
        df["Datum"] = pd.to_datetime(df["Datum"])
        prices = {}
        tickers = df[df['Skóre'] >= 8]['Ticker'].unique()
        for ticker in tickers:
            hist = yf.Ticker(ticker).history(period="max")["Close"]
            prices[ticker] = hist
        return df, prices

    df_hist, prices = load_history()

    @st.cache_data
    def get_dividends(tickers):
        divs = {}
        for t in tickers:
            try:
                dividends = yf.Ticker(t).dividends
                divs[t] = dividends
            except:
                divs[t] = pd.Series()
        return divs

    dividends_data = get_dividends(df_hist['Ticker'].unique())

    portfolio = []
    reinvested_cash = 0
    cumulative_dividends = 0
    monthly_portfolio = []
    current_date = pd.to_datetime(start_date)

    while current_date < datetime.today():
        current_portfolio = []
        month_df = df_hist[df_hist["Datum"].dt.to_period("M") == current_date.to_period("M")]
        top_df = month_df[month_df["Skóre"] >= 8].sort_values("Skóre", ascending=False).head(top_n)
        tickers = top_df["Ticker"].tolist()
        total_investment = invest_per_month + reinvested_cash
        amount_per_stock = total_investment / len(tickers) if tickers else 0

        for ticker in tickers:
            if ticker in prices and current_date in prices[ticker].index:
                price = prices[ticker].loc[current_date]
                shares = amount_per_stock / price if price > 0 else 0
                current_portfolio.append({
                    "Datum": current_date,
                    "Ticker": ticker,
                    "Cena": price,
                    "Kusy": shares,
                    "Investováno": amount_per_stock
                })

        portfolio.extend(current_portfolio)

        hodnota = sum(
            row["Kusy"] * prices[row["Ticker"]].loc[current_date]
            for row in current_portfolio
            if row["Ticker"] in prices and current_date in prices[row["Ticker"]].index
        )

        month_dividends = 0
        for row in current_portfolio:
            ticker = row["Ticker"]
            shares = row["Kusy"]
            if ticker in dividends_data:
                div_series = dividends_data[ticker]
                if current_date in div_series.index:
                    dividend = div_series.loc[current_date] * shares
                    month_dividends += dividend

        cumulative_dividends += month_dividends
        reinvested_cash = month_dividends
        monthly_portfolio.append({"Datum": current_date, "Hodnota": hodnota, "Dividendy": cumulative_dividends})

        current_date += timedelta(days=32)
        current_date = current_date.replace(day=1)

    portfolio_df = pd.DataFrame(portfolio)

    if not portfolio_df.empty:
        summary = portfolio_df.groupby("Ticker").agg({
            "Kusy": "sum",
            "Investováno": "sum"
        }).reset_index()

        summary["Aktuální cena"] = summary["Ticker"].apply(lambda x: prices[x].iloc[-1] if x in prices else 0)
        summary["Hodnota"] = summary["Kusy"] * summary["Aktuální cena"]
        summary["Zhodnocení"] = (summary["Hodnota"] - summary["Investováno"]) / summary["Investováno"] * 100

        st.subheader("📊 Výsledky simulace")
        st.dataframe(summary.set_index("Ticker"))
        st.metric("💵 Celková investice", f"{summary['Investováno'].sum():,.0f} USD")
        st.metric("📈 Aktuální hodnota", f"{summary['Hodnota'].sum():,.0f} USD")
        st.metric("📊 Celkové zhodnocení", f"{summary['Zhodnocení'].mean():.2f} %")

        st.subheader("📈 Vývoj hodnoty portfolia v čase")
        timeline = pd.DataFrame(monthly_portfolio)
        st.line_chart(timeline.set_index("Datum")[["Hodnota"]])

        st.subheader("📤 Kumulované dividendy")
        st.line_chart(timeline.set_index("Datum")[["Dividendy"]])
    else:
        st.warning("Žádná investice nebyla provedena v daném období.")

