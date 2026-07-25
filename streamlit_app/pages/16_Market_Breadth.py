import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical, load_signals, load_risk_metrics

st.set_page_config(
    page_title="Market Breadth",
    page_icon="📡",
    layout="wide"
)

st.markdown(
    '<style>'
    '[data-testid="stSidebar"]{background:#F0F2F5;}'
    '.block-container{padding-top:1rem;}'
    '</style>',
    unsafe_allow_html=True
)

st.markdown(
    '<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);'
    'padding:20px;border-radius:10px;color:white;margin-bottom:20px;">'
    '<h2 style="margin:0">📡 Market Breadth Dashboard</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    '52-Week Highs/Lows · Advance/Decline Ratio · '
    'RSI Distribution · Trend Strength'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

tech    = load_technical()
signals = load_signals()
risk    = load_risk_metrics()

if tech.empty:
    st.error("Technical data not found.")
    st.stop()

tech["Date"] = pd.to_datetime(tech["Date"])
max_date     = tech["Date"].max()

latest_df = tech[tech["Date"] == max_date].copy()
if latest_df.empty:
    latest_df = tech.groupby("Ticker").last().reset_index()

merged = latest_df.merge(
    signals[["Ticker","Signal","Signal_Score"]],
    on="Ticker",
    how="left"
) if not signals.empty else latest_df.copy()

if "Signal" not in merged.columns:
    merged["Signal"] = "Neutral"
if "Signal_Score" not in merged.columns:
    merged["Signal_Score"] = 0

total_stocks = len(merged)

advancing = len(merged[
    merged["Daily_Return"].fillna(0) > 0
])
declining = len(merged[
    merged["Daily_Return"].fillna(0) < 0
])
unchanged = total_stocks - advancing - declining

adr = round(advancing / declining, 2) if declining > 0 else 99.0

bull_signals = len(merged[merged["Signal"].isin(
    ["Strong Buy","Buy","Weak Buy"]
)])
bear_signals = len(merged[merged["Signal"].isin(
    ["Strong Sell","Sell","Weak Sell"]
)])

rsi_vals = merged["RSI"].dropna()
above_70  = int((rsi_vals > 70).sum())
below_30  = int((rsi_vals < 30).sum())
neutral_rsi = len(rsi_vals) - above_70 - below_30

highs_52w = 0
lows_52w  = 0

for _, row in merged.iterrows():
    ticker      = row["Ticker"]
    stock_hist  = tech[tech["Ticker"]==ticker]
    if stock_hist.empty:
        continue
    close_52w   = stock_hist["Close"].tail(252)
    curr_close  = float(row["Close"])
    if len(close_52w) >= 5:
        h52 = float(close_52w.max())
        l52 = float(close_52w.min())
        if curr_close >= h52 * 0.98:
            highs_52w += 1
        if curr_close <= l52 * 1.02:
            lows_52w  += 1

if adr >= 2:
    market_health = "Very Bullish"
    health_color  = "#1A7A1A"
elif adr >= 1.5:
    market_health = "Bullish"
    health_color  = "#2CA02C"
elif adr >= 1:
    market_health = "Neutral"
    health_color  = "#FF7F0E"
elif adr >= 0.7:
    market_health = "Bearish"
    health_color  = "#D62728"
else:
    market_health = "Very Bearish"
    health_color  = "#8B0000"

st.markdown(
    '<div style="background:' + health_color + '22;'
    'border:3px solid ' + health_color + ';'
    'border-radius:10px;padding:15px;'
    'text-align:center;margin-bottom:20px;">'
    '<h2 style="color:' + health_color + ';margin:0">'
    'Market Health: ' + market_health + '</h2>'
    '<p style="color:' + health_color + ';margin:5px 0 0 0;">'
    'Advance/Decline Ratio: ' + str(adr) +
    ' | Data as of: ' + str(max_date.date()) +
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

kc1,kc2,kc3,kc4,kc5,kc6 = st.columns(6)
kc1.metric("Advancing",      str(advancing),
           delta=str(advancing - declining))
kc2.metric("Declining",      str(declining))
kc3.metric("A/D Ratio",      str(adr))
kc4.metric("52W Highs",      str(highs_52w))
kc5.metric("52W Lows",       str(lows_52w))
kc6.metric("Overbought RSI", str(above_70))

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Advance/Decline",
    "📈 52-Week Highs/Lows",
    "🌡️ RSI Heatmap",
    "💪 Sector Strength"
])

