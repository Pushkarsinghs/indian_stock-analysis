
import pandas as pd
import os
import streamlit as st

DATA_DIR = "/content/streamlit_data"

@st.cache_data(ttl=3600)
def load_technical():
    return pd.read_csv(
        f"{DATA_DIR}/nifty50_technical_powerbi.csv",
        parse_dates=["Date"]
    )

@st.cache_data(ttl=3600)
def load_signals():
    return pd.read_csv(f"{DATA_DIR}/latest_signals.csv")

@st.cache_data(ttl=3600)
def load_fundamentals():
    return pd.read_csv(
        f"{DATA_DIR}/nifty50_fundamentals_powerbi.csv"
    )

@st.cache_data(ttl=3600)
def load_sentiment():
    return pd.read_csv(
        f"{DATA_DIR}/nifty50_sentiment_powerbi.csv"
    )

@st.cache_data(ttl=3600)
def load_headlines():
    return pd.read_csv(
        f"{DATA_DIR}/nifty50_headlines_powerbi.csv"
    )

@st.cache_data(ttl=3600)
def load_forecasts():
    return pd.read_csv(
        f"{DATA_DIR}/nifty50_forecasts_powerbi.csv",
        parse_dates=["Date"]
    )

@st.cache_data(ttl=3600)
def load_forecast_summary():
    return pd.read_csv(
        f"{DATA_DIR}/forecast_summary_powerbi.csv"
    )

@st.cache_data(ttl=3600)
def load_risk_metrics():
    return pd.read_csv(
        f"{DATA_DIR}/nifty50_risk_metrics_powerbi.csv"
    )

@st.cache_data(ttl=3600)
def load_portfolio_allocation():
    return pd.read_csv(
        f"{DATA_DIR}/portfolio_allocation_powerbi.csv"
    )

@st.cache_data(ttl=3600)
def load_portfolio_performance():
    return pd.read_csv(
        f"{DATA_DIR}/portfolio_performance_powerbi.csv"
    )

@st.cache_data(ttl=3600)
def load_backtest_equity():
    return pd.read_csv(
        f"{DATA_DIR}/backtest_equity_powerbi.csv",
        parse_dates=["Date"]
    )

@st.cache_data(ttl=3600)
def load_backtest_trades():
    return pd.read_csv(
        f"{DATA_DIR}/backtest_trades_powerbi.csv",
        parse_dates=["Date"]
    )

@st.cache_data(ttl=3600)
def load_backtest_summary():
    return pd.read_csv(
        f"{DATA_DIR}/backtest_summary_powerbi.csv"
    )

@st.cache_data(ttl=3600)
def load_forecast_accuracy():
    return pd.read_csv(
        f"{DATA_DIR}/forecast_accuracy_powerbi.csv"
    )

@st.cache_data(ttl=3600)
def load_mape_summary():
    return pd.read_csv(
        f"{DATA_DIR}/forecast_mape_summary_powerbi.csv"
    )
