# STABILNÍ DASHBOARD (barevné skóre + top 5 + PDF a email)

import yfinance as yf import pandas as pd import streamlit as st import plotly.express as px from datetime import datetime import os import matplotlib.pyplot as plt import pdfkit from jinja2 import Environment, FileSystemLoader import smtplib from email.message import EmailMessage

st.set\_page\_config(layout="wide") st.title("📈 Investiční akcie – růst, zisk a hodnota")

HISTORY\_FILE = "skore\_history.csv"

@st.cache\_data(show\_spinner=False) def get\_all\_tickers(): sp500 = pd.read\_html("[[https://en.wikipedia.org/wiki/List\_of\_S%26P\_500\_companies](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies)")[0](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"\)\[0)]["Symbol"].tolist() dax\_table = pd.read\_html("[[https://en.wikipedia.org/wiki/DAX](https://en.wikipedia.org/wiki/DAX)")[1](https://en.wikipedia.org/wiki/DAX"\)\[1)] dax\_symbols = dax\_table[dax\_table.columns[0]].tolist() ceske = ["CEZ.PR", "KOMB.PR", "MONET.PR"] polske = ["PKN.OL", "PKOBP.OL", "PEKAO.OL"] lse = ["HSBA.L", "TSCO.L", "BP.L"] nasdaq\_tables = pd.read\_html("[https://en.wikipedia.org/wiki/NASDAQ-100](https://en.wikipedia.org/wiki/NASDAQ-100)") for table in nasdaq\_tables: if any(isinstance(col, str) and col.lower() in ["ticker", "symbol"] for col in table.columns): nasdaq = table[table.columns[0]].tolist() break else: nasdaq = [] nyse = ["JNJ", "PG", "KO", "DIS", "BA", "CAT", "MMM"]  # ukázka tokyo = ["7203.T", "6758.T", "9984.T"] xetra = ["SAP.DE", "DTE.DE", "BAS.DE", "ALV.DE"] bse = ["RELIANCE.BO", "TCS.BO", "INFY.BO"] tsx = ["RY.TO", "TD.TO", "BNS.TO"] asx = ["CBA.AX", "BHP.AX", "WES.AX"]

```
return sp500 + dax_symbols + ceske + polske + lse + nasdaq + nyse + tokyo + xetra + bse + tsx + asx
```

@st.cache\_data(show\_spinner=False) def get\_stock\_info(ticker): try: stock = yf.Ticker(ticker) info = stock.info price = stock.history(period="1d")["Close"][-1] hist\_div = stock.dividends last\_div = hist\_div[-1] if not hist\_div.empty else 0 payout\_ratio = info.get("payoutRatio") return { "Ticker": ticker, "Název": info.get("longName"), "Burza": ticker.split(".")[-1] if "." in ticker else "USA", "Měna": info.get("currency", "USD"), "Sektor": info.get("sector"), "Cena": price, "P/E": info.get("trailingPE"), "ROE": info.get("returnOnEquity"), "EPS": info.get("trailingEps"), "Dividenda": last\_div, "Payout Ratio": payout\_ratio, "D/E poměr": info.get("debtToEquity"), "Free Cash Flow": info.get("freeCashflow"), "Market Cap": info.get("marketCap"), "Beta": info.get("beta"), "Fáze": classify\_phase(info), "Skóre": calculate\_score(info) } except: return None

def classify\_phase(info): eps = info.get("trailingEps", 0) roe = info.get("returnOnEquity", 0) mc = info.get("marketCap", 0) if eps > 2 and roe > 0.15: return "📈 Růstová" elif mc > 5e10: return "🏦 Stabilní" else: return "💎 Hodnotová"

def calculate\_score(info): score = 0 payout\_ratio = info.get("payoutRatio") or 0 eps = info.get("trailingEps", 0) phase = classify\_phase(info) if info.get("trailingPE") and info["trailingPE"] < 15: score += 3 if payout\_ratio > 0: if phase == "📈 Růstová" and 0.1 < payout\_ratio < 0.4: score += 2 elif phase == "🏦 Stabilní" and 0.3 < payout\_ratio < 0.7: score += 2 elif phase == "💎 Hodnotová" and 0.5 < payout\_ratio < 0.8: score += 2 if eps > 1 and info.get("dividendYield", 0) > 0: score += 2 if info.get("freeCashflow") and info["freeCashflow"] > 0: score += 2 beta = info.get("beta") if beta and 0.7 <= beta <= 1.3: score += 1 return min(score, 10)

def log\_score\_history(df): today = datetime.today().strftime("%Y-%m-%d") log\_df = df[["Ticker", "Skóre"]].copy() log\_df["Datum"] = today if os.path.exists(HISTORY\_FILE): old = pd.read\_csv(HISTORY\_FILE) combined = pd.concat([old, log\_df], ignore\_index=True) combined.drop\_duplicates(subset=["Ticker", "Datum"], inplace=True) else: combined = log\_df combined.to\_csv(HISTORY\_FILE, index=False)

def generate\_price\_chart(ticker, period="1y", output\_path="chart.png"): hist = yf.Ticker(ticker).history(period=period) if not hist.empty: plt.figure(figsize=(10, 4)) plt.plot(hist.index, hist["Close"], label="Cena") plt.title(f"Vývoj ceny za {period} – {ticker}") plt.xlabel("Datum") plt.ylabel("Cena") plt.grid(True) plt.tight\_layout() plt.savefig(output\_path) return output\_path return None

def generate\_pdf(ticker, selected, chart\_path): env = Environment(loader=FileSystemLoader('.')) template = env.get\_template("template.html") html = template.render( ticker=ticker, name=selected["Název"], sector=selected["Sektor"], phase=selected["Fáze"], metrics=selected, chart\_path=chart\_path, date=datetime.today().strftime("%d.%m.%Y %H:%M") ) pdfkit.from\_string(html, "report.pdf")

def send\_email\_with\_attachment(receiver\_email): msg = EmailMessage() msg["Subject"] = "Tvůj PDF report – akcie" msg["From"] = "[noreply@example.com](mailto\:noreply@example.com)" msg["To"] = receiver\_email msg.set\_content("V příloze nalezneš PDF report tvé vybrané akcie.") with open("report.pdf", "rb") as f: msg.add\_attachment(f.read(), maintype="application", subtype="pdf", filename="report.pdf") with smtplib.SMTP("smtp.example.com", 587) as server: server.starttls() server.login("[your\_email@example.com](mailto\:your_email@example.com)", "your\_password") server.send\_message(msg)

# === ZAČÁTEK HLAVNÍHO KÓDU ===

page = st.sidebar.radio("📄 Stránka", ["📋 Dashboard", "⭐ Top výběr", "🧮 Kalkulačka investic"])

with st.spinner("Načítám data..."): tickers = get\_all\_tickers() data = [get\_stock\_info(t) for t in tickers] df = pd.DataFrame([d for d in data if d]) log\_score\_history(df)

currency = df["Měna"].mode().values[0] if "Měna" in df.columns else "USD" df["Cena"] = df["Cena"].map(lambda x: f"{currency} {x:.2f}") df["ROE"] = df["ROE"] \* 100 df["ROE"] = df["ROE"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A") df["Dividenda"] = df["Dividenda"].map(lambda x: f"{currency} {x:.2f}" if pd.notnull(x) else "N/A") df["Free Cash Flow"] = df["Free Cash Flow"].map(lambda x: f"{x/1e6:.0f} mil." if pd.notnull(x) else "N/A") df["Market Cap"] = df["Market Cap"].map(lambda x: f"{x/1e9:.1f} mld." if pd.notnull(x) else "N/A") df["Payout Ratio"] = df["Payout Ratio"].map(lambda x: f"{x:.0%}" if pd.notnull(x) else "N/A")

st.sidebar.header("🔍 Filtrování") sector = st.sidebar.multiselect("Sektor", sorted(df["Sektor"].dropna().unique())) burza = st.sidebar.multiselect("Burza", sorted(df["Burza"].unique())) faze = st.sidebar.multiselect("Fáze", sorted(df["Fáze"].unique())) min\_skore = st.sidebar.slider("Minimální skóre", 1, 10, 6)

filtered = df.copy() if sector: filtered = filtered[filtered["Sektor"].isin(sector)] if burza: filtered = filtered[filtered["Burza"].isin(burza)] if faze: filtered = filtered[filtered["Fáze"].isin(faze)] filtered = filtered[filtered["Skóre"] >= min\_skore]

if page == "⭐ Top výběr": st.subheader("⭐ TOP 50 akcií podle skóre") top5 = filtered.sort\_values("Skóre", ascending=False).head(50) st.dataframe(top5.set\_index("Ticker"), use\_container\_width=True)

if page == "📋 Dashboard": st.subheader("📋 Výběr akcie") ticker = st.selectbox("Vyber akcii", options=filtered["Ticker"].unique()) selected = filtered[filtered["Ticker"] == ticker].iloc[0]

styled\_df = filtered.copy() styled\_df["Skóre"] = styled\_df["Skóre"].astype(int)

styled\_df["ROE"] = df["ROE"] styled\_df["Dividenda"] = df["Dividenda"]

st.dataframe( styled\_df.style.format(precision=2), use\_container\_width=True )

st.markdown("---") st.markdown(f"### 📊 Vývoj ceny pro: {ticker}") for label, period in {"ROK": "1y", "3 ROKY": "3y", "5 LET": "5y"}.items(): hist = yf.Ticker(ticker).history(period=period) if not hist.empty: change = ((hist["Close"][-1] - hist["Close"][0]) / hist["Close"][0]) \* 100 trend = "🔺" if change >= 0 else "🔻" st.markdown(f"### {label}: {trend} {change:.2f}%") fig = px.line(hist, x=hist.index, y="Close", title=f"Vývoj ceny za {label}") st.plotly\_chart(fig, use\_container\_width=True)

if os.path.exists(HISTORY\_FILE): st.subheader("📈 Vývoj skóre – historie") history\_df = pd.read\_csv(HISTORY\_FILE) chart\_df = history\_df[history\_df["Ticker"] == ticker] if not chart\_df.empty: fig = px.line(chart\_df, x="Datum", y="Skóre", title=f"Skóre v čase – {ticker}") st.plotly\_chart(fig, use\_container\_width=True)

# 📄 Export PDF a odeslání e-mailem

st.markdown("---") if st.button("📄 Exportovat PDF report"): chart\_path = generate\_price\_chart(ticker) generate\_pdf(ticker, selected, chart\_path) with open("report.pdf", "rb") as f: st.download\_button("📥 Stáhnout PDF", data=f, file\_name=f"{ticker}\_report.pdf", mime="application/pdf")

email = st.text\_input("📧 Zadat e-mail pro odeslání PDF:") if st.button("✉️ Odeslat e-mailem"): if email: try: send\_email\_with\_attachment(email) st.success(f"PDF report odeslán na {email}") except Exception as e: st.error(f"Chyba při odesílání: {e}") else: st.warning("Zadej prosím e-mailovou adresu.")

csv = filtered.to\_csv(index=False).encode("utf-8") st.download\_button("📥 Export do CSV", data=csv, file\_name="akcie\_filtr.csv", mime="text/csv")

st.caption("Data: Yahoo Finance + Wikipedia")

# === Kalkulačka investic ===
if page == "🧮 Kalkulačka investic":
    st.title("💰 Investiční kalkulačka – simulace pravidelného nákupu akcií")

    invest_per_month = st.number_input("Měsíční investice (USD)", min_value=10, value=1000, step=10)
    start_date = st.date_input("Začátek investování", value=datetime(2020, 1, 1))
    top_n = st.selectbox("Počet TOP akcií (podle skóre 10–8)", [10, 30, 50])

    @st.cache_data
    def load_data():
        df = pd.read_csv("skore_history.csv")
        prices = {}
        tickers = df[df['Skóre'] >= 8]['Ticker'].unique()
        for ticker in tickers:
            hist = yf.Ticker(ticker).history(period="max")["Close"]
            prices[ticker] = hist
        return df, prices

    df, prices = load_data()
    score_scale = lambda x: int((x / 10) * 100)
    df["Skóre_scaled"] = df["Skóre"].apply(score_scale)

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

    dividends_data = get_dividends(df['Ticker'].unique())
    portfolio = []
    reinvested_cash = 0
    cumulative_dividends = 0
    monthly_portfolio = []
    current_date = pd.to_datetime(start_date)

    while current_date < datetime.today():
        current_portfolio = []
        month_df = df[df["Datum"] == current_date.strftime("%Y-%m-%d")]
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

mám tenhle skript&#x20;

\# STABILNÍ DASHBOARD (barevné skóre + top 5 + PDF a email)

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



st.set\_page\_config(layout="wide")

st.title("📈 Investiční akcie – růst, zisk a hodnota")



HISTORY\_FILE = "skore\_history.csv"



@st.cache\_data(show\_spinner=False)

def get\_all\_tickers():

&#x20;   sp500 = pd.read\_html("[https://en.wikipedia.org/wiki/List\_of\_S%26P\_500\_companies")[0\]["Symbol"\].tolist(](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"\)\[0]\["Symbol"].tolist\())

&#x20;   dax\_table = pd.read\_html("[https://en.wikipedia.org/wiki/DAX")[1](https://en.wikipedia.org/wiki/DAX"\)\[1)]

&#x20;   dax\_symbols = dax\_table[dax\_table.columns[0]].tolist()

&#x20;   ceske = ["CEZ.PR", "KOMB.PR", "MONET.PR"]

&#x20;   polske = ["PKN.OL", "PKOBP.OL", "PEKAO.OL"]

&#x20;   lse = ["HSBA.L", "TSCO.L", "BP.L"]

&#x20;   nasdaq\_tables = pd.read\_html("[https://en.wikipedia.org/wiki/NASDAQ-100](https://en.wikipedia.org/wiki/NASDAQ-100)")

&#x20;   for table in nasdaq\_tables:

&#x20;       if any(isinstance(col, str) and col.lower() in ["ticker", "symbol"] for col in table.columns):

&#x20;           nasdaq = table[table.columns[0]].tolist()

&#x20;           break

&#x20;   else:

&#x20;       nasdaq = []

&#x20;   nyse = ["JNJ", "PG", "KO", "DIS", "BA", "CAT", "MMM"]  # ukázka

&#x20;   tokyo = ["7203.T", "6758.T", "9984.T"]

&#x20;   xetra = ["SAP.DE", "DTE.DE", "BAS.DE", "ALV.DE"]

&#x20;   bse = ["RELIANCE.BO", "TCS.BO", "INFY.BO"]

&#x20;   tsx = ["RY.TO", "TD.TO", "BNS.TO"]

&#x20;   asx = ["CBA.AX", "BHP.AX", "WES.AX"]

&#x20;  &#x20;

&#x20;   return sp500 + dax\_symbols + ceske + polske + lse + nasdaq + nyse + tokyo + xetra + bse + tsx + asx



@st.cache\_data(show\_spinner=False)

def get\_stock\_info(ticker):

&#x20;   try:

&#x20;       stock = yf.Ticker(ticker)

&#x20;       info = stock.info

&#x20;       price = stock.history(period="1d")["Close"][-1]

&#x20;       hist\_div = stock.dividends

&#x20;       last\_div = hist\_div[-1] if not hist\_div.empty else 0

&#x20;       payout\_ratio = info.get("payoutRatio")

&#x20;       return {

&#x20;           "Ticker": ticker,

&#x20;           "Název": info.get("longName"),

&#x20;           "Burza": ticker.split(".")[-1] if "." in ticker else "USA",

&#x20;           "Měna": info.get("currency", "USD"),

&#x20;           "Sektor": info.get("sector"),

&#x20;           "Cena": price,

&#x20;           "P/E": info.get("trailingPE"),

&#x20;           "ROE": info.get("returnOnEquity"),

&#x20;           "EPS": info.get("trailingEps"),

&#x20;           "Dividenda": last\_div,

&#x20;           "Payout Ratio": payout\_ratio,

&#x20;           "D/E poměr": info.get("debtToEquity"),

&#x20;           "Free Cash Flow": info.get("freeCashflow"),

&#x20;           "Market Cap": info.get("marketCap"),

&#x20;           "Beta": info.get("beta"),

&#x20;           "Fáze": classify\_phase(info),

&#x20;           "Skóre": calculate\_score(info)

&#x20;       }

&#x20;   except:

&#x20;       return None



def classify\_phase(info):

&#x20;   eps = info.get("trailingEps", 0)

&#x20;   roe = info.get("returnOnEquity", 0)

&#x20;   mc = info.get("marketCap", 0)

&#x20;   if eps > 2 and roe > 0.15:

&#x20;       return "📈 Růstová"

&#x20;   elif mc > 5e10:

&#x20;       return "🏦 Stabilní"

&#x20;   else:

&#x20;       return "💎 Hodnotová"



def calculate\_score(info):

&#x20;   score = 0

&#x20;   payout\_ratio = info.get("payoutRatio") or 0

&#x20;   eps = info.get("trailingEps", 0)

&#x20;   phase = classify\_phase(info)

&#x20;   if info.get("trailingPE") and info["trailingPE"] < 15: score += 3

&#x20;   if payout\_ratio > 0:

&#x20;       if phase == "📈 Růstová" and 0.1 < payout\_ratio < 0.4: score += 2

&#x20;       elif phase == "🏦 Stabilní" and 0.3 < payout\_ratio < 0.7: score += 2

&#x20;       elif phase == "💎 Hodnotová" and 0.5 < payout\_ratio < 0.8: score += 2

&#x20;   if eps > 1 and info.get("dividendYield", 0) > 0: score += 2

&#x20;   if info.get("freeCashflow") and info["freeCashflow"] > 0: score += 2

&#x20;   beta = info.get("beta")

&#x20;   if beta and 0.7 <= beta <= 1.3: score += 1

&#x20;   return min(score, 10)



def log\_score\_history(df):

&#x20;   today = datetime.today().strftime("%Y-%m-%d")

&#x20;   log\_df = df[["Ticker", "Skóre"]].copy()

&#x20;   log\_df["Datum"] = today

&#x20;   if os.path.exists(HISTORY\_FILE):

&#x20;       old = pd.read\_csv(HISTORY\_FILE)

&#x20;       combined = pd.concat([old, log\_df], ignore\_index=True)

&#x20;       combined.drop\_duplicates(subset=["Ticker", "Datum"], inplace=True)

&#x20;   else:

&#x20;       combined = log\_df

&#x20;   combined.to\_csv(HISTORY\_FILE, index=False)



def generate\_price\_chart(ticker, period="1y", output\_path="chart.png"):

&#x20;   hist = yf.Ticker(ticker).history(period=period)

&#x20;   if not hist.empty:

&#x20;       plt.figure(figsize=(10, 4))

&#x20;       plt.plot(hist.index, hist["Close"], label="Cena")

&#x20;       plt.title(f"Vývoj ceny za {period} – {ticker}")

&#x20;       plt.xlabel("Datum")

&#x20;       plt.ylabel("Cena")

&#x20;       plt.grid(True)

&#x20;       plt.tight\_layout()

&#x20;       plt.savefig(output\_path)

&#x20;       return output\_path

&#x20;   return None



def generate\_pdf(ticker, selected, chart\_path):

&#x20;   env = Environment(loader=FileSystemLoader('.'))

&#x20;   template = env.get\_template("template.html")

&#x20;   html = template.render(

&#x20;       ticker=ticker,

&#x20;       name=selected["Název"],

&#x20;       sector=selected["Sektor"],

&#x20;       phase=selected["Fáze"],

&#x20;       metrics=selected,

&#x20;       chart\_path=chart\_path,

&#x20;       date=datetime.today().strftime("%d.%m.%Y %H:%M")

&#x20;   )

&#x20;   pdfkit.from\_string(html, "report.pdf")



def send\_email\_with\_attachment(receiver\_email):

&#x20;   msg = EmailMessage()

&#x20;   msg["Subject"] = "Tvůj PDF report – akcie"

&#x20;   msg["From"] = "[noreply@example.com](mailto\:noreply@example.com)"

&#x20;   msg["To"] = receiver\_email

&#x20;   msg.set\_content("V příloze nalezneš PDF report tvé vybrané akcie.")

&#x20;   with open("report.pdf", "rb") as f:

&#x20;       msg.add\_attachment(f.read(), maintype="application", subtype="pdf", filename="report.pdf")

&#x20;   with smtplib.SMTP("smtp.example.com", 587) as server:

&#x20;       server.starttls()

&#x20;       server.login("[your\_email@example.com](mailto\:your_email@example.com)", "your\_password")

&#x20;       server.send\_message(msg)



\# === ZAČÁTEK HLAVNÍHO KÓDU ===



page = st.sidebar.radio("📄 Stránka", ["📋 Dashboard", "⭐ Top výběr"])



with st.spinner("Načítám data..."):

&#x20;   tickers = get\_all\_tickers()

&#x20;   data = [get\_stock\_info(t) for t in tickers]

&#x20;   df = pd.DataFrame([d for d in data if d])

&#x20;   log\_score\_history(df)



currency = df["Měna"].mode().values[0] if "Měna" in df.columns else "USD"

df["Cena"] = df["Cena"].map(lambda x: f"{currency} {x:.2f}")

df["ROE"] = df["ROE"] \* 100

df["ROE"] = df["ROE"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")

df["Dividenda"] = df["Dividenda"].map(lambda x: f"{currency} {x:.2f}" if pd.notnull(x) else "N/A")

df["Free Cash Flow"] = df["Free Cash Flow"].map(lambda x: f"{x/1e6:.0f} mil." if pd.notnull(x) else "N/A")

df["Market Cap"] = df["Market Cap"].map(lambda x: f"{x/1e9:.1f} mld." if pd.notnull(x) else "N/A")

df["Payout Ratio"] = df["Payout Ratio"].map(lambda x: f"{x:.0%}" if pd.notnull(x) else "N/A")



st.sidebar.header("🔍 Filtrování")

sector = st.sidebar.multiselect("Sektor", sorted(df["Sektor"].dropna().unique()))

burza = st.sidebar.multiselect("Burza", sorted(df["Burza"].unique()))

faze = st.sidebar.multiselect("Fáze", sorted(df["Fáze"].unique()))

min\_skore = st.sidebar.slider("Minimální skóre", 1, 10, 6)



filtered = df.copy()

if sector: filtered = filtered[filtered["Sektor"].isin(sector)]

if burza: filtered = filtered[filtered["Burza"].isin(burza)]

if faze: filtered = filtered[filtered["Fáze"].isin(faze)]

filtered = filtered[filtered["Skóre"] >= min\_skore]



if page == "⭐ Top výběr":

&#x20;   st.subheader("⭐ TOP 50 akcií podle skóre")

&#x20;   top5 = filtered.sort\_values("Skóre", ascending=False).head(50)

&#x20;   st.dataframe(top5.set\_index("Ticker"), use\_container\_width=True)



if page == "📋 Dashboard":

&#x20;   st.subheader("📋 Výběr akcie")

ticker = st.selectbox("Vyber akcii", options=filtered["Ticker"].unique())

selected = filtered[filtered["Ticker"] == ticker].iloc[0]



styled\_df = filtered.copy()

styled\_df["Skóre"] = styled\_df["Skóre"].astype(int)



styled\_df["ROE"] = df["ROE"]

styled\_df["Dividenda"] = df["Dividenda"]



st.dataframe(

&#x20;   styled\_df.style.format(precision=2),

&#x20;   use\_container\_width=True

)



st.markdown("---")

st.markdown(f"### 📊 Vývoj ceny pro: {ticker}")

for label, period in {"ROK": "1y", "3 ROKY": "3y", "5 LET": "5y"}.items():

&#x20;   hist = yf.Ticker(ticker).history(period=period)

&#x20;   if not hist.empty:

&#x20;       change = ((hist["Close"][-1] - hist["Close"][0]) / hist["Close"][0]) \* 100

&#x20;       trend = "🔺" if change >= 0 else "🔻"

&#x20;       st.markdown(f"### {label}: {trend} {change:.2f}%")

&#x20;       fig = px.line(hist, x=hist.index, y="Close", title=f"Vývoj ceny za {label}")

&#x20;       st.plotly\_chart(fig, use\_container\_width=True)



if os.path.exists(HISTORY\_FILE):

&#x20;   st.subheader("📈 Vývoj skóre – historie")

&#x20;   history\_df = pd.read\_csv(HISTORY\_FILE)

&#x20;   chart\_df = history\_df[history\_df["Ticker"] == ticker]

&#x20;   if not chart\_df.empty:

&#x20;       fig = px.line(chart\_df, x="Datum", y="Skóre", title=f"Skóre v čase – {ticker}")

&#x20;       st.plotly\_chart(fig, use\_container\_width=True)



\# 📄 Export PDF a odeslání e-mailem

st.markdown("---")

if st.button("📄 Exportovat PDF report"):

&#x20;   chart\_path = generate\_price\_chart(ticker)

&#x20;   generate\_pdf(ticker, selected, chart\_path)

&#x20;   with open("report.pdf", "rb") as f:

&#x20;       st.download\_button("📥 Stáhnout PDF", data=f, file\_name=f"{ticker}\_report.pdf", mime="application/pdf")



email = st.text\_input("📧 Zadat e-mail pro odeslání PDF:")

if st.button("✉️ Odeslat e-mailem"):

&#x20;   if email:

&#x20;       try:

&#x20;           send\_email\_with\_attachment(email)

&#x20;           st.success(f"PDF report odeslán na {email}")

&#x20;       except Exception as e:

&#x20;           st.error(f"Chyba při odesílání: {e}")

&#x20;   else:

&#x20;       st.warning("Zadej prosím e-mailovou adresu.")



csv = filtered.to\_csv(index=False).encode("utf-8")

st.download\_button("📥 Export do CSV", data=csv, file\_name="akcie\_filtr.csv", mime="text/csv")



st.caption("Data: Yahoo Finance + Wikipedia")  jak to lze leješště zlepšit?

