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
    '<style>'
    '[data-testid="stSidebar"]{background:#F0F2F5;}'
    '.block-container{padding-top:1rem;}'
    '</style>',
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

tech  = load_technical()
sigs  = load_signals()
fund  = load_fundamentals()
sent  = load_sentiment()
risk  = load_risk_metrics()

if tech.empty:
    st.error("Technical data not found.")
    st.stop()

tech["Date"] = pd.to_datetime(tech["Date"])

SECTOR_MAP = {
    "RELIANCE.NS":"Energy","TCS.NS":"IT","HDFCBANK.NS":"Banking",
    "INFY.NS":"IT","ICICIBANK.NS":"Banking","HINDUNILVR.NS":"FMCG",
    "ITC.NS":"FMCG","SBIN.NS":"Banking","BHARTIARTL.NS":"Telecom",
    "KOTAKBANK.NS":"Banking","LT.NS":"Infrastructure",
    "AXISBANK.NS":"Banking","ASIANPAINT.NS":"Paints",
    "MARUTI.NS":"Auto","SUNPHARMA.NS":"Pharma","TITAN.NS":"Consumer",
    "ULTRACEMCO.NS":"Cement","BAJFINANCE.NS":"NBFC","WIPRO.NS":"IT",
    "ONGC.NS":"Energy","NTPC.NS":"Power","POWERGRID.NS":"Power",
    "TECHM.NS":"IT","HCLTECH.NS":"IT","JSWSTEEL.NS":"Steel",
    "TATASTEEL.NS":"Steel","TATAMOTORS.NS":"Auto",
    "NESTLEIND.NS":"FMCG","DRREDDY.NS":"Pharma",
    "DIVISLAB.NS":"Pharma","CIPLA.NS":"Pharma",
    "COALINDIA.NS":"Mining","BPCL.NS":"Energy","GRASIM.NS":"Cement",
    "ADANIENT.NS":"Conglomerate","ADANIPORTS.NS":"Ports",
    "BAJAJFINSV.NS":"NBFC","BAJAJ-AUTO.NS":"Auto",
    "HEROMOTOCO.NS":"Auto","EICHERMOT.NS":"Auto",
    "BRITANNIA.NS":"FMCG","HINDALCO.NS":"Metals",
    "UPL.NS":"Agrochemicals","SBILIFE.NS":"Insurance",
    "HDFCLIFE.NS":"Insurance","APOLLOHOSP.NS":"Healthcare",
    "TATACONSUM.NS":"FMCG","INDUSINDBK.NS":"Banking",
    "M&M.NS":"Auto","LTF.NS":"NBFC"
}

latest = tech.groupby("Ticker").last().reset_index()
latest["Sector"] = latest["Ticker"].map(SECTOR_MAP)

merged = latest.copy()
if not sigs.empty:
    sig_cols = [c for c in ["Ticker","Signal","Signal_Score"]
                if c in sigs.columns]
    merged = merged.merge(sigs[sig_cols], on="Ticker", how="left")

if not fund.empty:
    fund_cols = [
        c for c in [
            "Ticker","PE_Ratio","PB_Ratio","ROE_Pct",
            "Debt_To_Equity","Fund_Score","Fund_Grade",
            "Dividend_Yield_Pct","Profit_Margin_Pct"
        ] if c in fund.columns
    ]
    merged = merged.merge(fund[fund_cols], on="Ticker", how="left")

if not sent.empty:
    sent_cols = [
        c for c in [
            "Ticker","Sentiment_Score","Sentiment_Label","Avg_Confidence"
        ] if c in sent.columns
    ]
    merged = merged.merge(sent[sent_cols], on="Ticker", how="left")

if not risk.empty:
    risk_cols = [
        c for c in [
            "Ticker","Sharpe_Ratio","Ann_Return_Pct",
            "Ann_Volatility_Pct","Max_Drawdown_Pct","Beta"
        ] if c in risk.columns
    ]
    merged = merged.merge(risk[risk_cols], on="Ticker", how="left")

