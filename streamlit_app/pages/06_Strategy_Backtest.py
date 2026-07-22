import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_backtest_equity, load_backtest_trades, load_backtest_summary

st.set_page_config(page_title="Strategy Backtest", page_icon="📊", layout="wide")
st.markdown('<style>[data-testid="stSidebar"]{background:#F0F2F5;}</style>', unsafe_allow_html=True)
st.markdown('<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);padding:20px;border-radius:10px;color:white;margin-bottom:20px;"><h2 style="margin:0">📊 Strategy Backtest - Signal vs Buy and Hold</h2><p style="margin:5px 0 0 0;opacity:0.85">Compares signal-based trading against passive buy and hold</p></div>', unsafe_allow_html=True)

try:
    equity  = load_backtest_equity()
    trades  = load_backtest_trades()
    summary = load_backtest_summary()
except Exception as e:
    st.error("Error: " + str(e))
    st.stop()

if equity.empty:
    st.error("Backtest data not found.")
    st.stop()

equity["Date"] = pd.to_datetime(equity["Date"])
if "Date" in trades.columns:
    trades["Date"] = pd.to_datetime(trades["Date"])

win_rate    = round(float((summary["Beat_Benchmark"]=="Yes").mean())*100,1) if not summary.empty and "Beat_Benchmark" in summary.columns else 0
med_outperf = round(float(summary["Outperformance_Pct"].median()),2) if not summary.empty and "Outperformance_Pct" in summary.columns else 0
best_stock  = str(summary.nlargest(1,"Outperformance_Pct")["Ticker"].values[0]).replace(".NS","") if not summary.empty and "Outperformance_Pct" in summary.columns else "N/A"

c1,c2,c3,c4 = st.columns(4)
c1.metric("Strategy Win Rate",     str(win_rate)+"%")
c2.metric("Median Outperformance", "{:+.2f}%".format(med_outperf))
c3.metric("Total Trades",          "{:,}".format(len(trades)))
c4.metric("Best Signal Stock",     best_stock)

st.markdown("---")
st.sidebar.header("Controls")
ticker       = st.sidebar.selectbox("Select Stock", sorted(equity["Ticker"].unique()), index=0)
ticker_clean = str(ticker).replace(".NS","")
stock_eq     = equity[equity["Ticker"]==ticker].sort_values("Date")

st.subheader(ticker_clean + " - Strategy vs Buy and Hold")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=stock_eq["Date"],y=stock_eq["Strategy_Equity"],name="Signal Strategy",line=dict(color="#2CA02C",width=2.5)))
fig1.add_trace(go.Scatter(x=stock_eq["Date"],y=stock_eq["BuyHold_Equity"],name="Buy and Hold",line=dict(color="#1F77B4",width=1.5,dash="dash")))
fig1.add_hline(y=100000,line_dash="dot",line_color="gray",annotation_text="Starting Capital Rs1,00,000")
fig1.update_layout(height=400,template="plotly_white",xaxis_title="Date",yaxis_title="Portfolio Value (Rs)",legend=dict(orientation="h",y=1.02))
st.plotly_chart(fig1, use_container_width=True)

cl, cr = st.columns(2)
with cl:
    st.subheader("Outperformance by Stock")
    if not summary.empty and "Outperformance_Pct" in summary.columns:
        ss            = summary.sort_values("Outperformance_Pct",ascending=True)
        bar_colors    = ["#2CA02C" if float(v)>=0 else "#D62728" for v in ss["Outperformance_Pct"]]
        ticker_labels = [str(t).replace(".NS","") for t in ss["Ticker"]]
        fig2 = go.Figure(go.Bar(x=ss["Outperformance_Pct"],y=ticker_labels,orientation="h",marker_color=bar_colors,
                                text=["{:+.1f}%".format(float(v)) for v in ss["Outperformance_Pct"]],textposition="outside"))
        fig2.add_vline(x=0,line_color="black",line_width=1)
        fig2.update_layout(height=500,template="plotly_white",xaxis_title="Outperformance (%)")
        st.plotly_chart(fig2, use_container_width=True)
with cr:
    st.subheader("Recent Trade Log")
    if not trades.empty:
        st_trades = trades[trades["Ticker"]==ticker].sort_values("Date",ascending=False).head(20)
        if not st_trades.empty:
            dc = [c for c in ["Date","Action","Price","Signal"] if c in st_trades.columns]
            st.dataframe(st_trades[dc], use_container_width=True, hide_index=True)
        else:
            st.info("No trades for " + ticker_clean)

st.subheader("Full Backtest Summary")
if not summary.empty:
    dc = [c for c in ["Ticker","Strategy_Return_Pct","BuyHold_Return_Pct","Outperformance_Pct","Num_Trades","Beat_Benchmark"] if c in summary.columns]
    disp = summary[dc]
    if "Outperformance_Pct" in disp.columns:
        disp = disp.sort_values("Outperformance_Pct",ascending=False)
    st.dataframe(disp, use_container_width=True, hide_index=True)
