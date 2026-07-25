import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical, load_signals, load_sentiment

st.set_page_config(
    page_title="My Watchlist",
    page_icon="👁️",
    layout="wide"
)

st.markdown(
    '<style>'
    '[data-testid="stSidebar"]{background:#F0F2F5;}'
    '.block-container{padding-top:1rem;}'
    '.alert-card{'
    'border-radius:8px;padding:12px;margin:8px 0;'
    'border-left:5px solid;'
    '}'
    '</style>',
    unsafe_allow_html=True
)

st.markdown(
    '<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);'
    'padding:20px;border-radius:10px;color:white;margin-bottom:20px;">'
    '<h2 style="margin:0">👁️ My Watchlist — Personalised Stock Tracker</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Track your favourite stocks. Get RSI alerts and sentiment signals.'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

tech     = load_technical()
signals  = load_signals()
sent     = load_sentiment()

if tech.empty:
    st.error("Technical data not found.")
    st.stop()

tech["Date"] = pd.to_datetime(tech["Date"])

all_tickers = sorted(tech["Ticker"].unique().tolist())
all_clean   = [str(t).replace(".NS","") for t in all_tickers]

st.sidebar.header("Watchlist Setup")

if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = [
        "RELIANCE.NS","TCS.NS","HDFCBANK.NS",
        "INFY.NS","ICICIBANK.NS"
    ]

selected_watchlist = st.sidebar.multiselect(
    "Add stocks to your watchlist",
    all_tickers,
    default=st.session_state["watchlist"],
    format_func=lambda x: str(x).replace(".NS","")
)

if selected_watchlist:
    st.session_state["watchlist"] = selected_watchlist

st.sidebar.markdown("---")
st.sidebar.subheader("Alert Settings")

rsi_overbought = st.sidebar.slider(
    "RSI Overbought Alert",
    min_value=60, max_value=80,
    value=70, step=1
)
rsi_oversold = st.sidebar.slider(
    "RSI Oversold Alert",
    min_value=20, max_value=40,
    value=30, step=1
)

show_alerts_only = st.sidebar.checkbox(
    "Show Only Stocks with Alerts",
    value=False
)

watchlist = st.session_state.get("watchlist", [])

if not watchlist:
    st.info(
        "Your watchlist is empty. "
        "Add stocks using the sidebar controls."
    )
    st.stop()

watchlist_data   = []
alert_stocks     = []
strong_signals   = []

for ticker in watchlist:
    stock = tech[tech["Ticker"]==ticker].sort_values("Date")
    if stock.empty:
        continue

    latest     = stock.iloc[-1]
    sig_row    = signals[signals["Ticker"]==ticker]
    sent_row   = sent[sent["Ticker"]==ticker]

    rsi_val    = float(latest.get("RSI",  50) or 50)
    macd_val   = float(latest.get("MACD",  0) or 0)
    close_val  = float(latest["Close"])
    signal_val = str(sig_row["Signal"].values[0]) \
                 if not sig_row.empty else "N/A"
    sent_label = str(sent_row["Sentiment_Label"].values[0]) \
                 if not sent_row.empty else "N/A"
    sent_conf  = float(sent_row["Avg_Confidence"].values[0]) \
                 if not sent_row.empty and \
                    "Avg_Confidence" in sent_row.columns \
                 else 0.5

    period_stock = stock.tail(30)
    period_ret   = 0.0
    if len(period_stock) > 1:
        period_ret = round(
            (float(period_stock["Close"].iloc[-1]) /
             float(period_stock["Close"].iloc[0]) - 1) * 100, 2
        )

    alerts = []
    if rsi_val > rsi_overbought:
        alerts.append({
            "type":  "RSI Overbought",
            "msg":   "RSI at " + str(round(rsi_val,1)) +
                     " — above " + str(rsi_overbought),
            "color": "#D62728",
            "icon":  "🔴"
        })
    if rsi_val < rsi_oversold:
        alerts.append({
            "type":  "RSI Oversold",
            "msg":   "RSI at " + str(round(rsi_val,1)) +
                     " — below " + str(rsi_oversold),
            "color": "#2CA02C",
            "icon":  "🟢"
        })
    if signal_val in ["Strong Buy","Buy"]:
        alerts.append({
            "type":  "Buy Signal",
            "msg":   signal_val + " signal active",
            "color": "#2CA02C",
            "icon":  "⭐"
        })
    if signal_val in ["Strong Sell","Sell"]:
        alerts.append({
            "type":  "Sell Signal",
            "msg":   signal_val + " signal active",
            "color": "#D62728",
            "icon":  "⚠️"
        })

    ticker_clean = str(ticker).replace(".NS","")
    entry = {
        "ticker":       ticker,
        "ticker_clean": ticker_clean,
        "price":        close_val,
        "rsi":          rsi_val,
        "macd":         macd_val,
        "signal":       signal_val,
        "sentiment":    sent_label,
        "confidence":   sent_conf,
        "period_ret":   period_ret,
        "alerts":       alerts,
        "stock_data":   stock
    }
    watchlist_data.append(entry)

    if alerts:
        alert_stocks.append(entry)
    if signal_val in ["Strong Buy","Buy"]:
        strong_signals.append(entry)

if show_alerts_only:
    display_data = alert_stocks
else:
    display_data = watchlist_data

alert_count  = sum(len(e["alerts"]) for e in watchlist_data)
signal_count = len(strong_signals)

kc1, kc2, kc3, kc4 = st.columns(4)
kc1.metric("Stocks Watching",  len(watchlist))
kc2.metric("Active Alerts",    alert_count)
kc3.metric("Buy Signals",      signal_count)
kc4.metric("Alert Threshold",  "RSI " + str(rsi_oversold) +
           "/" + str(rsi_overbought))

if alert_count > 0:
    st.markdown("---")
    st.subheader("Active Alerts")
    for entry in alert_stocks:
        for alert in entry["alerts"]:
            st.markdown(
                '<div class="alert-card" style="'
                'background:' + alert["color"] + '11;'
                'border-color:' + alert["color"] + ';">'
                '' + alert["icon"] + ' <b>' +
                entry["ticker_clean"] + '</b> — ' +
                alert["type"] + ': ' + alert["msg"] +
                '</div>',
                unsafe_allow_html=True
            )

st.markdown("---")
st.subheader("Watchlist Overview")

overview_rows = []
for entry in display_data:
    ret_str = "{:+.2f}%".format(entry["period_ret"])
    alert_str = (
        ", ".join([a["type"] for a in entry["alerts"]])
        if entry["alerts"] else "None"
    )
    overview_rows.append({
        "Ticker":       entry["ticker_clean"],
        "Price (Rs)":   "{:,.2f}".format(entry["price"]),
        "RSI":          "{:.1f}".format(entry["rsi"]),
        "30d Return":   ret_str,
        "Signal":       entry["signal"],
        "Sentiment":    entry["sentiment"],
        "Confidence":   "{:.0%}".format(entry["confidence"]),
        "Alerts":       alert_str
    })

if overview_rows:
    st.dataframe(
        pd.DataFrame(overview_rows),
        use_container_width=True,
        hide_index=True
    )

st.markdown("---")
st.subheader("Individual Stock Charts")

chart_ticker = st.selectbox(
    "Select stock to view chart",
    [e["ticker_clean"] for e in display_data],
    index=0
)

chart_entry = next(
    (e for e in display_data
     if e["ticker_clean"] == chart_ticker),
    None
)

if chart_entry:
    stock     = chart_entry["stock_data"]
    plot_data = stock.tail(90).copy()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[
            chart_ticker + " — Price (90 Days)",
            "RSI (14)"
        ],
        row_heights=[0.65, 0.35]
    )

    fig.add_trace(go.Scatter(
        x=plot_data["Date"],
        y=plot_data["Close"],
        name="Price",
        line=dict(color="#1F77B4", width=2)
    ), row=1, col=1)

    if "SMA_20" in plot_data.columns:
        fig.add_trace(go.Scatter(
            x=plot_data["Date"],
            y=plot_data["SMA_20"],
            name="SMA 20",
            line=dict(color="#FF7F0E",width=1.5,dash="dash")
        ), row=1, col=1)

    if "SMA_50" in plot_data.columns:
        fig.add_trace(go.Scatter(
            x=plot_data["Date"],
            y=plot_data["SMA_50"],
            name="SMA 50",
            line=dict(color="#2CA02C",width=1.5,dash="dash")
        ), row=1, col=1)

    if "RSI" in plot_data.columns:
        rsi_colors = [
            "#D62728" if float(r) > rsi_overbought else
            "#2CA02C" if float(r) < rsi_oversold  else
            "#9467BD"
            for r in plot_data["RSI"].fillna(50)
        ]
        fig.add_trace(go.Scatter(
            x=plot_data["Date"],
            y=plot_data["RSI"],
            name="RSI",
            line=dict(color="#9467BD", width=2)
        ), row=2, col=1)
        fig.add_hline(
            y=rsi_overbought,
            line_dash="dash",
            line_color="#D62728",
            annotation_text="Overbought (" +
                            str(rsi_overbought) + ")",
            row=2, col=1
        )
        fig.add_hline(
            y=rsi_oversold,
            line_dash="dash",
            line_color="#2CA02C",
            annotation_text="Oversold (" +
                            str(rsi_oversold) + ")",
            row=2, col=1
        )

    fig.update_layout(
        height=500,
        template="plotly_white",
        legend=dict(orientation="h", y=1.02),
        margin=dict(t=40, b=20)
    )
    fig.update_yaxes(title_text="Price (Rs)", row=1, col=1)
    fig.update_yaxes(
        title_text="RSI",
        range=[0, 100],
        row=2, col=1
    )
    st.plotly_chart(fig, use_container_width=True)

    if chart_entry["alerts"]:
        for alert in chart_entry["alerts"]:
            st.markdown(
                '<div class="alert-card" style="'
                'background:' + alert["color"] + '11;'
                'border-color:' + alert["color"] + ';">'
                '' + alert["icon"] + ' ' + alert["type"] +
                ': ' + alert["msg"] +
                '</div>',
                unsafe_allow_html=True
            )
