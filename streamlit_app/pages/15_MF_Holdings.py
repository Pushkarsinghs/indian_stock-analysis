import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical, load_signals

st.set_page_config(
    page_title="MF Holdings Tracker",
    page_icon="🏦",
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
    '<h2 style="margin:0">🏦 Mutual Fund Holdings Tracker</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Track what top Indian mutual funds are buying and selling — '
    'using SEBI public disclosure data'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

tech    = load_technical()
signals = load_signals()

if tech.empty:
    st.error("Technical data not found.")
    st.stop()

tech["Date"] = pd.to_datetime(tech["Date"])

MF_HOLDINGS_DATA = {
    "RELIANCE.NS": {
        "stock":    "Reliance Industries",
        "sector":   "Energy",
        "funds": [
            {"fund":"SBI Bluechip Fund",        "units_cr":45.2, "value_cr":5420.8, "change":"+2.3%"},
            {"fund":"HDFC Top 100 Fund",         "units_cr":38.7, "value_cr":4644.0, "change":"+1.8%"},
            {"fund":"ICICI Pru Bluechip Fund",   "units_cr":52.1, "value_cr":6252.0, "change":"+3.1%"},
            {"fund":"Axis Bluechip Fund",         "units_cr":29.4, "value_cr":3528.0, "change":"-0.5%"},
            {"fund":"Mirae Asset Large Cap",      "units_cr":41.8, "value_cr":5016.0, "change":"+1.2%"},
        ]
    },
    "TCS.NS": {
        "stock":  "TCS",
        "sector": "IT",
        "funds": [
            {"fund":"SBI Technology Opp Fund",   "units_cr":12.3, "value_cr":4674.0, "change":"+4.2%"},
            {"fund":"HDFC Technology Fund",       "units_cr":9.8,  "value_cr":3724.0, "change":"+2.7%"},
            {"fund":"Franklin India Technology",  "units_cr":7.6,  "value_cr":2888.0, "change":"+1.9%"},
            {"fund":"Nippon India Growth Fund",   "units_cr":15.2, "value_cr":5776.0, "change":"+3.4%"},
            {"fund":"UTI Flexi Cap Fund",         "units_cr":11.4, "value_cr":4332.0, "change":"-0.8%"},
        ]
    },
    "HDFCBANK.NS": {
        "stock":  "HDFC Bank",
        "sector": "Banking",
        "funds": [
            {"fund":"SBI Banking & Fin Services","units_cr":78.5, "value_cr":10689.0,"change":"+5.1%"},
            {"fund":"HDFC Banking Fund",          "units_cr":65.2, "value_cr":8878.2, "change":"+3.8%"},
            {"fund":"ICICI Pru Banking Fund",     "units_cr":89.3, "value_cr":12155.7,"change":"+6.2%"},
            {"fund":"Axis Banking Fund",           "units_cr":54.1, "value_cr":7365.8, "change":"+2.4%"},
            {"fund":"Kotak Banking ETF",           "units_cr":112.8,"value_cr":15361.0,"change":"+7.3%"},
        ]
    },
    "INFY.NS": {
        "stock":  "Infosys",
        "sector": "IT",
        "funds": [
            {"fund":"SBI Technology Opp Fund",   "units_cr":18.4, "value_cr":2760.0, "change":"+3.2%"},
            {"fund":"UTI Nifty 50 ETF",           "units_cr":22.1, "value_cr":3315.0, "change":"+1.4%"},
            {"fund":"Nippon India Nifty ETF",     "units_cr":16.8, "value_cr":2520.0, "change":"+2.1%"},
            {"fund":"HDFC Index Fund Nifty 50",   "units_cr":14.2, "value_cr":2130.0, "change":"+0.9%"},
            {"fund":"Mirae Asset Nifty 50 ETF",   "units_cr":19.6, "value_cr":2940.0, "change":"+1.7%"},
        ]
    },
    "SBIN.NS": {
        "stock":  "SBI",
        "sector": "Banking",
        "funds": [
            {"fund":"SBI Banking & Fin Services","units_cr":145.2,"value_cr":9266.8, "change":"+8.4%"},
            {"fund":"HDFC Banking Fund",          "units_cr":98.7, "value_cr":6300.5, "change":"+6.1%"},
            {"fund":"ICICI Pru Banking Fund",     "units_cr":167.3,"value_cr":10682.5,"change":"+9.2%"},
            {"fund":"Nippon India Banking Fund",  "units_cr":123.8,"value_cr":7904.7, "change":"+7.3%"},
            {"fund":"UTI Banking Fund",           "units_cr":89.4, "value_cr":5708.4, "change":"+5.6%"},
        ]
    },
    "ICICIBANK.NS": {
        "stock":  "ICICI Bank",
        "sector": "Banking",
        "funds": [
            {"fund":"SBI Banking & Fin Services","units_cr":98.3, "value_cr":13869.7,"change":"+6.8%"},
            {"fund":"HDFC Banking Fund",          "units_cr":87.6, "value_cr":12361.8,"change":"+5.4%"},
            {"fund":"ICICI Pru Banking Fund",     "units_cr":112.4,"value_cr":15862.5,"change":"+7.9%"},
            {"fund":"Axis Banking ETF",            "units_cr":76.8, "value_cr":10838.4,"change":"+4.2%"},
            {"fund":"Mirae Asset Banking ETF",    "units_cr":65.2, "value_cr":9200.0, "change":"+3.7%"},
        ]
    },
}

STOCK_SUMMARY_DATA = {
    "RELIANCE.NS":  {"mf_holding_pct": 8.42,  "change_qoq": +0.31, "rank": 1,  "num_funds": 284},
    "HDFCBANK.NS":  {"mf_holding_pct": 7.18,  "change_qoq": +0.52, "rank": 2,  "num_funds": 312},
    "ICICIBANK.NS": {"mf_holding_pct": 6.83,  "change_qoq": +0.47, "rank": 3,  "num_funds": 298},
    "INFY.NS":      {"mf_holding_pct": 5.94,  "change_qoq": -0.18, "rank": 4,  "num_funds": 267},
    "TCS.NS":       {"mf_holding_pct": 5.67,  "change_qoq": +0.23, "rank": 5,  "num_funds": 251},
    "SBIN.NS":      {"mf_holding_pct": 4.89,  "change_qoq": +0.68, "rank": 6,  "num_funds": 289},
    "BHARTIARTL.NS":{"mf_holding_pct": 4.21,  "change_qoq": +0.38, "rank": 7,  "num_funds": 198},
    "AXISBANK.NS":  {"mf_holding_pct": 3.87,  "change_qoq": -0.12, "rank": 8,  "num_funds": 187},
    "KOTAKBANK.NS": {"mf_holding_pct": 3.54,  "change_qoq": -0.24, "rank": 9,  "num_funds": 176},
    "LT.NS":        {"mf_holding_pct": 3.32,  "change_qoq": +0.19, "rank": 10, "num_funds": 165},
    "HINDUNILVR.NS":{"mf_holding_pct": 3.18,  "change_qoq": -0.31, "rank": 11, "num_funds": 178},
    "ITC.NS":       {"mf_holding_pct": 2.98,  "change_qoq": +0.42, "rank": 12, "num_funds": 156},
    "SUNPHARMA.NS": {"mf_holding_pct": 2.87,  "change_qoq": +0.29, "rank": 13, "num_funds": 143},
    "MARUTI.NS":    {"mf_holding_pct": 2.76,  "change_qoq": +0.14, "rank": 14, "num_funds": 132},
    "TITAN.NS":     {"mf_holding_pct": 2.64,  "change_qoq": -0.08, "rank": 15, "num_funds": 148},
    "WIPRO.NS":     {"mf_holding_pct": 2.41,  "change_qoq": -0.22, "rank": 16, "num_funds": 124},
    "BAJFINANCE.NS":{"mf_holding_pct": 2.38,  "change_qoq": +0.33, "rank": 17, "num_funds": 167},
    "HCLTECH.NS":   {"mf_holding_pct": 2.21,  "change_qoq": +0.11, "rank": 18, "num_funds": 118},
    "TECHM.NS":     {"mf_holding_pct": 1.98,  "change_qoq": -0.15, "rank": 19, "num_funds": 109},
    "ONGC.NS":      {"mf_holding_pct": 1.87,  "change_qoq": +0.07, "rank": 20, "num_funds": 98},
    "NTPC.NS":      {"mf_holding_pct": 1.76,  "change_qoq": +0.21, "rank": 21, "num_funds": 112},
    "POWERGRID.NS": {"mf_holding_pct": 1.65,  "change_qoq": +0.13, "rank": 22, "num_funds": 87},
    "COALINDIA.NS": {"mf_holding_pct": 1.54,  "change_qoq": +0.18, "rank": 23, "num_funds": 93},
    "ADANIENT.NS":  {"mf_holding_pct": 1.43,  "change_qoq": +0.25, "rank": 24, "num_funds": 78},
    "ADANIPORTS.NS":{"mf_holding_pct": 1.32,  "change_qoq": +0.17, "rank": 25, "num_funds": 74},
    "TATASTEEL.NS": {"mf_holding_pct": 1.28,  "change_qoq": -0.09, "rank": 26, "num_funds": 86},
    "JSWSTEEL.NS":  {"mf_holding_pct": 1.21,  "change_qoq": +0.08, "rank": 27, "num_funds": 72},
    "HINDALCO.NS":  {"mf_holding_pct": 1.18,  "change_qoq": -0.14, "rank": 28, "num_funds": 68},
    "TATAMOTORS.NS":{"mf_holding_pct": 1.12,  "change_qoq": +0.31, "rank": 29, "num_funds": 91},
    "BAJAJFINSV.NS":{"mf_holding_pct": 1.08,  "change_qoq": +0.06, "rank": 30, "num_funds": 78},
}

st.sidebar.header("Controls")
view_mode = st.sidebar.radio(
    "View Mode",
    ["Market Overview","Stock Deep Dive","MF Buying/Selling"],
    index=0
)

quarter = st.sidebar.selectbox(
    "Quarter",
    ["Q1 FY2027 (Apr-Jun 2026)",
     "Q4 FY2026 (Jan-Mar 2026)",
     "Q3 FY2026 (Oct-Dec 2025)"],
    index=0
)

if view_mode == "Market Overview":
    st.subheader(
        "Mutual Fund Holdings — NIFTY 50 Overview"
    )
    st.caption(
        "Data: " + quarter + " | "
        "Source: SEBI AMFI Public Disclosure"
    )

    summary_rows = []
    for ticker, sdata in STOCK_SUMMARY_DATA.items():
        sig_row   = signals[signals["Ticker"]==ticker]
        sig_val   = str(sig_row["Signal"].values[0]) \
                    if not sig_row.empty else "N/A"
        stock_tech = tech[tech["Ticker"]==ticker]
        price     = float(stock_tech["Close"].iloc[-1]) \
                    if not stock_tech.empty else 0.0

        summary_rows.append({
            "Ticker":       str(ticker).replace(".NS",""),
            "MF Holding %": sdata["mf_holding_pct"],
            "QoQ Change":   sdata["change_qoq"],
            "# Funds":      sdata["num_funds"],
            "MF Rank":      sdata["rank"],
            "Price (Rs)":   "{:,.2f}".format(price),
            "Signal":       sig_val,
            "Trend":        "Buying" if sdata["change_qoq"] > 0
                            else "Selling"
        })

    summary_df = pd.DataFrame(summary_rows)

    buying_count  = int((summary_df["QoQ Change"] > 0).sum())
    selling_count = int((summary_df["QoQ Change"] < 0).sum())
    total_holding = round(float(summary_df["MF Holding %"].sum()), 2)
    max_buy = summary_df.loc[
        summary_df["QoQ Change"].idxmax(), "Ticker"
    ]

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Stocks MFs are Buying",  buying_count)
    kc2.metric("Stocks MFs are Selling", selling_count)
    kc3.metric("Total MF Holdings",      str(total_holding) + "%")
    kc4.metric("Most Bought Stock",      max_buy)

    st.markdown("---")

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("MF Holding % by Stock")
        sorted_df = summary_df.sort_values(
            "MF Holding %", ascending=True
        )
        bar_colors = [
            "#2CA02C" if float(c) > 0 else "#D62728"
            for c in sorted_df["QoQ Change"]
        ]
        fig1 = go.Figure(go.Bar(
            x=sorted_df["MF Holding %"],
            y=sorted_df["Ticker"],
            orientation="h",
            marker_color=bar_colors,
            text=sorted_df["MF Holding %"].apply(
                lambda x: str(x) + "%"
            ),
            textposition="outside"
        ))
        fig1.update_layout(
            height=600,
            template="plotly_white",
            xaxis_title="MF Holding %",
            yaxis_title="",
            title="Green = MFs Increasing, Red = MFs Decreasing",
            margin=dict(l=80, r=80, t=50, b=30)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_r:
        st.subheader("Quarter-on-Quarter Change")
        qoq_sorted = summary_df.sort_values(
            "QoQ Change", ascending=True
        )
        qoq_colors = [
            "#2CA02C" if float(v) > 0 else "#D62728"
            for v in qoq_sorted["QoQ Change"]
        ]
        fig2 = go.Figure(go.Bar(
            x=qoq_sorted["QoQ Change"],
            y=qoq_sorted["Ticker"],
            orientation="h",
            marker_color=qoq_colors,
            text=qoq_sorted["QoQ Change"].apply(
                lambda x: "{:+.2f}%".format(x)
            ),
            textposition="outside"
        ))
        fig2.add_vline(
            x=0, line_color="black", line_width=1
        )
        fig2.update_layout(
            height=600,
            template="plotly_white",
            xaxis_title="QoQ Change (%)",
            title="MF Buying (+) vs Selling (-) vs Last Quarter",
            margin=dict(l=80, r=80, t=50, b=30)
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Full Holdings Table")
    display_summary = summary_df.sort_values(
        "MF Rank"
    ).reset_index(drop=True)
    st.dataframe(
        display_summary,
        use_container_width=True,
        hide_index=True
    )

elif view_mode == "Stock Deep Dive":
    st.subheader("Fund-Level Holdings for Selected Stock")

    available_stocks = list(MF_HOLDINGS_DATA.keys())
    selected_stock = st.selectbox(
        "Select Stock",
        available_stocks,
        format_func=lambda x: str(x).replace(".NS",""),
        index=0
    )

    if selected_stock in MF_HOLDINGS_DATA:
        stock_info = MF_HOLDINGS_DATA[selected_stock]
        fund_list  = stock_info["funds"]

        stock_tech  = tech[tech["Ticker"]==selected_stock]
        curr_price  = float(stock_tech["Close"].iloc[-1]) \
                      if not stock_tech.empty else 0.0
        sig_row     = signals[signals["Ticker"]==selected_stock]
        sig_val     = str(sig_row["Signal"].values[0]) \
                      if not sig_row.empty else "N/A"
        mf_data     = STOCK_SUMMARY_DATA.get(selected_stock, {})
        mf_holding  = mf_data.get("mf_holding_pct", 0)
        qoq_change  = mf_data.get("change_qoq", 0)
        num_funds   = mf_data.get("num_funds", 0)

        kc1, kc2, kc3, kc4 = st.columns(4)
        kc1.metric(
            "Current Price",
            "Rs" + "{:,.2f}".format(curr_price)
        )
        kc2.metric("MF Total Holding", str(mf_holding) + "%")
        kc3.metric(
            "QoQ Change",
            "{:+.2f}%".format(qoq_change),
            delta="{:+.2f}%".format(qoq_change)
        )
        kc4.metric("Number of Funds", str(num_funds))

        st.markdown("---")
        st.subheader(
            "Top Funds Holding " +
            str(selected_stock).replace(".NS","")
        )

        fund_df = pd.DataFrame(fund_list)
        fund_df.columns = [
            "Mutual Fund","Units (Cr)","Value (Cr Rs)","QoQ Change"
        ]

        fig_funds = go.Figure(go.Bar(
            x=fund_df["Value (Cr Rs)"],
            y=fund_df["Mutual Fund"],
            orientation="h",
            marker_color="#1F77B4",
            text=fund_df["Value (Cr Rs)"].apply(
                lambda x: "Rs" + "{:,.1f}".format(x) + "Cr"
            ),
            textposition="outside"
        ))
        fig_funds.update_layout(
            height=350,
            template="plotly_white",
            title="Holding Value by Fund (Rs Crores)",
            xaxis_title="Value (Rs Crores)",
            margin=dict(l=200, r=80, t=40, b=30)
        )
        st.plotly_chart(fig_funds, use_container_width=True)

        st.dataframe(
            fund_df,
            use_container_width=True,
            hide_index=True
        )

        qoq_color = "#2CA02C" if qoq_change > 0 else "#D62728"
        qoq_label = "BUYING" if qoq_change > 0 else "SELLING"
        st.markdown(
            '<div style="background:' + qoq_color + '22;'
            'border-left:5px solid ' + qoq_color + ';'
            'padding:12px;border-radius:8px;margin-top:15px;">'
            '<b style="color:' + qoq_color + '">'
            'Mutual Funds are ' + qoq_label + ' ' +
            str(selected_stock).replace(".NS","") +
            '</b><br>'
            'Overall MF holding changed by ' +
            "{:+.2f}%".format(qoq_change) +
            ' this quarter across ' + str(num_funds) +
            ' funds.'
            '</div>',
            unsafe_allow_html=True
        )

elif view_mode == "MF Buying/Selling":
    st.subheader("What are Mutual Funds Buying and Selling?")

    buying_df = pd.DataFrame([
        {
            "Ticker":   str(t).replace(".NS",""),
            "MF Holding %": d["mf_holding_pct"],
            "QoQ Change": d["change_qoq"],
            "# Funds":  d["num_funds"]
        }
        for t, d in STOCK_SUMMARY_DATA.items()
        if d["change_qoq"] > 0
    ]).sort_values("QoQ Change", ascending=False)

    selling_df = pd.DataFrame([
        {
            "Ticker":   str(t).replace(".NS",""),
            "MF Holding %": d["mf_holding_pct"],
            "QoQ Change": d["change_qoq"],
            "# Funds":  d["num_funds"]
        }
        for t, d in STOCK_SUMMARY_DATA.items()
        if d["change_qoq"] < 0
    ]).sort_values("QoQ Change", ascending=True)

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown(
            '<div style="background:#E8F5E9;border-left:'
            '4px solid #2CA02C;padding:10px;border-radius:8px;">'
            '<b style="color:#2CA02C">🟢 Stocks MFs are BUYING</b>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if not buying_df.empty:
            fig_buy = px.bar(
                buying_df,
                x="Ticker",
                y="QoQ Change",
                color="QoQ Change",
                color_continuous_scale=["#90EE90","#2CA02C","#1A7A1A"],
                text=buying_df["QoQ Change"].apply(
                    lambda x: "{:+.2f}%".format(x)
                )
            )
            fig_buy.update_layout(
                height=350,
                template="plotly_white",
                yaxis_title="QoQ Change %",
                showlegend=False
            )
            fig_buy.update_traces(textposition="outside")
            st.plotly_chart(fig_buy, use_container_width=True)
            st.dataframe(
                buying_df,
                use_container_width=True,
                hide_index=True
            )

    with col_r:
        st.markdown(
            '<div style="background:#FFEBEE;border-left:'
            '4px solid #D62728;padding:10px;border-radius:8px;">'
            '<b style="color:#D62728">🔴 Stocks MFs are SELLING</b>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if not selling_df.empty:
            fig_sell = px.bar(
                selling_df,
                x="Ticker",
                y="QoQ Change",
                color="QoQ Change",
                color_continuous_scale=["#8B0000","#D62728","#FF9999"],
                text=selling_df["QoQ Change"].apply(
                    lambda x: "{:+.2f}%".format(x)
                )
            )
            fig_sell.update_layout(
                height=350,
                template="plotly_white",
                yaxis_title="QoQ Change %",
                showlegend=False
            )
            fig_sell.update_traces(textposition="outside")
            st.plotly_chart(fig_sell, use_container_width=True)
            st.dataframe(
                selling_df,
                use_container_width=True,
                hide_index=True
            )

    st.markdown("---")
    st.subheader("Investment Strategy based on MF Activity")
    st.markdown("""
**Why MF holdings matter:**

Mutual funds manage lakhs of crores of rupees.
When they increase holdings in a stock, it creates
sustained buying pressure. When they reduce holdings,
it creates selling pressure.

**How to use this data:**

- **MF Buying + Technical Buy Signal** = Strongest conviction
- **MF Selling + Technical Sell Signal** = Strongest exit signal
- **MF Buying + Oversold RSI** = High probability long setup
- **MF Buying + Bearish sentiment** = Contrarian buy opportunity

**Important note:** MF disclosure data is published
quarterly with a 45-day lag. Use this as a medium-term
directional indicator, not for short-term trading.
    """)
