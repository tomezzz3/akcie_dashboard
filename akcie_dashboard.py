# STABILNÍ DASHBOARD (barevné skóre + top 5 + PDF a email)
import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
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
    nasdaq = pd.read_html("https://en.wikipedia.org/wiki/NASDAQ-100")[3]["Ticker"].tolist()
nyse = ["JNJ", "PG", "KO", "DIS", "BA", "CAT", "MMM"]  # ukázka (reálný seznam vyžaduje externí zdroj)
tokyo = ["7203.T", "6758.T", "9984.T"]  # Toyota, Sony, SoftBank (pro Yahoo Finance)
xetra = ["SAP.DE", "DTE.DE", "BAS.DE", "ALV.DE"]  # ukázkové německé akcie z XETRA
bse = ["RELIANCE.BO", "TCS.BO", "INFY.BO"]  # Bombay Stock Exchange
tsx = ["RY.TO", "TD.TO", "BNS.TO"]  # Toronto Stock Exchange
asx = ["CBA.AX", "BHP.AX", "WES.AX"]  # Australian Stock Exchange
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
    if info.get("trailingPE") and info["trailingPE"] < 15: score += 3
    if payout_ratio > 0:
        if phase == "📈 Růstová" and 0.1 < payout_ratio < 0.4: score += 2
        elif phase == "🏦 Stabilní" and 0.3 < payout_ratio < 0.7: score += 2
        elif phase == "💎 Hodnotová" and 0.5 < payout_ratio < 0.8: score += 2
    if eps > 1 and info.get("dividendYield", 0) > 0: score += 2
    if info.get("freeCashflow") and info["freeCashflow"] > 0: score += 2
    beta = info.get("beta")
    if beta and 0.7 <= beta <= 1.3: score += 1
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

def generate_price_chart(ticker, period="1y", output_path="chart.png"):
    hist = yf.Ticker(ticker).history(period=period)
    if not hist.empty:
        plt.figure(figsize=(10, 4))
        plt.plot(hist.index, hist["Close"], label="Cena")
        plt.title(f"Vývoj ceny za {period} – {ticker}")
        plt.xlabel("Datum")
        plt.ylabel("Cena")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_path)
        return output_path
    return None

def generate_pdf(ticker, selected, chart_path):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("template.html")
    html = template.render(
        ticker=ticker,
        name=selected["Název"],
        sector=selected["Sektor"],
        phase=selected["Fáze"],
        metrics=selected,
        chart_path=chart_path,
        date=datetime.today().strftime("%d.%m.%Y %H:%M")
    )
    pdfkit.from_string(html, "report.pdf")

def send_email_with_attachment(receiver_email):
    msg = EmailMessage()
    msg["Subject"] = "Tvůj PDF report – akcie"
    msg["From"] = "noreply@example.com"
    msg["To"] = receiver_email
    msg.set_content("V příloze nalezneš PDF report tvé vybrané akcie.")
    with open("report.pdf", "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="report.pdf")
    with smtplib.SMTP("smtp.example.com", 587) as server:
        server.starttls()
        server.login("your_email@example.com", "your_password")
        server.send_message(msg)

# === ZAČÁTEK HLAVNÍHO KÓDU ===

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

st.subheader("⭐ TOP 50 akcií podle skóre")
top5 = filtered.sort_values("Skóre", ascending=False).head(50)
st.dataframe(top5.set_index("Ticker"), use_container_width=True)

st.subheader("📋 Výběr akcie")
ticker = st.selectbox("Vyber akcii", options=filtered["Ticker"].unique())
selected = filtered[filtered["Ticker"] == ticker].iloc[0]

styled_df = filtered.copy()
styled_df["Skóre"] = styled_df["Skóre"].astype(int)

# Převod formátovaných sloupců zpět na čísla pro barevný gradient
for col in ["P/E", "ROE", "EPS", "Dividenda"]:
    styled_df[col] = pd.to_numeric(df[col], errors="coerce")

st.dataframe(
    styled_df.style.background_gradient(subset=["Skóre", "P/E", "ROE", "EPS", "Dividenda"], cmap="RdYlGn", axis=0)
    .format(precision=2),
    use_container_width=True
)

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

if os.path.exists(HISTORY_FILE):
    st.subheader("📈 Vývoj skóre – historie")
    history_df = pd.read_csv(HISTORY_FILE)
    chart_df = history_df[history_df["Ticker"] == ticker]
    if not chart_df.empty:
        fig = px.line(chart_df, x="Datum", y="Skóre", title=f"Skóre v čase – {ticker}")
        st.plotly_chart(fig, use_container_width=True)

# 📄 Export PDF a odeslání e-mailem
st.markdown("---")
if st.button("📄 Exportovat PDF report"):
    chart_path = generate_price_chart(ticker)
    generate_pdf(ticker, selected, chart_path)
    with open("report.pdf", "rb") as f:
        st.download_button("📥 Stáhnout PDF", data=f, file_name=f"{ticker}_report.pdf", mime="application/pdf")

email = st.text_input("📧 Zadat e-mail pro odeslání PDF:")
if st.button("✉️ Odeslat e-mailem"):
    if email:
        try:
            send_email_with_attachment(email)
            st.success(f"PDF report odeslán na {email}")
        except Exception as e:
            st.error(f"Chyba při odesílání: {e}")
    else:
        st.warning("Zadej prosím e-mailovou adresu.")

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("📥 Export do CSV", data=csv, file_name="akcie_filtr.csv", mime="text/csv")

st.caption("Data: Yahoo Finance + Wikipedia")

