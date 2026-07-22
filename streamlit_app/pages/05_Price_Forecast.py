import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_forecasts, load_forecast_summary, load_sentiment

st.set_page_config(page_title="Price Forecast", page_icon="🔮", layout="wide")
st.markdown('<style>[data-testid="stSidebar"]{background:#F0F2F5;}</style>', unsafe_allow_html=True)
st.markdown('<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);padding:20px;border-radius:10px;color:white;margin-bottom:20px;"><h2 style="margin:0">🔮 Price Forecast - 30-Day Prophet Predictions</h2></div>', unsafe_allow_html=True)

try:
    forecasts = load_forecasts()
    summary   = load_forecast_summary()
    sent      = load_sentiment()
except Exception as e:
    st.error("Error: " + str(e))
    st.stop()

if forecasts.empty:
    st.error("Forecast data not found.")
    st.stop()

forecasts["Date"] = pd.to_datetime(forecasts["Date"])
today_ts  = pd.Timestamp.today().normalize()
today_str = str(today_ts.date())

st.sidebar.header("Controls")
ticker = st.sidebar.selectbox("Select Stock", sorted(forecasts["Ticker"].unique()), index=0)

bull_fc    = int((summary["Expected_Change"]>0).sum()) if not summary.empty and "Expected_Change" in summary.columns else 0
best_gain  = float(summary["Expected_Change"].max())   if not summary.empty and "Expected_Change" in summary.columns else 0.0
worst_loss = float(summary["Expected_Change"].min())   if not summary.empty and "Expected_Change" in summary.columns else 0.0

c1,c2,c3 = st.columns(3)
c1.metric("Bullish Forecasts",  str(bull_fc)+" stocks")
c2.metric("Best Expected Gain", "+"+"{:.1f}".format(best_gain)+"%")
c3.metric("Worst Expected Loss","{:.1f}".format(worst_loss)+"%")

st.markdown("---")
ticker_clean = str(ticker).replace(".NS","")
st.subheader(ticker_clean + " - 30-Day Prophet Forecast")

stock_fc   = forecasts[forecasts["Ticker"]==ticker].sort_values("Date")
historical = stock_fc[stock_fc["Date"]<=today_ts]
future     = stock_fc[stock_fc["Date"]>today_ts]

fig = go.Figure()
if not historical.empty:
    fig.add_trace(go.Scatter(x=historical["Date"],y=historical["Forecast"],name="Historical Fitted",line=dict(color="#1F77B4",width=1.5)))
if not future.empty:
    fig.add_trace(go.Scatter(x=future["Date"],y=future["Forecast"],name="30-Day Forecast",line=dict(color="#2CA02C",width=2.5)))
    x_band = list(future["Date"]) + list(future["Date"].iloc[::-1])
    y_band = list(future["Upper_CI"]) + list(future["Lower_CI"].iloc[::-1])
    fig.add_trace(go.Scatter(x=x_band,y=y_band,fill="toself",fillcolor="rgba(44,160,44,0.12)",line=dict(color="rgba(255,255,255,0)"),name="80% CI"))

all_y = list(stock_fc["Forecast"].dropna())
if all_y:
    y_min = min(all_y)*0.995
    y_max = max(all_y)*1.005
    fig.add_trace(go.Scatter(x=[today_str,today_str],y=[y_min,y_max],mode="lines",line=dict(color="#FF7F0E",width=2,dash="dash"),name="Today"))
    fig.add_annotation(x=today_str,y=y_max,text="Today",showarrow=False,font=dict(color="#FF7F0E",size=11),yanchor="bottom")

fig.update_layout(height=450,template="plotly_white",xaxis_title="Date",yaxis_title="Price (Rs)",legend=dict(orientation="h",y=1.02))
st.plotly_chart(fig, use_container_width=True)

cl, cr = st.columns(2)
with cl:
    st.subheader("Expected 30-Day Change")
    if not summary.empty and "Expected_Change" in summary.columns:
        ss = summary.sort_values("Expected_Change",ascending=True)
        bar_colors    = ["#2CA02C" if float(v)>=0 else "#D62728" for v in ss["Expected_Change"]]
        ticker_labels = [str(t).replace(".NS","") for t in ss["Ticker"]]
        fig2 = go.Figure(go.Bar(x=ss["Expected_Change"],y=ticker_labels,orientation="h",marker_color=bar_colors,
                                text=["{:+.1f}%".format(float(v)) for v in ss["Expected_Change"]],textposition="outside"))
        fig2.add_vline(x=0,line_color="black",line_width=1)
        fig2.update_layout(height=500,template="plotly_white",xaxis_title="Expected Change (%)")
        st.plotly_chart(fig2, use_container_width=True)
with cr:
    st.subheader("Forecast Summary")
    if not summary.empty:
        dc = [c for c in ["Ticker","Current_Price","Forecast_30d","Expected_Change","Direction"] if c in summary.columns]
        disp = summary[dc]
        if "Expected_Change" in disp.columns:
            disp = disp.sort_values("Expected_Change",ascending=False)
        st.dataframe(disp, use_container_width=True, hide_index=True)

st.subheader("Sentiment vs Forecast")
if not sent.empty and "Sentiment_Score" in sent.columns and not summary.empty and "Expected_Change" in summary.columns:
    merged = summary.merge(sent[["Ticker","Sentiment_Score","Sentiment_Label"]],on="Ticker",how="left").dropna(subset=["Sentiment_Score","Expected_Change"])
    if not merged.empty:
        hover_cols = [c for c in ["Ticker","Sentiment_Label","Direction"] if c in merged.columns]
        fig3 = px.scatter(merged,x="Sentiment_Score",y="Expected_Change",color="Expected_Change",
                          color_continuous_scale=["#D62728","#FFFFFF","#2CA02C"],hover_data=hover_cols,text="Ticker")
        fig3.add_vline(x=50,line_dash="dash",line_color="gray",annotation_text="Neutral")
        fig3.add_hline(y=0,line_dash="dash",line_color="gray",annotation_text="No Change")
        fig3.update_traces(textposition="top center",textfont_size=7)
        fig3.update_layout(height=450,template="plotly_white")
        st.plotly_chart(fig3, use_container_width=True)
