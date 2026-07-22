import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_risk_metrics, load_portfolio_allocation, load_portfolio_performance

st.set_page_config(page_title="Portfolio and Risk", page_icon="💼", layout="wide")
st.markdown('<style>[data-testid="stSidebar"]{background:#F0F2F5;}</style>', unsafe_allow_html=True)
st.markdown('<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);padding:20px;border-radius:10px;color:white;margin-bottom:20px;"><h2 style="margin:0">💼 Portfolio and Risk Analysis - Efficient Frontier</h2></div>', unsafe_allow_html=True)

risk  = load_risk_metrics()
alloc = load_portfolio_allocation()
perf  = load_portfolio_performance()

total_val  = float(alloc["Value_INR"].sum()) if not alloc.empty and "Value_INR" in alloc.columns else 0
avg_sharpe = float(risk["Sharpe_Ratio"].mean()) if not risk.empty and "Sharpe_Ratio" in risk.columns else 0
best_t     = str(risk.nlargest(1,"Sharpe_Ratio")["Ticker"].values[0]).replace(".NS","") if not risk.empty else "N/A"

c1,c2,c3,c4 = st.columns(4)
c1.metric("Portfolio Value",  "Rs" + "{:,.0f}".format(total_val))
c2.metric("Avg Sharpe Ratio", "{:.3f}".format(avg_sharpe))
c3.metric("Best Sharpe Stock", best_t)
c4.metric("Stocks in Portfolio", len(alloc))

st.markdown("---")
cl, cr = st.columns(2)
with cl:
    st.subheader("Portfolio Allocation")
    if not alloc.empty and "Value_INR" in alloc.columns:
        name_col = "Company" if "Company" in alloc.columns else "Ticker"
        fig1 = px.pie(alloc,names=name_col,values="Value_INR",hole=0.3,title="Rs" + "{:,.0f}".format(total_val))
        fig1.update_traces(textposition="outside",textinfo="label+percent")
        st.plotly_chart(fig1, use_container_width=True)
        show_cols = [c for c in ["Company","Shares","Price","Value_INR","Weight_Pct"] if c in alloc.columns]
        st.dataframe(alloc[show_cols].sort_values("Value_INR",ascending=False) if "Value_INR" in alloc.columns else alloc[show_cols], use_container_width=True, hide_index=True)
with cr:
    st.subheader("Risk vs Return")
    if not risk.empty and "Ann_Volatility_Pct" in risk.columns:
        fig2 = px.scatter(risk,x="Ann_Volatility_Pct",y="Ann_Return_Pct",color="Sharpe_Ratio",
                          color_continuous_scale=["#D62728","#FFFFFF","#2CA02C"],hover_data=["Ticker"],
                          labels={"Ann_Volatility_Pct":"Volatility (%)","Ann_Return_Pct":"Return (%)"})
        fig2.add_vline(x=20,line_dash="dash",line_color="#D62728",annotation_text="High Risk")
        fig2.add_hline(y=0,line_dash="dash",line_color="black")
        fig2.update_layout(height=450,template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)

st.subheader("Sharpe Ratio by Stock")
if not risk.empty and "Sharpe_Ratio" in risk.columns:
    ss            = risk.sort_values("Sharpe_Ratio",ascending=True)
    bar_colors    = ["#2CA02C" if float(v)>=0 else "#D62728" for v in ss["Sharpe_Ratio"]]
    ticker_labels = [str(t).replace(".NS","") for t in ss["Ticker"]]
    fig3 = go.Figure(go.Bar(x=ss["Sharpe_Ratio"],y=ticker_labels,orientation="h",marker_color=bar_colors))
    fig3.add_vline(x=1.0,line_dash="dash",line_color="navy",annotation_text="Good Sharpe")
    fig3.add_vline(x=0,line_color="black",line_width=0.8)
    fig3.update_layout(height=600,template="plotly_white",xaxis_title="Sharpe Ratio")
    st.plotly_chart(fig3, use_container_width=True)

if not perf.empty:
    st.subheader("Portfolio Strategy Comparison")
    st.dataframe(perf, use_container_width=True, hide_index=True)
