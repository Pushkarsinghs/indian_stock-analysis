import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_sentiment, load_headlines

st.set_page_config(page_title="Sentiment Intelligence", page_icon="💬", layout="wide")
st.markdown('<style>[data-testid="stSidebar"]{background:#F0F2F5;}</style>', unsafe_allow_html=True)
st.markdown('<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);padding:20px;border-radius:10px;color:white;margin-bottom:20px;"><h2 style="margin:0">💬 Sentiment Intelligence - FinBERT NLP</h2><p style="margin:5px 0 0 0;opacity:0.85">ProsusAI/FinBERT - trained on Bloomberg and Reuters financial news</p></div>', unsafe_allow_html=True)

sent      = load_sentiment()
headlines = load_headlines()

if sent.empty:
    st.error("Sentiment data not found.")
    st.stop()

total_hl  = len(headlines) if not headlines.empty else 0
avg_conf  = float(headlines["Confidence"].mean()) if not headlines.empty and "Confidence" in headlines.columns else 0.0
most_bull = str(sent.nlargest(1,"Sentiment_Score")["Ticker"].values[0]).replace(".NS","") if "Sentiment_Score" in sent.columns else "N/A"
most_bear = str(sent.nsmallest(1,"Sentiment_Score")["Ticker"].values[0]).replace(".NS","") if "Sentiment_Score" in sent.columns else "N/A"

c1,c2,c3,c4 = st.columns(4)
c1.metric("Headlines Analyzed",     "{:,}".format(total_hl))
c2.metric("Avg FinBERT Confidence", "{:.3f}".format(avg_conf))
c3.metric("Most Bullish Stock",     most_bull)
c4.metric("Most Bearish Stock",     most_bear)

st.sidebar.header("Controls")
ticker_options = ["All Stocks"] + sorted(sent["Ticker"].unique().tolist())
ticker = st.sidebar.selectbox("Select Stock", ticker_options, index=0)

st.markdown("---")
cl, cr = st.columns(2)
with cl:
    st.subheader("FinBERT Sentiment Score")
    if "Sentiment_Score" in sent.columns:
        ss            = sent.sort_values("Sentiment_Score",ascending=True)
        bar_colors    = ["#1A7A1A" if float(s)>65 else "#2CA02C" if float(s)>55 else "#FF7F0E" if float(s)>45 else "#D62728" for s in ss["Sentiment_Score"]]
        ticker_labels = [str(t).replace(".NS","") for t in ss["Ticker"]]
        fig1 = go.Figure(go.Bar(x=ss["Sentiment_Score"],y=ticker_labels,orientation="h",marker_color=bar_colors,
                                text=["{:.1f}".format(float(s)) for s in ss["Sentiment_Score"]],textposition="outside"))
        fig1.add_vline(x=50,line_dash="dash",line_color="black",annotation_text="Neutral (50)")
        fig1.update_layout(height=700,template="plotly_white",xaxis_title="Sentiment Score (0-100)",xaxis_range=[0,100])
        st.plotly_chart(fig1, use_container_width=True)
with cr:
    st.subheader("Headline Distribution")
    if not headlines.empty and "Label" in headlines.columns:
        lc = headlines["Label"].value_counts().reset_index()
        lc.columns = ["Label","Count"]
        label_colors = {"positive":"#2CA02C","negative":"#D62728","neutral":"#AAAAAA"}
        fig2 = px.pie(lc,names="Label",values="Count",color="Label",color_discrete_map=label_colors,hole=0.5,
                      title="Total: "+str(total_hl)+" headlines")
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, use_container_width=True)
    st.subheader("FinBERT Confidence")
    if not headlines.empty and "Confidence" in headlines.columns:
        fig3 = px.histogram(headlines,x="Confidence",nbins=30,color_discrete_sequence=["#1F77B4"])
        fig3.add_vline(x=avg_conf,line_dash="dash",line_color="#D62728",annotation_text="Mean: "+"{:.3f}".format(avg_conf))
        fig3.update_layout(height=280,template="plotly_white")
        st.plotly_chart(fig3, use_container_width=True)

st.subheader("Headlines with FinBERT Scores")
if headlines.empty:
    st.info("No headlines available")
else:
    hl_display = headlines if ticker=="All Stocks" else headlines[headlines["Ticker"]==ticker]
    if not hl_display.empty:
        dc = [c for c in ["Ticker","Headline","Label","Confidence","Polarity"] if c in hl_display.columns]
        disp = hl_display[dc]
        if "Confidence" in disp.columns:
            disp = disp.sort_values("Confidence",ascending=False).head(50)
        st.dataframe(disp, use_container_width=True, hide_index=True)
    else:
        st.info("No headlines for "+str(ticker))