PRESET_SCREENS = {
    "Quality Growth (Grade A/B + ROE > 20% + Buy Signal)": {
        "description": "High-quality stocks with strong fundamentals and bullish signals",
        "filters": {
            "signal":   ["Strong Buy","Buy"],
            "grade":    ["A","B"],
            "roe_min":  20.0
        }
    },
    "Deep Value (P/E < 15 + RSI < 45 + Grade B+)": {
        "description": "Undervalued stocks at attractive prices",
        "filters": {
            "pe_max":   15.0,
            "rsi_max":  45.0,
            "grade":    ["A","B"]
        }
    },
    "Momentum (RSI 55-70 + MACD Bullish + Positive Sentiment)": {
        "description": "Stocks with strong price momentum",
        "filters": {
            "rsi_min":      55.0,
            "rsi_max":      70.0,
            "sentiment_min":55.0
        }
    },
    "Oversold Bounce (RSI < 35 + Grade A/B/C)": {
        "description": "Quality stocks that may have been oversold",
        "filters": {
            "rsi_max":  35.0,
            "grade":    ["A","B","C"]
        }
    },
    "High Sharpe (Sharpe > 1 + Positive Annual Return)": {
        "description": "Best risk-adjusted return stocks",
        "filters": {
            "sharpe_min":    1.0,
            "ann_return_min":0.0
        }
    },
    "High Dividend (Yield > 2% + Low Debt)": {
        "description": "Income-generating stocks with healthy balance sheets",
        "filters": {
            "div_yield_min":  2.0,
            "debt_eq_max":    1.0
        }
    },
    "Custom (Set your own filters below)": {
        "description": "Build your own custom screen",
        "filters": {}
    }
}

st.sidebar.header("Screen Selection")
preset = st.sidebar.selectbox(
    "Choose a Preset Screen or Custom",
    list(PRESET_SCREENS.keys()),
    index=6
)

preset_data    = PRESET_SCREENS[preset]
preset_filters = preset_data["filters"]

if preset != "Custom (Set your own filters below)":
    st.info(
        "**" + preset + "**\n\n" +
        preset_data["description"]
    )

st.sidebar.markdown("---")
st.sidebar.subheader("Technical Filters")

signals_available = ["Strong Buy","Buy","Weak Buy",
                     "Neutral","Weak Sell","Sell","Strong Sell"]
sig_default = preset_filters.get("signal", [])
signal_filter = st.sidebar.multiselect(
    "Signal",
    signals_available,
    default=sig_default
)

rsi_range = st.sidebar.slider(
    "RSI Range",
    min_value=0, max_value=100,
    value=(
        int(preset_filters.get("rsi_min", 0)),
        int(preset_filters.get("rsi_max", 100))
    )
)

st.sidebar.markdown("---")
st.sidebar.subheader("Fundamental Filters")

all_sectors = sorted(set(SECTOR_MAP.values()))
sector_filter = st.sidebar.multiselect(
    "Sectors",
    all_sectors,
    default=[]
)

grade_default = preset_filters.get("grade", [])
grade_filter = st.sidebar.multiselect(
    "Fund Grade",
    ["A","B","C","D","F"],
    default=grade_default
)

pe_max = st.sidebar.number_input(
    "Max P/E Ratio",
    min_value=0.0, max_value=200.0,
    value=float(preset_filters.get("pe_max", 100.0)),
    step=1.0
)

roe_min = st.sidebar.number_input(
    "Min ROE %",
    min_value=0.0, max_value=100.0,
    value=float(preset_filters.get("roe_min", 0.0)),
    step=1.0
)

debt_eq_max = st.sidebar.number_input(
    "Max Debt/Equity",
    min_value=0.0, max_value=1000.0,
    value=float(preset_filters.get("debt_eq_max", 1000.0)),
    step=10.0
)

div_yield_min = st.sidebar.number_input(
    "Min Dividend Yield %",
    min_value=0.0, max_value=20.0,
    value=float(preset_filters.get("div_yield_min", 0.0)),
    step=0.1
)

st.sidebar.markdown("---")
st.sidebar.subheader("Sentiment Filters")

sent_min = st.sidebar.slider(
    "Min Sentiment Score",
    min_value=0, max_value=100,
    value=int(preset_filters.get("sentiment_min", 0))
)

st.sidebar.markdown("---")
st.sidebar.subheader("Risk Filters")

sharpe_min = st.sidebar.number_input(
    "Min Sharpe Ratio",
    min_value=-5.0, max_value=10.0,
    value=float(preset_filters.get("sharpe_min", -10.0)),
    step=0.1
)

ann_return_min = st.sidebar.number_input(
    "Min Annual Return %",
    min_value=-100.0, max_value=200.0,
    value=float(preset_filters.get("ann_return_min", -100.0)),
    step=1.0
)

filtered = merged.copy()

if signal_filter:
    if "Signal" in filtered.columns:
        filtered = filtered[
            filtered["Signal"].isin(signal_filter)
        ]

if "RSI" in filtered.columns:
    filtered = filtered[
        (filtered["RSI"].fillna(50) >= rsi_range[0]) &
        (filtered["RSI"].fillna(50) <= rsi_range[1])
    ]

