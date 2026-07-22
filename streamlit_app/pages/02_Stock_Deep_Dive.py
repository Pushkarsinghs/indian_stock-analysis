import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical, load_signals

st.set_page_config(page_title="Stock Deep Dive", page_icon="🔍", layout="wide")
st.markdown('<style>[data-testid="stSidebar"]{background:#F0F2F5;}.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)
st.markdown('<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);padding:20px;border-radius:10px;color:white;margin-bottom:20px;"><h2 style="margin:0">🔍 Stock Deep Dive - Technical Analysis</h2></div>', unsafe_allow_html=True)

df      = load_technical()
signals = load_signals()

if df.empty:
    st.error("Technical data not found.")
    st.stop()

df["Date"] = pd.to_datetime(df["Date"])

st.sidebar.header("Controls")
ticker  = st.sidebar.selectbox("Select Stock", sorted(df["Ticker"].unique()), index=0)
period  = st.sidebar.selectbox("Date Range", ["1 Month","3 Months","6 Months","1 Year"], index=3)
show_bb  = st.sidebar.checkbox("Bollinger Bands", value=True)
show_sma = st.sidebar.checkbox("Moving Averages", value=True)

stock  = df[df["Ticker"]==ticker].copy().sort_values("Date")
days   = {"1 Month":30,"3 Months":90,"6 Months":180,"1 Year":365}[period]
cutoff = stock["Date"].max() - pd.Timedelta(days=days)
stock  = stock[stock["Date"] >= cutoff]

if stock.empty:
    st.warning("No data for selected filters")
    st.stop()

latest     = stock.iloc[-1]
signal_row = signals[signals["Ticker"]==ticker] if not signals.empty else pd.DataFrame()
signal_val = str(signal_row["Signal"].values[0]) if not signal_row.empty else "N/A"

close_val = float(latest["Close"])
rsi_val   = float(latest["RSI"])  if pd.notna(latest.get("RSI",  None)) else 0.0
macd_val  = float(latest["MACD"]) if pd.notna(latest.get("MACD", None)) else 0.0
ret_val   = float(latest["Daily_Return"])*100 if pd.notna(latest.get("Daily_Return", None)) else 0.0

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Price",  "Rs" + "{:,.2f}".format(close_val))
c2.metric("RSI",    "{:.1f}".format(rsi_val))
c3.metric("MACD",   "{:.2f}".format(macd_val))
c4.metric("Signal", signal_val)
c5.metric("Return", "{:.2f}%".format(ret_val), delta="{:.2f}%".format(ret_val))

fig = make_subplots(
    rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
    subplot_titles=[str(ticker)+" Price Chart","Volume","RSI (14)","MACD"],
    row_heights=[0.45,0.15,0.20,0.20]
)
fig.add_trace(go.Scatter(x=stock["Date"],y=stock["Close"],name="Close",line=dict(color="#1F77B4",width=2)),row=1,col=1)
if show_sma and "SMA_20" in stock.columns:
    fig.add_trace(go.Scatter(x=stock["Date"],y=stock["SMA_20"],name="SMA 20",line=dict(color="#FF7F0E",width=1.5,dash="dash")),row=1,col=1)
    fig.add_trace(go.Scatter(x=stock["Date"],y=stock["SMA_50"],name="SMA 50",line=dict(color="#2CA02C",width=1.5,dash="dash")),row=1,col=1)
    fig.add_trace(go.Scatter(x=stock["Date"],y=stock["EMA_20"],name="EMA 20",line=dict(color="#9467BD",width=1,dash="dot")),row=1,col=1)
if show_bb and "BB_Upper" in stock.columns:
    fig.add_trace(go.Scatter(x=stock["Date"],y=stock["BB_Upper"],line=dict(color="#D62728",width=1,dash="dot"),showlegend=False),row=1,col=1)
    fig.add_trace(go.Scatter(x=stock["Date"],y=stock["BB_Lower"],line=dict(color="#2CA02C",width=1,dash="dot"),fill="tonexty",fillcolor="rgba(128,128,128,0.08)",showlegend=False),row=1,col=1)
vol_colors = ["#2CA02C" if r>=0 else "#D62728" for r in stock["Daily_Return"].fillna(0)]
fig.add_trace(go.Bar(x=stock["Date"],y=stock["Volume"],marker_color=vol_colors,showlegend=False),row=2,col=1)
if "RSI" in stock.columns:
    fig.add_trace(go.Scatter(x=stock["Date"],y=stock["RSI"],name="RSI",line=dict(color="#9467BD",width=1.5)),row=3,col=1)
    fig.add_hline(y=70,line_dash="dash",line_color="#D62728",annotation_text="Overbought",row=3,col=1)
    fig.add_hline(y=30,line_dash="dash",line_color="#2CA02C",annotation_text="Oversold",row=3,col=1)
if "MACD" in stock.columns:
    fig.add_trace(go.Scatter(x=stock["Date"],y=stock["MACD"],name="MACD",line=dict(color="#1F77B4",width=1.5)),row=4,col=1)
    fig.add_trace(go.Scatter(x=stock["Date"],y=stock["MACD_Signal"],name="Signal Line",line=dict(color="#D62728",width=1.5,dash="dash")),row=4,col=1)
    macd_colors = ["#2CA02C" if v>=0 else "#D62728" for v in stock["MACD_Hist"].fillna(0)]
    fig.add_trace(go.Bar(x=stock["Date"],y=stock["MACD_Hist"],marker_color=macd_colors,showlegend=False),row=4,col=1)
    fig.add_hline(y=0,line_color="black",line_width=0.8,row=4,col=1)

fig.update_layout(height=750,template="plotly_white",legend=dict(orientation="h",y=1.02),xaxis_rangeslider_visible=False,margin=dict(t=40,b=20))
fig.update_yaxes(title_text="Price (Rs)",row=1,col=1)
fig.update_yaxes(title_text="Volume",row=2,col=1)
fig.update_yaxes(title_text="RSI",range=[0,100],row=3,col=1)
fig.update_yaxes(title_text="MACD",row=4,col=1)
st.plotly_chart(fig, use_container_width=True)
st.caption("Latest: " + str(stock["Date"].max().date()) + "  |  " + str(len(stock)) + " trading days")
