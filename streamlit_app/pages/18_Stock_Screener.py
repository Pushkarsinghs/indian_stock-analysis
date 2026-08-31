import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import (
    load_technical, load_signals, load_fundamentals,
    load_sentiment, load_risk_metrics
)

st.set_page_config(
    page_title="Stock Screener",
    page_icon="🔎",
    layout="wide"
)

st.markdown(
    "<style>"
    "[data-testid='stSidebar']{background:#F0F2F5;}"
    ".block-container{padding-top:1rem;}"
    "</style>",
    unsafe_allow_html=True
)

st.markdown(
    '<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);'
    'padding:20px;border-radius:10px;color:white;margin-bottom:20px;">'
    '<h2 style="margin:0">🔎 Custom Stock Screener</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Filter all 50 NIFTY stocks by any combination of '
    'technical · fundamental · sentiment · risk criteria'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

# ── Load all data ─────────────────────────────────────
tech = load_technical()
sigs = load_signals()
fund = load_fundamentals()
sent = load_sentiment()
risk = load_risk_metrics()

if tech.empty:
    st.error("Technical data not found.")
    st.stop()

tech["Date"] = pd.to_datetime(tech["Date"])

SECTOR_MAP = {
    "RELIANCE.NS":   "Energy",
    "TCS.NS":        "IT",
    "HDFCBANK.NS":   "Banking",
    "INFY.NS":       "IT",
    "ICICIBANK.NS":  "Banking",
    "HINDUNILVR.NS": "FMCG",
    "ITC.NS":        "FMCG",
    "SBIN.NS":       "Banking",
    "BHARTIARTL.NS": "Telecom",
    "KOTAKBANK.NS":  "Banking",
    "LT.NS":         "Infrastructure",
    "AXISBANK.NS":   "Banking",
    "ASIANPAINT.NS": "Paints",
    "MARUTI.NS":     "Auto",
    "SUNPHARMA.NS":  "Pharma",
    "TITAN.NS":      "Consumer",
    "ULTRACEMCO.NS": "Cement",
    "BAJFINANCE.NS": "NBFC",
    "WIPRO.NS":      "IT",
    "ONGC.NS":       "Energy",
    "NTPC.NS":       "Power",
    "POWERGRID.NS":  "Power",
    "TECHM.NS":      "IT",
    "HCLTECH.NS":    "IT",
    "JSWSTEEL.NS":   "Steel",
    "TATASTEEL.NS":  "Steel",
    "TATAMOTORS.NS": "Auto",
    "NESTLEIND.NS":  "FMCG",
    "DRREDDY.NS":    "Pharma",
    "DIVISLAB.NS":   "Pharma",
    "CIPLA.NS":      "Pharma",
    "COALINDIA.NS":  "Mining",
    "BPCL.NS":       "Energy",
    "GRASIM.NS":     "Cement",
    "ADANIENT.NS":   "Conglomerate",
    "ADANIPORTS.NS": "Ports",
    "BAJAJFINSV.NS": "NBFC",
    "BAJAJ-AUTO.NS": "Auto",
    "HEROMOTOCO.NS": "Auto",
    "EICHERMOT.NS":  "Auto",
    "BRITANNIA.NS":  "FMCG",
    "HINDALCO.NS":   "Metals",
    "UPL.NS":        "Agrochemicals",
    "SBILIFE.NS":    "Insurance",
    "HDFCLIFE.NS":   "Insurance",
    "APOLLOHOSP.NS": "Healthcare",
    "TATACONSUM.NS": "FMCG",
    "INDUSINDBK.NS": "Banking",
    "M&M.NS":        "Auto",
    "LTF.NS":        "NBFC",
}

# ── Build merged dataset ───────────────────────────────
latest = tech.groupby("Ticker").last().reset_index()
latest["Sector"] = latest["Ticker"].map(SECTOR_MAP)

merged = latest.copy()

if not sigs.empty:
    sig_cols = [
        c for c in ["Ticker", "Signal", "Signal_Score"]
        if c in sigs.columns
    ]
    merged = merged.merge(sigs[sig_cols], on="Ticker", how="left")

if not fund.empty:
    fund_cols = [
        c for c in [
            "Ticker", "PE_Ratio", "PB_Ratio", "ROE_Pct",
            "Debt_To_Equity", "Fund_Score", "Fund_Grade",
            "Dividend_Yield_Pct", "Profit_Margin_Pct"
        ] if c in fund.columns
    ]
    merged = merged.merge(fund[fund_cols], on="Ticker", how="left")

if not sent.empty:
    sent_cols = [
        c for c in [
            "Ticker", "Sentiment_Score",
            "Sentiment_Label", "Avg_Confidence"
        ] if c in sent.columns
    ]
    merged = merged.merge(sent[sent_cols], on="Ticker", how="left")

if not risk.empty:
    risk_cols = [
        c for c in [
            "Ticker", "Sharpe_Ratio", "Ann_Return_Pct",
            "Ann_Volatility_Pct", "Max_Drawdown_Pct", "Beta"
        ] if c in risk.columns
    ]
    merged = merged.merge(risk[risk_cols], on="Ticker", how="left")

# ── Preset screens ─────────────────────────────────────
PRESET_SCREENS = {
    "Custom (Set your own filters below)": {
        "description": "Build your own custom screen",
        "signal":       [],
        "grade":        [],
        "rsi_min":      0,
        "rsi_max":      100,
        "pe_max":       200.0,
        "roe_min":      0.0,
        "div_yield_min":0.0,
        "sentiment_min":0,
        "sharpe_min":   -5.0,
        "ann_ret_min":  -100.0,
    },
    "Quality Growth (Grade A/B + ROE > 20% + Buy)": {
        "description": "High-quality stocks with strong fundamentals",
        "signal":       ["Strong Buy", "Buy"],
        "grade":        ["A", "B"],
        "rsi_min":      0,
        "rsi_max":      100,
        "pe_max":       200.0,
        "roe_min":      20.0,
        "div_yield_min":0.0,
        "sentiment_min":0,
        "sharpe_min":   -5.0,
        "ann_ret_min":  -100.0,
    },
    "Deep Value (P/E < 15 + RSI < 45)": {
        "description": "Undervalued stocks at attractive prices",
        "signal":       [],
        "grade":        [],
        "rsi_min":      0,
        "rsi_max":      45,
        "pe_max":       15.0,
        "roe_min":      0.0,
        "div_yield_min":0.0,
        "sentiment_min":0,
        "sharpe_min":   -5.0,
        "ann_ret_min":  -100.0,
    },
    "Momentum (RSI 55-70 + Positive Sentiment)": {
        "description": "Stocks with strong price momentum",
        "signal":       [],
        "grade":        [],
        "rsi_min":      55,
        "rsi_max":      70,
        "pe_max":       200.0,
        "roe_min":      0.0,
        "div_yield_min":0.0,
        "sentiment_min":55,
        "sharpe_min":   -5.0,
        "ann_ret_min":  -100.0,
    },
    "Oversold Bounce (RSI < 35)": {
        "description": "Stocks that may have been oversold",
        "signal":       [],
        "grade":        [],
        "rsi_min":      0,
        "rsi_max":      35,
        "pe_max":       200.0,
        "roe_min":      0.0,
        "div_yield_min":0.0,
        "sentiment_min":0,
        "sharpe_min":   -5.0,
        "ann_ret_min":  -100.0,
    },
    "High Dividend (Yield > 2%)": {
        "description": "Income-generating stocks",
        "signal":       [],
        "grade":        [],
        "rsi_min":      0,
        "rsi_max":      100,
        "pe_max":       200.0,
        "roe_min":      0.0,
        "div_yield_min":2.0,
        "sentiment_min":0,
        "sharpe_min":   -5.0,
        "ann_ret_min":  -100.0,
    },
    "Best Risk-Adjusted (Sharpe > 1)": {
        "description": "Stocks with best risk-adjusted returns",
        "signal":       [],
        "grade":        [],
        "rsi_min":      0,
        "rsi_max":      100,
        "pe_max":       200.0,
        "roe_min":      0.0,
        "div_yield_min":0.0,
        "sentiment_min":0,
        "sharpe_min":   1.0,
        "ann_ret_min":  0.0,
    },
}

# ── Sidebar controls ───────────────────────────────────
st.sidebar.header("Screen Selection")
preset = st.sidebar.selectbox(
    "Choose a Preset or Custom",
    list(PRESET_SCREENS.keys()),
    index=0
)

p = PRESET_SCREENS[preset]

if preset != "Custom (Set your own filters below)":
    st.info("**" + preset + "** — " + p["description"])

st.sidebar.markdown("---")
st.sidebar.subheader("Technical Filters")

signal_filter = st.sidebar.multiselect(
    "Signal",
    ["Strong Buy", "Buy", "Weak Buy",
     "Neutral", "Weak Sell", "Sell", "Strong Sell"],
    default=p["signal"]
)

rsi_range = st.sidebar.slider(
    "RSI Range",
    min_value=0,
    max_value=100,
    value=(int(p["rsi_min"]), int(p["rsi_max"]))
)

st.sidebar.markdown("---")
st.sidebar.subheader("Fundamental Filters")

all_sectors = sorted(set(SECTOR_MAP.values()))
sector_filter = st.sidebar.multiselect(
    "Sectors", all_sectors, default=[]
)

grade_filter = st.sidebar.multiselect(
    "Fund Grade",
    ["A", "B", "C", "D", "F"],
    default=p["grade"]
)

pe_max = st.sidebar.slider(
    "Max P/E Ratio",
    min_value=0.0,
    max_value=200.0,
    value=float(p["pe_max"]),
    step=1.0
)

roe_min = st.sidebar.slider(
    "Min ROE %",
    min_value=0.0,
    max_value=60.0,
    value=float(p["roe_min"]),
    step=0.5
)

debt_eq_max = st.sidebar.slider(
    "Max Debt/Equity",
    min_value=0.0,
    max_value=100.0,
    value=50.0,
    step=0.5
)

div_yield_min = st.sidebar.slider(
    "Min Dividend Yield %",
    min_value=0.0,
    max_value=20.0,
    value=float(p["div_yield_min"]),
    step=0.1
)

st.sidebar.markdown("---")
st.sidebar.subheader("Sentiment Filters")

sent_min = st.sidebar.slider(
    "Min Sentiment Score",
    min_value=0,
    max_value=100,
    value=int(p["sentiment_min"])
)

st.sidebar.markdown("---")
st.sidebar.subheader("Risk Filters")

# ── KEY FIX: use sliders with safe min/max/value ──────
# All three (min_value, max_value, value) use slider
# so there is NO chance of value < min_value error
sharpe_min = st.sidebar.slider(
    "Min Sharpe Ratio",
    min_value=-5.0,
    max_value=5.0,
    value=float(p["sharpe_min"]),
    step=0.1
)

ann_ret_min = st.sidebar.slider(
    "Min Annual Return %",
    min_value=-100.0,
    max_value=200.0,
    value=float(p["ann_ret_min"]),
    step=1.0
)

# ── Apply all filters ──────────────────────────────────
filtered = merged.copy()

if signal_filter and "Signal" in filtered.columns:
    filtered = filtered[filtered["Signal"].isin(signal_filter)]

if "RSI" in filtered.columns:
    filtered = filtered[
        (filtered["RSI"].fillna(50) >= rsi_range[0]) &
        (filtered["RSI"].fillna(50) <= rsi_range[1])
    ]

if sector_filter and "Sector" in filtered.columns:
    filtered = filtered[filtered["Sector"].isin(sector_filter)]

if grade_filter and "Fund_Grade" in filtered.columns:
    filtered = filtered[filtered["Fund_Grade"].isin(grade_filter)]

if "PE_Ratio" in filtered.columns:
    filtered = filtered[
        filtered["PE_Ratio"].fillna(pe_max) <= pe_max
    ]

if "ROE_Pct" in filtered.columns:
    filtered = filtered[
        filtered["ROE_Pct"].fillna(0) >= roe_min
    ]

if "Debt_To_Equity" in filtered.columns:
    filtered = filtered[
        filtered["Debt_To_Equity"].fillna(0) <= debt_eq_max
    ]

if "Dividend_Yield_Pct" in filtered.columns:
    filtered = filtered[
        filtered["Dividend_Yield_Pct"].fillna(0) >= div_yield_min
    ]

if "Sentiment_Score" in filtered.columns:
    filtered = filtered[
        filtered["Sentiment_Score"].fillna(50) >= sent_min
    ]

if "Sharpe_Ratio" in filtered.columns:
    filtered = filtered[
        filtered["Sharpe_Ratio"].fillna(-5.0) >= sharpe_min
    ]

if "Ann_Return_Pct" in filtered.columns:
    filtered = filtered[
        filtered["Ann_Return_Pct"].fillna(-100) >= ann_ret_min
    ]

# ── KPI row ────────────────────────────────────────────
total   = len(merged)
matched = len(filtered)
pct     = round(matched / total * 100, 1) if total > 0 else 0

kc1, kc2, kc3, kc4 = st.columns(4)
kc1.metric("Total Stocks",   str(total))
kc2.metric("Stocks Matched", str(matched))
kc3.metric("Match Rate",     str(pct) + "%")
kc4.metric(
    "Screen Used",
    preset.split("(")[0].strip()[:25]
)

st.markdown("---")

# ── Results ────────────────────────────────────────────
if filtered.empty:
    st.warning(
        "No stocks match your current criteria. "
        "Try relaxing some filters using the sidebar sliders."
    )
else:
    st.subheader(
        "Screener Results — " + str(matched) + " Stocks Found"
    )

    priority_cols = [
        "Ticker", "Sector", "Close", "RSI", "Signal",
        "Fund_Grade", "Fund_Score", "PE_Ratio", "ROE_Pct",
        "Sentiment_Score", "Sharpe_Ratio", "Ann_Return_Pct"
    ]
    display_cols = [
        c for c in priority_cols if c in filtered.columns
    ]

    display_df = filtered[display_cols].copy()
    display_df["Ticker"] = display_df["Ticker"].str.replace(
        ".NS", "", regex=False
    )

    for col in [
        "PE_Ratio", "ROE_Pct", "Sharpe_Ratio",
        "Ann_Return_Pct", "Fund_Score", "Sentiment_Score"
    ]:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(2)

    if "RSI" in display_df.columns:
        display_df["RSI"] = display_df["RSI"].round(1)

    if "Close" in display_df.columns:
        display_df["Close"] = display_df["Close"].apply(
            lambda x: "{:,.2f}".format(float(x))
            if pd.notna(x) else "N/A"
        )

    sort_options = [
        c for c in [
            "Fund_Score", "ROE_Pct", "Sharpe_Ratio",
            "Ann_Return_Pct", "Sentiment_Score", "RSI"
        ] if c in display_df.columns
    ]

    if sort_options:
        sort_by = st.selectbox(
            "Sort results by", sort_options, index=0
        )
        display_df = display_df.sort_values(
            sort_by, ascending=False
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # ── Visual charts ──────────────────────────────────
    if len(filtered) > 1:
        st.markdown("---")
        st.subheader("Visual Analysis")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            if (
                "RSI" in filtered.columns and
                "Fund_Score" in filtered.columns
            ):
                sc_df = filtered.dropna(
                    subset=["RSI", "Fund_Score"]
                ).copy()
                sc_df["Label"] = sc_df[
                    "Ticker"
                ].str.replace(".NS", "", regex=False)

                if not sc_df.empty:
                    color_col = (
                        "Signal"
                        if "Signal" in sc_df.columns
                        else None
                    )
                    fig_sc = px.scatter(
                        sc_df,
                        x="RSI",
                        y="Fund_Score",
                        color=color_col,
                        text="Label",
                        title="RSI vs Fundamental Score",
                        color_discrete_map={
                            "Strong Buy":  "#1A7A1A",
                            "Buy":         "#2CA02C",
                            "Weak Buy":    "#90EE90",
                            "Neutral":     "#AAAAAA",
                            "Weak Sell":   "#FFB3B3",
                            "Sell":        "#D62728",
                            "Strong Sell": "#8B0000"
                        }
                    )
                    fig_sc.add_vline(
                        x=30, line_dash="dash",
                        line_color="#2CA02C",
                        annotation_text="Oversold"
                    )
                    fig_sc.add_vline(
                        x=70, line_dash="dash",
                        line_color="#D62728",
                        annotation_text="Overbought"
                    )
                    fig_sc.add_hline(
                        y=50, line_dash="dash",
                        line_color="gray",
                        annotation_text="Avg Score"
                    )
                    fig_sc.update_traces(
                        textposition="top center",
                        textfont_size=9
                    )
                    fig_sc.update_layout(
                        height=380,
                        template="plotly_white"
                    )
                    st.plotly_chart(
                        fig_sc, use_container_width=True
                    )

        with chart_col2:
            if "Sector" in filtered.columns:
                sc = filtered["Sector"].value_counts()
                if not sc.empty:
                    fig_pie = go.Figure(go.Pie(
                        labels=sc.index.tolist(),
                        values=sc.values.tolist(),
                        hole=0.4,
                        textinfo="label+percent+value"
                    ))
                    fig_pie.update_layout(
                        height=380,
                        title="Screened Stocks by Sector",
                        legend=dict(orientation="h")
                    )
                    st.plotly_chart(
                        fig_pie, use_container_width=True
                    )

st.markdown("---")
st.caption(
    "All filters use the latest available data. "
    "This screener is for educational purposes only. "
    "Always do your own research before investing."
)
