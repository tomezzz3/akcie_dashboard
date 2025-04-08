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