with tab1:
    st.subheader("Advance / Decline Analysis")

    col_l, col_r = st.columns(2)

    with col_l:
        fig_ad = go.Figure(go.Pie(
            labels=["Advancing","Declining","Unchanged"],
            values=[advancing, declining, unchanged],
            hole=0.55,
            marker_colors=["#2CA02C","#D62728","#AAAAAA"],
            textinfo="label+percent+value"
        ))
        fig_ad.update_layout(
            height=350,
            title="Today's Market Breadth",
            legend=dict(orientation="h")
        )
        st.plotly_chart(fig_ad, use_container_width=True)

    with col_r:
        fig_sig = go.Figure(go.Bar(
            x=["Strong Buy","Buy","Weak Buy",
               "Neutral",
               "Weak Sell","Sell","Strong Sell"],
            y=[
                len(merged[merged["Signal"]=="Strong Buy"]),
                len(merged[merged["Signal"]=="Buy"]),
                len(merged[merged["Signal"]=="Weak Buy"]),
                len(merged[merged["Signal"]=="Neutral"]),
                len(merged[merged["Signal"]=="Weak Sell"]),
                len(merged[merged["Signal"]=="Sell"]),
                len(merged[merged["Signal"]=="Strong Sell"]),
            ],
            marker_color=[
                "#1A7A1A","#2CA02C","#90EE90",
                "#AAAAAA",
                "#FFB3B3","#D62728","#8B0000"
            ]
        ))
        fig_sig.update_layout(
            height=350,
            template="plotly_white",
            title="Signal Distribution Across All Stocks",
            yaxis_title="Number of Stocks",
            xaxis_tickangle=-15
        )
        st.plotly_chart(fig_sig, use_container_width=True)

    adv_stocks = merged[
        merged["Daily_Return"].fillna(0) > 0
    ].sort_values("Daily_Return", ascending=False)
    dec_stocks = merged[
        merged["Daily_Return"].fillna(0) < 0
    ].sort_values("Daily_Return", ascending=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Top Advancing Stocks")
        if not adv_stocks.empty:
            disp = adv_stocks.head(10)[[
                "Ticker","Close","Daily_Return","Signal"
            ]].copy()
            disp["Daily_Return"] = (
                disp["Daily_Return"]*100
            ).round(2).astype(str)+"%"
            disp["Ticker"] = disp["Ticker"].str.replace(".NS","")
            disp.columns = ["Ticker","Price","Return %","Signal"]
            st.dataframe(
                disp, use_container_width=True, hide_index=True
            )

    with col_b:
        st.subheader("Top Declining Stocks")
        if not dec_stocks.empty:
            disp2 = dec_stocks.head(10)[[
                "Ticker","Close","Daily_Return","Signal"
            ]].copy()
            disp2["Daily_Return"] = (
                disp2["Daily_Return"]*100
            ).round(2).astype(str)+"%"
            disp2["Ticker"] = disp2["Ticker"].str.replace(".NS","")
            disp2.columns = ["Ticker","Price","Return %","Signal"]
            st.dataframe(
                disp2, use_container_width=True, hide_index=True
            )

with tab2:
    st.subheader("52-Week Highs and Lows")

    highs_list = []
    lows_list  = []

    for _, row in merged.iterrows():
        ticker     = row["Ticker"]
        stock_hist = tech[tech["Ticker"]==ticker]
        if stock_hist.empty:
            continue
        close_52w  = stock_hist["Close"].tail(252)
        curr_close = float(row["Close"])
        if len(close_52w) < 5:
            continue
        h52 = float(close_52w.max())
        l52 = float(close_52w.min())
        dist_from_high = round((curr_close-h52)/h52*100, 2)
        dist_from_low  = round((curr_close-l52)/l52*100, 2)

        if curr_close >= h52 * 0.98:
            highs_list.append({
                "Ticker":     str(ticker).replace(".NS",""),
                "Price":      "{:,.2f}".format(curr_close),
                "52W High":   "{:,.2f}".format(h52),
                "Dist High %":"{:+.2f}%".format(dist_from_high),
                "Signal":     str(row.get("Signal","N/A"))
            })
        if curr_close <= l52 * 1.02:
            lows_list.append({
                "Ticker":    str(ticker).replace(".NS",""),
                "Price":     "{:,.2f}".format(curr_close),
                "52W Low":   "{:,.2f}".format(l52),
                "Dist Low %":"{:+.2f}%".format(dist_from_low),
                "Signal":    str(row.get("Signal","N/A"))
            })

    kh1, kh2 = st.columns(2)
    with kh1:
        st.markdown(
            '<div style="background:#E8F5E9;border-left:'
            '4px solid #2CA02C;padding:10px;border-radius:8px;">'
            '<b style="color:#2CA02C">📈 Near 52-Week High</b>'
            '</div>',
            unsafe_allow_html=True
        )
        if highs_list:
            st.dataframe(
                pd.DataFrame(highs_list),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No stocks near 52-week high today")

    with kh2:
        st.markdown(
            '<div style="background:#FFEBEE;border-left:'
            '4px solid #D62728;padding:10px;border-radius:8px;">'
            '<b style="color:#D62728">📉 Near 52-Week Low</b>'
            '</div>',
            unsafe_allow_html=True
        )
        if lows_list:
            st.dataframe(
                pd.DataFrame(lows_list),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No stocks near 52-week low today")

with tab3:
    st.subheader("RSI Heatmap — All 50 Stocks")

    rsi_data = []
    for _, row in merged.iterrows():
        rsi_v = float(row.get("RSI",50) or 50)
        rsi_data.append({
            "Ticker": str(row["Ticker"]).replace(".NS",""),
            "RSI":    round(rsi_v, 1),
            "Status": "Overbought" if rsi_v > 70 else
                      "Oversold"   if rsi_v < 30 else
                      "Neutral"
        })

    rsi_df = pd.DataFrame(rsi_data).sort_values(
        "RSI", ascending=False
    )

    fig_rsi = go.Figure(go.Bar(
        x=rsi_df["Ticker"],
        y=rsi_df["RSI"],
        marker_color=[
            "#8B0000" if r > 80 else
            "#D62728" if r > 70 else
            "#FF7F0E" if r > 60 else
            "#2CA02C" if r > 40 else
            "#1F77B4" if r > 30 else
            "#9467BD"
            for r in rsi_df["RSI"]
        ],
        text=rsi_df["RSI"].astype(str),
        textposition="outside",
        textfont=dict(size=8)
    ))
    fig_rsi.add_hline(
        y=70, line_dash="dash",
        line_color="#D62728",
        annotation_text="Overbought (70)"
    )
    fig_rsi.add_hline(
        y=30, line_dash="dash",
        line_color="#2CA02C",
        annotation_text="Oversold (30)"
    )
    fig_rsi.update_layout(
        height=500,
        template="plotly_white",
        title="RSI Values — All NIFTY 50 Stocks",
        yaxis_title="RSI Value",
        yaxis_range=[0, 115],
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_rsi, use_container_width=True)

    col_ob, col_os, col_nt = st.columns(3)
    with col_ob:
        st.metric(
            "Overbought (>70)",
            str(above_70) + " stocks",
            help="Potential sell candidates"
        )
    with col_os:
        st.metric(
            "Oversold (<30)",
            str(below_30) + " stocks",
            help="Potential buy candidates"
        )
    with col_nt:
        st.metric("Neutral (30-70)", str(neutral_rsi) + " stocks")

with tab4:
    st.subheader("Sector Strength Index")

    SECTOR_MAP = {
        "RELIANCE.NS":"Energy","TCS.NS":"IT",
        "HDFCBANK.NS":"Banking","INFY.NS":"IT",
        "ICICIBANK.NS":"Banking","HINDUNILVR.NS":"FMCG",
        "ITC.NS":"FMCG","SBIN.NS":"Banking",
        "BHARTIARTL.NS":"Telecom","KOTAKBANK.NS":"Banking",
        "LT.NS":"Infrastructure","AXISBANK.NS":"Banking",
        "ASIANPAINT.NS":"Paints","MARUTI.NS":"Auto",
        "SUNPHARMA.NS":"Pharma","TITAN.NS":"Consumer",
        "ULTRACEMCO.NS":"Cement","BAJFINANCE.NS":"NBFC",
        "WIPRO.NS":"IT","ONGC.NS":"Energy",
        "NTPC.NS":"Power","POWERGRID.NS":"Power",
        "TECHM.NS":"IT","HCLTECH.NS":"IT",
        "JSWSTEEL.NS":"Steel","TATASTEEL.NS":"Steel",
        "TATAMOTORS.NS":"Auto","NESTLEIND.NS":"FMCG",
        "DRREDDY.NS":"Pharma","DIVISLAB.NS":"Pharma",
        "CIPLA.NS":"Pharma","COALINDIA.NS":"Mining",
        "BPCL.NS":"Energy","GRASIM.NS":"Cement",
        "ADANIENT.NS":"Conglomerate","ADANIPORTS.NS":"Ports",
        "BAJAJFINSV.NS":"NBFC","BAJAJ-AUTO.NS":"Auto",
        "HEROMOTOCO.NS":"Auto","EICHERMOT.NS":"Auto",
        "BRITANNIA.NS":"FMCG","HINDALCO.NS":"Metals",
        "UPL.NS":"Agrochemicals","SBILIFE.NS":"Insurance",
        "HDFCLIFE.NS":"Insurance","APOLLOHOSP.NS":"Healthcare",
        "TATACONSUM.NS":"FMCG","INDUSINDBK.NS":"Banking",
        "M&M.NS":"Auto","LTF.NS":"NBFC"
    }

    merged["Sector"] = merged["Ticker"].map(SECTOR_MAP)

    sector_stats = merged.groupby("Sector").agg(
        Avg_Return    = ("Daily_Return", "mean"),
        Avg_RSI       = ("RSI",          "mean"),
        Num_Stocks    = ("Ticker",        "count"),
        Bull_Signals  = ("Signal",
                         lambda x: (
                             x.isin(["Strong Buy","Buy"])
                         ).sum()),
        Bear_Signals  = ("Signal",
                         lambda x: (
                             x.isin(["Strong Sell","Sell"])
                         ).sum())
    ).reset_index()

    sector_stats["Sector_Score"] = (
        sector_stats["Avg_Return"]  * 1000 * 40 +
        (sector_stats["Avg_RSI"] - 50) * 0.5  +
        sector_stats["Bull_Signals"] * 10 -
        sector_stats["Bear_Signals"] * 10
    ).round(2)

    sector_stats = sector_stats.sort_values(
        "Sector_Score", ascending=True
    )

    sec_colors = [
        "#1A7A1A" if float(s) > 20 else
        "#2CA02C" if float(s) > 5  else
        "#FF7F0E" if float(s) > -5 else
        "#D62728"
        for s in sector_stats["Sector_Score"]
    ]

    fig_sec = go.Figure(go.Bar(
        x=sector_stats["Sector_Score"],
        y=sector_stats["Sector"],
        orientation="h",
        marker_color=sec_colors,
        text=sector_stats["Sector_Score"].apply(
            lambda x: "{:+.1f}".format(x)
        ),
        textposition="outside"
    ))
    fig_sec.add_vline(
        x=0, line_color="black", line_width=1
    )
    fig_sec.update_layout(
        height=500,
        template="plotly_white",
        title="Sector Strength Score (Higher = Stronger Today)",
        xaxis_title="Composite Score",
        margin=dict(l=120, r=80, t=50, b=30)
    )
    st.plotly_chart(fig_sec, use_container_width=True)

    st.dataframe(
        sector_stats.sort_values(
            "Sector_Score", ascending=False
        ).rename(columns={
            "Avg_Return":   "Avg Daily Return",
            "Avg_RSI":      "Avg RSI",
            "Num_Stocks":   "# Stocks",
            "Bull_Signals": "Buy Signals",
            "Bear_Signals": "Sell Signals",
            "Sector_Score": "Strength Score"
        }),
        use_container_width=True,
        hide_index=True
    )