if sector_filter and "Sector" in filtered.columns:
    filtered = filtered[
        filtered["Sector"].isin(sector_filter)
    ]

if grade_filter and "Fund_Grade" in filtered.columns:
    filtered = filtered[
        filtered["Fund_Grade"].isin(grade_filter)
    ]

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
        filtered["Sharpe_Ratio"].fillna(-10) >= sharpe_min
    ]

if "Ann_Return_Pct" in filtered.columns:
    filtered = filtered[
        filtered["Ann_Return_Pct"].fillna(-100) >= ann_return_min
    ]

total   = len(merged)
matched = len(filtered)
pct     = round(matched / total * 100, 1) if total > 0 else 0

kc1, kc2, kc3, kc4 = st.columns(4)
kc1.metric("Total Stocks",   str(total))
kc2.metric("Stocks Matched", str(matched))
kc3.metric("Match Rate",     str(pct) + "%")
kc4.metric(
    "Screen Used",
    preset.split("(")[0].strip()[:20]
)

st.markdown("---")

if filtered.empty:
    st.warning(
        "No stocks match your current criteria. "
        "Try relaxing some filters."
    )
else:
    st.subheader(
        "Screener Results — " +
        str(matched) + " Stocks Found"
    )

    display_cols_priority = [
        "Ticker","Sector","Close","RSI","Signal",
        "Fund_Grade","Fund_Score","PE_Ratio","ROE_Pct",
        "Sentiment_Score","Sharpe_Ratio","Ann_Return_Pct"
    ]
    display_cols = [
        c for c in display_cols_priority
        if c in filtered.columns
    ]

    display_df = filtered[display_cols].copy()
    display_df["Ticker"] = display_df["Ticker"].str.replace(".NS","")

    for col in ["PE_Ratio","ROE_Pct","Sharpe_Ratio",
                "Ann_Return_Pct","Fund_Score","Sentiment_Score"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(2)

    if "RSI" in display_df.columns:
        display_df["RSI"] = display_df["RSI"].round(1)

    if "Close" in display_df.columns:
        display_df["Close"] = display_df["Close"].apply(
            lambda x: "{:,.2f}".format(float(x)) if pd.notna(x) else "N/A"
        )

    sort_options = [
        c for c in [
            "Fund_Score","ROE_Pct","Sharpe_Ratio",
            "Ann_Return_Pct","Sentiment_Score","RSI"
        ] if c in display_df.columns
    ]

    if sort_options:
        sort_by = st.selectbox(
            "Sort results by",
            sort_options,
            index=0
        )
        if sort_by in display_df.columns:
            display_df = display_df.sort_values(
                sort_by, ascending=False
            )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    if len(filtered) > 1:
        st.markdown("---")
        st.subheader("Visual Analysis of Screener Results")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            if "RSI" in filtered.columns and "Fund_Score" in filtered.columns:
                scatter_df = filtered.dropna(
                    subset=["RSI","Fund_Score"]
                ).copy()
                scatter_df["Ticker_Clean"] = scatter_df["Ticker"].str.replace(".NS","")

                fig_sc = px.scatter(
                    scatter_df,
                    x="RSI",
                    y="Fund_Score",
                    color="Signal" if "Signal" in scatter_df.columns else None,
                    text="Ticker_Clean",
                    size_max=15,
                    title="RSI vs Fundamental Score",
                    labels={
                        "RSI":        "RSI Value",
                        "Fund_Score": "Fundamental Score (0-100)"
                    },
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
                    annotation_text="Average Score"
                )
                fig_sc.update_traces(
                    textposition="top center",
                    textfont_size=9
                )
                fig_sc.update_layout(
                    height=380,
                    template="plotly_white"
                )
                st.plotly_chart(fig_sc, use_container_width=True)

        with chart_col2:
            if "Sector" in filtered.columns:
                sector_counts = filtered["Sector"].value_counts()
                fig_sec = go.Figure(go.Pie(
                    labels=sector_counts.index.tolist(),
                    values=sector_counts.values.tolist(),
                    hole=0.4,
                    textinfo="label+percent+value"
                ))
                fig_sec.update_layout(
                    height=380,
                    title="Screened Stocks by Sector",
                    legend=dict(orientation="h")
                )
                st.plotly_chart(fig_sec, use_container_width=True)

    st.markdown("---")
    st.caption(
        "Screener uses latest available data. "
        "Always do your own research before investing. "
        "This tool is for educational purposes only."
    )
