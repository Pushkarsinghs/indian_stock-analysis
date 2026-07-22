import pandas as pd
import streamlit as st
import os

def get_data_dir():
    if os.path.exists("/content/streamlit_data"):
        return "/content/streamlit_data"
    for candidate in ["data", "streamlit_app/data", "../data"]:
        if os.path.exists(candidate):
            return candidate
    return "."

DATA_DIR = get_data_dir()

def safe_read(filename, parse_dates=None, fallback_cols=None):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        if fallback_cols:
            return pd.DataFrame(columns=fallback_cols)
        return pd.DataFrame()
    try:
        if parse_dates:
            return pd.read_csv(path, parse_dates=parse_dates)
        return pd.read_csv(path)
    except Exception as e:
        st.error("Error reading " + filename + ": " + str(e))
        if fallback_cols:
            return pd.DataFrame(columns=fallback_cols)
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_technical():    return safe_read("nifty50_technical_powerbi.csv", parse_dates=["Date"])
@st.cache_data(ttl=300)
def load_signals():      return safe_read("latest_signals.csv")
@st.cache_data(ttl=300)
def load_fundamentals(): return safe_read("nifty50_fundamentals_powerbi.csv")
@st.cache_data(ttl=300)
def load_sentiment():    return safe_read("nifty50_sentiment_powerbi.csv")
@st.cache_data(ttl=300)
def load_headlines():    return safe_read("nifty50_headlines_powerbi.csv", fallback_cols=["Ticker","Company","Headline","Label","Confidence","Polarity","Model"])
@st.cache_data(ttl=300)
def load_forecasts():    return safe_read("nifty50_forecasts_powerbi.csv", parse_dates=["Date"])
@st.cache_data(ttl=300)
def load_forecast_summary(): return safe_read("forecast_summary_powerbi.csv")
@st.cache_data(ttl=300)
def load_risk_metrics(): return safe_read("nifty50_risk_metrics_powerbi.csv")
@st.cache_data(ttl=300)
def load_portfolio_allocation():   return safe_read("portfolio_allocation_powerbi.csv")
@st.cache_data(ttl=300)
def load_portfolio_performance():  return safe_read("portfolio_performance_powerbi.csv")
@st.cache_data(ttl=300)
def load_backtest_equity():  return safe_read("backtest_equity_powerbi.csv", parse_dates=["Date"])
@st.cache_data(ttl=300)
def load_backtest_trades():  return safe_read("backtest_trades_powerbi.csv", parse_dates=["Date"])
@st.cache_data(ttl=300)
def load_backtest_summary(): return safe_read("backtest_summary_powerbi.csv")
@st.cache_data(ttl=300)
def load_forecast_accuracy(): return safe_read("forecast_accuracy_powerbi.csv", fallback_cols=["Ticker","Forecast_Date","Predicted","Actual","Abs_Error_Pct"])
@st.cache_data(ttl=300)
def load_mape_summary():      return safe_read("forecast_mape_summary_powerbi.csv", fallback_cols=["Ticker","MAPE_Pct","Predictions_Checked","Reliability"])
