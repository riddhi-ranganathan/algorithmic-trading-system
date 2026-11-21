
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime

st.set_page_config(
    page_title="Algorithmic Trading System",
    layout="wide"
)

st.title("Algorithmic Trading System")
st.write(
    "Stock analysis, technical indicators, trading signals "
    "and historical strategy information."
)

st.caption(
    "Data source: Yahoo Finance. Data availability and delay "
    "depend on the provider. This dashboard is for educational "
    "and research purposes, not investment advice."
)

stocks = {
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HCLTech": "HCLTECH.NS"
}

company = st.selectbox(
    "Select Company",
    list(stocks.keys())
)

symbol = stocks[company]

period = st.selectbox(
    "Historical Data Period",
    ["6mo", "1y", "2y", "5y"]
)

@st.cache_data(ttl=300)
def get_stock_data(symbol, period):

    df = yf.download(
        symbol,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.dropna()

df = get_stock_data(symbol, period)

if df.empty:

    st.error("Stock data could not be downloaded.")

else:

    df["SMA_10"] = df["Close"].rolling(10).mean()
    df["SMA_30"] = df["Close"].rolling(30).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1/14,
        min_periods=14,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1/14,
        min_periods=14,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()

    df["MACD"] = ema12 - ema26

    latest = df.iloc[-1]

    st.subheader(company + " Stock Information")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Latest Available Close",
        round(float(latest["Close"]), 2)
    )

    col2.metric(
        "SMA 10",
        round(float(latest["SMA_10"]), 2)
        if pd.notna(latest["SMA_10"]) else "N/A"
    )

    col3.metric(
        "RSI",
        round(float(latest["RSI"]), 2)
        if pd.notna(latest["RSI"]) else "N/A"
    )

    st.subheader("Historical Price Chart")

    st.line_chart(df["Close"])

    st.subheader("Moving Average Comparison")

    st.line_chart(df[["Close", "SMA_10", "SMA_30"]])

    st.subheader("Technical Indicators")

    st.line_chart(df[["RSI", "MACD"]])

    st.subheader("Latest Trading Signals")

    if (
        latest["SMA_10"] > latest["SMA_30"]
        and df["SMA_10"].iloc[-2] <= df["SMA_30"].iloc[-2]
    ):
        sma_signal = "BUY"

    elif (
        latest["SMA_10"] < latest["SMA_30"]
        and df["SMA_10"].iloc[-2] >= df["SMA_30"].iloc[-2]
    ):
        sma_signal = "EXIT"

    else:
        sma_signal = "NO NEW SIGNAL"

    if (
        latest["RSI"] > 30
        and df["RSI"].iloc[-2] <= 30
    ):
        rsi_signal = "BUY"

    elif (
        latest["RSI"] < 70
        and df["RSI"].iloc[-2] >= 70
    ):
        rsi_signal = "EXIT"

    else:
        rsi_signal = "NO NEW SIGNAL"

    st.write("Moving Average Strategy:", sma_signal)
    st.write("RSI Strategy:", rsi_signal)

    st.subheader("Alert Notification")

    if sma_signal == "BUY":
        st.success("SMA strategy generated a BUY signal.")

    elif sma_signal == "EXIT":
        st.warning("SMA strategy generated an EXIT signal.")

    if rsi_signal == "BUY":
        st.success("RSI strategy generated a BUY signal.")

    elif rsi_signal == "EXIT":
        st.warning("RSI strategy generated an EXIT signal.")

    if sma_signal == "NO NEW SIGNAL" and rsi_signal == "NO NEW SIGNAL":
        st.info("No new trading signals for the latest available data.")

    st.subheader("Recent Stock Data")

    st.dataframe(df.tail(10))

    st.caption(
        "The displayed signals are indicator events, not "
        "personalised recommendations or guaranteed trade entries."
    )
