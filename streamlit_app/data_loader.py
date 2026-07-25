import pandas as pd
import streamlit as st
import os
from datetime import datetime

def get_data_dir():
    """
    Finds the correct data directory automatically.
    Works in Colab, local development, and Streamlit Cloud.
    """
    candidates = [
        "/content/streamlit_data",
        "data",
        "streamlit_app/data",
        "../data"
    ]
    for path in candidates:
        if os.path.exists(path):
            test_file = os.path.join(path, "latest_signals.csv")
            if os.path.exists(test_file):
                return path
    for path in candidates:
        if os.path.exists(path):
            return path
    return "."

DATA_DIR = get_data_dir()

def get_file_date(filename):
    """
    Returns the last modified date of a data file.
    Used to show users when data was last updated.
    """
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    return "Unknown"

def safe_read(filename, parse_dates=None, fallback_cols=None):
    """
    Safely reads a CSV file with proper error handling.
    Returns empty DataFrame with correct columns if file missing.
    """
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        if fallback_cols:
            return pd.DataFrame(columns=fallback_cols)
        return pd.DataFrame()
    try:
        size = os.path.getsize(path)
        if size < 10:
            if fallback_cols:
                return pd.DataFrame(columns=fallback_cols)
            return pd.DataFrame()
        if parse_dates:
            return pd.read_csv(path, parse_dates=parse_dates)
        return pd.read_csv(path)
    except Exception as e:
        st.error("Error reading " + filename + ": " + str(e))
        if fallback_cols:
            return pd.DataFrame(columns=fallback_cols)
        return pd.DataFrame()

# TTL = 600 seconds (10 minutes)
# Data auto-refreshes every 10 minutes if files have changed

@st.cache_data(ttl=600)
def load_technical():
    return safe_read(
        "nifty50_technical_powerbi.csv",
        parse_dates=["Date"]
    )

@st.cache_data(ttl=600)
def load_signals():
    return safe_read("latest_signals.csv")

@st.cache_data(ttl=600)
def load_fundamentals():
    return safe_read("nifty50_fundamentals_powerbi.csv")

@st.cache_data(ttl=600)
def load_sentiment():
    return safe_read("nifty50_sentiment_powerbi.csv")

@st.cache_data(ttl=600)
def load_headlines():
    return safe_read(
        "nifty50_headlines_powerbi.csv",
        fallback_cols=[
            "Ticker","Company","Headline",
            "Label","Confidence","Polarity","Model"
        ]
    )

@st.cache_data(ttl=600)
def load_forecasts():
    return safe_read(
        "nifty50_forecasts_powerbi.csv",
        parse_dates=["Date"]
    )

@st.cache_data(ttl=600)
def load_forecast_summary():
    return safe_read("forecast_summary_powerbi.csv")

@st.cache_data(ttl=600)
def load_risk_metrics():
    return safe_read("nifty50_risk_metrics_powerbi.csv")

@st.cache_data(ttl=600)
def load_portfolio_allocation():
    return safe_read("portfolio_allocation_powerbi.csv")

@st.cache_data(ttl=600)
def load_portfolio_performance():
    return safe_read("portfolio_performance_powerbi.csv")

@st.cache_data(ttl=600)
def load_backtest_equity():
    return safe_read(
        "backtest_equity_powerbi.csv",
        parse_dates=["Date"]
    )

@st.cache_data(ttl=600)
def load_backtest_trades():
    return safe_read(
        "backtest_trades_powerbi.csv",
        parse_dates=["Date"]
    )

@st.cache_data(ttl=600)
def load_backtest_summary():
    return safe_read("backtest_summary_powerbi.csv")

@st.cache_data(ttl=600)
def load_forecast_accuracy():
    return safe_read(
        "forecast_accuracy_powerbi.csv",
        fallback_cols=[
            "Ticker","Forecast_Date",
            "Predicted","Actual","Abs_Error_Pct"
        ]
    )

@st.cache_data(ttl=600)
def load_mape_summary():
    return safe_read(
        "forecast_mape_summary_powerbi.csv",
        fallback_cols=[
            "Ticker","MAPE_Pct",
            "Predictions_Checked","Reliability"
        ]
    )

def get_data_freshness():
    """
    Returns information about how fresh the data is.
    Call this to show users the last update time.
    """
    signals_path = os.path.join(DATA_DIR, "latest_signals.csv")
    if not os.path.exists(signals_path):
        return {
            "last_updated": "Unknown",
            "is_fresh": False,
            "hours_old": 999
        }
    ts       = os.path.getmtime(signals_path)
    dt       = datetime.fromtimestamp(ts)
    now      = datetime.now()
    hours_old = (now - dt).total_seconds() / 3600

    return {
        "last_updated": dt.strftime("%d %b %Y %H:%M IST"),
        "is_fresh":     hours_old < 24,
        "hours_old":    round(hours_old, 1)
    }
