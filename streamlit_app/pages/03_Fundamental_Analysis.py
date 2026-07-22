import streamlit as st
import pandas as pd
import plotly.express as px
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_fundamentals

st.set_page_config(page_title="Fundamental Analysis", page_icon="📊", layout="wide")
st.markdown('<style>[data-testid="stSidebar"]{background:#F0F2F5;}</style>', unsafe_allow_html=True)
st.markdown('<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);padding:20px;border-radius:10px;color:white;margin-bottom:20px;"><h2 style="margin:0">📊 Fundamental Analysis - Financial Health Scorecard</h2></div>', unsafe_allow_html=True)

fund = load_fundamentals()
if fund.empty:
    st.error("Fundamental data not found.")
    st.stop()

st.sidebar.header("Filters")
sectors = sorted(fund["Sector"].dropna().unique()) if "Sector" in fund.columns else []
sector_filter = st.sidebar.multiselect("Sector", sectors, default=[])
grade_filter  = st.sidebar.multiselect("Grade", ["A","B","C","D","F"], default=[])

filtered = fund.copy()
if sector_filter: filtered = filtered[filtered["Sector"].isin(sector_filter)]
if grade_filter and "Fund_Grade" in filtered.columns:
    filtered = filtered[filtered["Fund_Grade"].isin(grade_filter)]

c1,c2,c3,c4 = st.columns(4)
c1.metric("Stocks", len(filtered))
c2.metric("Grade A/B", len(filtered[filtered["Fund_Grade"].isin(["A","B"])]) if "Fund_Grade" in filtered.columns else 0)
c3.metric("Avg P/E", "{:.1f}x".format(float(filtered["PE_Ratio"].mean())) if "PE_Ratio" in filtered.columns and filtered["PE_Ratio"].notna().any() else "N/A")
c4.metric("Avg ROE", "{:.1f}%".format(float(filtered["ROE_Pct"].mean())) if "ROE_Pct" in filtered.columns and filtered["ROE_Pct"].notna().any() else "N/A")

st.markdown("---")
grade_colors = {"A":"#1A7A1A","B":"#2CA02C","C":"#FF7F0E","D":"#D62728","F":"#8B0000"}
cl, cr = st.columns(2)
with cl:
    st.subheader("Fundamental Score by Stock")
    if "Fund_Score" in filtered.columns:
        top20 = filtered.nlargest(20,"Fund_Score")
        fig1  = px.bar(top20.sort_values("Fund_Score"),x="Fund_Score",y="Ticker",
                       color="Fund_Grade" if "Fund_Grade" in top20.columns else None,
                       color_discrete_map=grade_colors,orientation="h")
        fig1.add_vline(x=50,line_dash="dash",line_color="gray")
        fig1.update_layout(height=500,template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)
with cr:
    st.subheader("ROE vs P/E Ratio")
    if "PE_Ratio" in filtered.columns and "ROE_Pct" in filtered.columns:
        valid = filtered.dropna(subset=["PE_Ratio","ROE_Pct"])
        valid = valid[valid["PE_Ratio"].between(0,80)]
        if not valid.empty:
            fig2 = px.scatter(valid,x="PE_Ratio",y="ROE_Pct",color="Sector" if "Sector" in valid.columns else None,hover_data=["Ticker"])
            fig2.add_vline(x=25,line_dash="dash",line_color="gray",annotation_text="Fair Value")
            fig2.add_hline(y=15,line_dash="dash",line_color="gray",annotation_text="Benchmark")
            fig2.update_layout(height=500,template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)

cl2, cr2 = st.columns(2)
with cl2:
    st.subheader("Grade Distribution")
    if "Fund_Grade" in filtered.columns:
        gc = filtered["Fund_Grade"].value_counts().reset_index()
        gc.columns = ["Grade","Count"]
        fig3 = px.pie(gc,names="Grade",values="Count",color="Grade",color_discrete_map=grade_colors,hole=0.5)
        st.plotly_chart(fig3, use_container_width=True)
with cr2:
    st.subheader("Sector Average ROE")
    if "Sector" in filtered.columns and "ROE_Pct" in filtered.columns:
        sr = filtered.groupby("Sector")["ROE_Pct"].mean().reset_index().sort_values("ROE_Pct")
        fig4 = px.bar(sr,x="ROE_Pct",y="Sector",orientation="h",color="ROE_Pct",color_continuous_scale=["#D62728","#FF7F0E","#2CA02C"])
        fig4.add_vline(x=15,line_dash="dash",line_color="navy",annotation_text="Benchmark")
        fig4.update_layout(height=400,template="plotly_white")
        st.plotly_chart(fig4, use_container_width=True)

st.subheader("Full Fundamental Scorecard")
display_cols = [c for c in ["Ticker","Company","Sector","PE_Ratio","PB_Ratio","ROE_Pct","Profit_Margin_Pct","Debt_To_Equity","Dividend_Yield_Pct","Fund_Score","Fund_Grade"] if c in filtered.columns]
disp = filtered[display_cols]
if "Fund_Score" in disp.columns:
    disp = disp.sort_values("Fund_Score",ascending=False)
st.dataframe(disp, use_container_width=True, hide_index=True)
