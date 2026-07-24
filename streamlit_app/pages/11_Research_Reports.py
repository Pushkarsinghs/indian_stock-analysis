import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import (
    load_technical, load_signals, load_fundamentals,
    load_sentiment, load_forecasts, load_risk_metrics
)

st.set_page_config(
    page_title="Research Reports",
    page_icon="📄",
    layout="wide"
)

st.markdown(
    '<style>'
    '[data-testid="stSidebar"]{background:#F0F2F5;}'
    '.block-container{padding-top:1rem;}'
    '.report-header{background:linear-gradient(135deg,#1F3864,#2E5EAA);'
    'padding:20px;border-radius:10px;color:white;margin-bottom:20px;}'
    '.metric-box{background:#F8F9FA;border:1px solid #DEE2E6;'
    'border-radius:8px;padding:12px;text-align:center;margin:5px;}'
    '.metric-box-val{font-size:1.4rem;font-weight:800;color:#1F3864;}'
    '.metric-box-lbl{font-size:0.75rem;color:#666;text-transform:uppercase;}'
    '</style>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="report-header">'
    '<h2 style="margin:0">📄 Equity Research Reports</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Interactive research notes for NIFTY 50 stocks — '
    'covering technicals, fundamentals, sentiment and forecasts'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

try:
    tech     = load_technical()
    signals  = load_signals()
    fund     = load_fundamentals()
    sent     = load_sentiment()
    forecasts= load_forecasts()
    risk     = load_risk_metrics()
except Exception as e:
    st.error("Error loading data: " + str(e))
    st.stop()

if tech.empty:
    st.error("Technical data not found.")
    st.stop()

tech["Date"] = pd.to_datetime(tech["Date"])
if "Date" in forecasts.columns:
    forecasts["Date"] = pd.to_datetime(forecasts["Date"])

st.sidebar.header("Report Controls")

all_tickers = sorted(tech["Ticker"].unique().tolist())
ticker = st.sidebar.selectbox(
    "Select Stock for Report",
    all_tickers,
    index=0
)

period = st.sidebar.selectbox(
    "Chart Period",
    ["3 Months","6 Months","1 Year"],
    index=2
)
days_map = {"3 Months":90,"6 Months":180,"1 Year":365}
days     = days_map[period]

ticker_clean = str(ticker).replace(".NS","")

stock = tech[tech["Ticker"]==ticker].sort_values("Date")
cutoff = stock["Date"].max() - pd.Timedelta(days=days)
stock_period = stock[stock["Date"] >= cutoff].copy()

if stock_period.empty:
    st.warning("No data available for " + ticker)
    st.stop()

latest = stock.iloc[-1]

sig_row   = signals[signals["Ticker"]==ticker]
sig_val   = str(sig_row["Signal"].values[0]) \
            if not sig_row.empty else "N/A"
sig_score = int(sig_row["Signal_Score"].values[0]) \
            if not sig_row.empty and "Signal_Score" in sig_row.columns \
            else 0

fund_row  = fund[fund["Ticker"]==ticker]
sent_row  = sent[sent["Ticker"]==ticker]
risk_row  = risk[risk["Ticker"]==ticker]
fc_stock  = forecasts[forecasts["Ticker"]==ticker].sort_values("Date")

today_ts  = pd.Timestamp.today().normalize()
fc_future = fc_stock[fc_stock["Date"] > today_ts]

from datetime import datetime
report_date = datetime.now().strftime("%d %B %Y")

signal_color = (
    "#1A7A1A" if "Strong Buy" in sig_val else
    "#2CA02C" if "Buy"        in sig_val else
    "#D62728" if "Sell"       in sig_val else
    "#FF7F0E" if "Weak"       in sig_val else
    "#666666"
)

st.markdown(
    '<div style="border:2px solid #1F3864;border-radius:12px;'
    'padding:20px;margin-bottom:20px;">'
    '<div style="display:flex;justify-content:space-between;'
    'align-items:center;border-bottom:2px solid #1F3864;'
    'padding-bottom:12px;margin-bottom:15px;">'
    '<div>'
    '<h1 style="margin:0;color:#1F3864;font-size:1.8rem">'
    + ticker_clean +
    '</h1>'
    '<p style="margin:3px 0 0 0;color:#666;font-size:0.85rem">'
    'NSE Listed  |  NIFTY 50 Component  |  Report Date: '
    + report_date +
    '</p>'
    '</div>'
    '<div style="background:' + signal_color + ';color:white;'
    'padding:8px 20px;border-radius:8px;font-size:1.1rem;'
    'font-weight:800;">'
    + sig_val +
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

close_val = float(latest["Close"])
rsi_val   = float(latest["RSI"])  \
            if pd.notna(latest.get("RSI"))  else 0.0
macd_val  = float(latest["MACD"]) \
            if pd.notna(latest.get("MACD")) else 0.0

period_ret = 0.0
if len(stock_period) > 1:
    period_ret = round(
        (float(stock_period["Close"].iloc[-1]) /
         float(stock_period["Close"].iloc[0]) - 1) * 100, 2
    )

h52w = float(stock["Close"].tail(252).max())
l52w = float(stock["Close"].tail(252).min())

kpi_cols = st.columns(6)
kpi_data = [
    ("Current Price",  "Rs" + "{:,.2f}".format(close_val)),
    ("RSI (14)",       "{:.1f}".format(rsi_val)),
    ("MACD",           "{:.2f}".format(macd_val)),
    (period + " Return", "{:+.2f}%".format(period_ret)),
    ("52W High",       "Rs" + "{:,.2f}".format(h52w)),
    ("52W Low",        "Rs" + "{:,.2f}".format(l52w)),
]
for col, (label, value) in zip(kpi_cols, kpi_data):
    with col:
        st.markdown(
            '<div class="metric-box">'
            '<div class="metric-box-val">' + value + '</div>'
            '<div class="metric-box-lbl">' + label + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

st.markdown('</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Technical",
    "📊 Fundamental",
    "💬 Sentiment",
    "🔮 Forecast",
    "⚠️ Risk"
])

with tab1:
    st.subheader("Price Chart with Technical Indicators")

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[
            ticker_clean + " — Price and Moving Averages",
            "RSI (14)",
            "MACD"
        ],
        row_heights=[0.55, 0.22, 0.23]
    )

    fig.add_trace(go.Scatter(
        x=stock_period["Date"],
        y=stock_period["Close"],
        name="Price",
        line=dict(color="#1F77B4", width=2.5)
    ), row=1, col=1)

    if "SMA_50" in stock_period.columns:
        fig.add_trace(go.Scatter(
            x=stock_period["Date"],
            y=stock_period["SMA_50"],
            name="SMA 50",
            line=dict(color="#FF7F0E", width=1.5, dash="dash")
        ), row=1, col=1)

    if "SMA_200" in stock_period.columns:
        fig.add_trace(go.Scatter(
            x=stock_period["Date"],
            y=stock_period["SMA_200"],
            name="SMA 200",
            line=dict(color="#D62728", width=1.5, dash="dot")
        ), row=1, col=1)

    if "BB_Upper" in stock_period.columns:
        fig.add_trace(go.Scatter(
            x=stock_period["Date"],
            y=stock_period["BB_Upper"],
            line=dict(color="rgba(150,150,150,0.5)", width=1),
            showlegend=False
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=stock_period["Date"],
            y=stock_period["BB_Lower"],
            line=dict(color="rgba(150,150,150,0.5)", width=1),
            fill="tonexty",
            fillcolor="rgba(150,150,150,0.08)",
            name="Bollinger Bands"
        ), row=1, col=1)

    if "RSI" in stock_period.columns:
        fig.add_trace(go.Scatter(
            x=stock_period["Date"],
            y=stock_period["RSI"],
            name="RSI",
            line=dict(color="#9467BD", width=1.5)
        ), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash",
                      line_color="#D62728", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash",
                      line_color="#2CA02C", row=2, col=1)

    if "MACD" in stock_period.columns:
        fig.add_trace(go.Scatter(
            x=stock_period["Date"],
            y=stock_period["MACD"],
            name="MACD",
            line=dict(color="#1F77B4", width=1.5)
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=stock_period["Date"],
            y=stock_period["MACD_Signal"],
            name="Signal",
            line=dict(color="#D62728", width=1.5, dash="dash")
        ), row=3, col=1)
        macd_colors = [
            "#2CA02C" if float(v) >= 0 else "#D62728"
            for v in stock_period["MACD_Hist"].fillna(0)
        ]
        fig.add_trace(go.Bar(
            x=stock_period["Date"],
            y=stock_period["MACD_Hist"],
            marker_color=macd_colors,
            name="Histogram",
            showlegend=False
        ), row=3, col=1)

    fig.update_layout(
        height=600,
        template="plotly_white",
        legend=dict(orientation="h", y=1.02),
        margin=dict(t=40, b=20)
    )
    fig.update_yaxes(title_text="Price (Rs)", row=1, col=1)
    fig.update_yaxes(title_text="RSI",
                     range=[0,100],        row=2, col=1)
    fig.update_yaxes(title_text="MACD",    row=3, col=1)
    st.plotly_chart(fig, use_container_width=True)

    rsi_status = (
        "Overbought (RSI > 70) — potential selling pressure"
        if rsi_val > 70 else
        "Oversold (RSI < 30) — potential buying opportunity"
        if rsi_val < 30 else
        "Neutral zone (30-70) — no extreme reading"
    )
    macd_trend = (
        "Bullish — MACD above signal line"
        if macd_val > 0 else
        "Bearish — MACD below signal line"
    )

    st.markdown("**Technical Summary**")
    st.markdown(
        "- **Overall Signal:** " + sig_val +
        " (Score: " + str(sig_score) + "/5)\n"
        "- **RSI Status:** " + rsi_status + "\n"
        "- **MACD Trend:** " + macd_trend + "\n"
        "- **Period Return:** " + "{:+.2f}%".format(period_ret) +
        " over " + period
    )

with tab2:
    st.subheader("Fundamental Analysis — Financial Health")

    if fund_row.empty:
        st.warning("Fundamental data not available for " + ticker_clean)
    else:
        f = fund_row.iloc[0]

        fund_kpi_cols = st.columns(4)
        fund_kpi_data = [
            ("P/E Ratio",    str(round(float(f["PE_Ratio"]),2)) + "x"
                             if pd.notna(f.get("PE_Ratio")) else "N/A"),
            ("P/B Ratio",    str(round(float(f["PB_Ratio"]),2)) + "x"
                             if pd.notna(f.get("PB_Ratio")) else "N/A"),
            ("ROE",          str(round(float(f["ROE_Pct"]),1)) + "%"
                             if pd.notna(f.get("ROE_Pct")) else "N/A"),
            ("Fund Grade",   str(f.get("Fund_Grade","N/A"))),
        ]

        grade_colors_map = {
            "A":"#1A7A1A","B":"#2CA02C","C":"#FF7F0E",
            "D":"#D62728","F":"#8B0000"
        }
        for col, (label, value) in zip(fund_kpi_cols, fund_kpi_data):
            with col:
                val_color = grade_colors_map.get(
                    str(f.get("Fund_Grade","F")), "#1F3864"
                ) if label == "Fund Grade" else "#1F3864"
                st.markdown(
                    '<div class="metric-box">'
                    '<div class="metric-box-val" style="color:'
                    + val_color + '">' + value + '</div>'
                    '<div class="metric-box-lbl">' + label + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True)

        fund_detail_cols = st.columns(2)
        with fund_detail_cols[0]:
            st.markdown("**Profitability**")
            detail_rows = []
            for col_name, display_name, suffix in [
                ("ROE_Pct",          "Return on Equity",    "%"),
                ("Profit_Margin_Pct","Net Profit Margin",   "%"),
                ("Operating_Margin_Pct","Operating Margin", "%"),
            ]:
                if col_name in f.index and pd.notna(f.get(col_name)):
                    detail_rows.append({
                        "Metric": display_name,
                        "Value":  str(round(float(f[col_name]),2)) + suffix
                    })
            if detail_rows:
                st.dataframe(
                    pd.DataFrame(detail_rows),
                    use_container_width=True,
                    hide_index=True
                )

        with fund_detail_cols[1]:
            st.markdown("**Financial Health**")
            health_rows = []
            for col_name, display_name, suffix in [
                ("Debt_To_Equity","Debt to Equity",  "x"),
                ("Current_Ratio", "Current Ratio",   "x"),
                ("Dividend_Yield_Pct","Dividend Yield","%"),
            ]:
                if col_name in f.index and pd.notna(f.get(col_name)):
                    health_rows.append({
                        "Metric": display_name,
                        "Value":  str(round(float(f[col_name]),2)) + suffix
                    })
            if health_rows:
                st.dataframe(
                    pd.DataFrame(health_rows),
                    use_container_width=True,
                    hide_index=True
                )

        fund_score = float(f.get("Fund_Score", 0)) \
                     if pd.notna(f.get("Fund_Score")) else 0.0
        fund_grade = str(f.get("Fund_Grade","F"))

        grade_msg = {
            "A": "Excellent fundamentals — financially very strong",
            "B": "Good fundamentals — solid financial health",
            "C": "Average fundamentals — acceptable but not outstanding",
            "D": "Below average — some financial weaknesses",
            "F": "Poor fundamentals — significant financial concerns"
        }
        gc = grade_colors_map.get(fund_grade, "#666")
        st.markdown(
            '<div style="background:' + gc + '22;border-left:4px solid '
            + gc + ';padding:12px;border-radius:6px;margin-top:15px;">'
            '<b style="color:' + gc + '">Grade ' + fund_grade +
            ' — Fund Score: ' + str(round(fund_score,0)) + '/100</b><br>'
            '' + grade_msg.get(fund_grade,"") +
            '</div>',
            unsafe_allow_html=True
        )

with tab3:
    st.subheader("FinBERT Sentiment Analysis")

    if sent_row.empty:
        st.warning("Sentiment data not available for " + ticker_clean)
    else:
        s = sent_row.iloc[0]
        sent_label = str(s.get("Sentiment_Label","Neutral"))
        sent_score_val = float(s.get("Sentiment_Score",50))
        sent_conf  = float(s.get("Avg_Confidence",0.5))
        total_arts = int(s.get("Total_Articles",0))
        bull_count = int(s.get("Bullish_Count",0))
        bear_count = int(s.get("Bearish_Count",0))
        neut_count = int(s.get("Neutral_Count",0))

        sent_cols = st.columns(4)
        sent_color_map = {
            "Very Positive":"#1A7A1A","Positive":"#2CA02C",
            "Neutral":"#666666",
            "Negative":"#D62728","Very Negative":"#8B0000"
        }
        sc = sent_color_map.get(sent_label,"#666")
        for col, (label, value) in zip(sent_cols,[
            ("Sentiment",    sent_label),
            ("Score",        "{:.1f}/100".format(sent_score_val)),
            ("Confidence",   "{:.0%}".format(sent_conf)),
            ("Articles",     str(total_arts)),
        ]):
            with col:
                val_color = sc if label == "Sentiment" else "#1F3864"
                st.markdown(
                    '<div class="metric-box">'
                    '<div class="metric-box-val" style="color:'
                    + val_color + '">' + value + '</div>'
                    '<div class="metric-box-lbl">' + label + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True)

        col_pie, col_bar = st.columns(2)

        with col_pie:
            st.markdown("**Headline Breakdown**")
            if total_arts > 0:
                fig_pie = go.Figure(go.Pie(
                    labels=["Bullish","Bearish","Neutral"],
                    values=[bull_count, bear_count, neut_count],
                    hole=0.5,
                    marker_colors=["#2CA02C","#D62728","#AAAAAA"]
                ))
                fig_pie.update_layout(
                    height=250,
                    margin=dict(t=20,b=20,l=20,r=20),
                    showlegend=True,
                    legend=dict(orientation="h")
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        with col_bar:
            st.markdown("**Sentiment Score Context**")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=sent_score_val,
                domain=dict(x=[0,1], y=[0,1]),
                title=dict(text="Sentiment Score"),
                gauge=dict(
                    axis=dict(range=[0,100]),
                    bar=dict(color=sc),
                    steps=[
                        dict(range=[0,30],   color="#FFCCCC"),
                        dict(range=[30,70],  color="#FFFFCC"),
                        dict(range=[70,100], color="#CCFFCC"),
                    ],
                    threshold=dict(
                        line=dict(color="navy", width=3),
                        thickness=0.75,
                        value=50
                    )
                )
            ))
            fig_gauge.update_layout(
                height=250,
                margin=dict(t=30, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        conf_badge_color = (
            "#1A7A1A" if sent_conf >= 0.85 else
            "#2CA02C" if sent_conf >= 0.70 else
            "#FF7F0E"
        )
        conf_label = (
            "High confidence — reliable signal"
            if sent_conf >= 0.85 else
            "Medium confidence — moderately reliable"
            if sent_conf >= 0.70 else
            "Lower confidence — treat with caution"
        )
        st.markdown(
            '<div style="background:' + conf_badge_color +
            '22;border-left:4px solid ' + conf_badge_color +
            ';padding:10px;border-radius:6px;">'
            '<b style="color:' + conf_badge_color +
            '">FinBERT Confidence: ' +
            "{:.0%}".format(sent_conf) + '</b> — ' +
            conf_label +
            '</div>',
            unsafe_allow_html=True
        )

with tab4:
    st.subheader("30-Day Prophet Price Forecast")

    if fc_stock.empty:
        st.warning("Forecast data not available for " + ticker_clean)
    else:
        today_ts  = pd.Timestamp.today().normalize()
        today_str = str(today_ts.date())
        hist_fc   = fc_stock[fc_stock["Date"] <= today_ts]
        fut_fc    = fc_stock[fc_stock["Date"] >  today_ts]

        if not fut_fc.empty:
            curr_price  = float(latest["Close"])
            pred_price  = float(fut_fc["Forecast"].iloc[-1])
            change_pct  = round((pred_price/curr_price - 1)*100, 2)
            upper_price = float(fut_fc["Upper_CI"].iloc[-1]) \
                          if "Upper_CI" in fut_fc.columns else pred_price
            lower_price = float(fut_fc["Lower_CI"].iloc[-1]) \
                          if "Lower_CI" in fut_fc.columns else pred_price

            fc_metric_cols = st.columns(4)
            fc_metric_data = [
                ("Current Price",   "Rs" + "{:,.2f}".format(curr_price)),
                ("30-Day Target",   "Rs" + "{:,.2f}".format(pred_price)),
                ("Expected Change", "{:+.2f}%".format(change_pct)),
                ("Upper / Lower",   "Rs" + "{:,.0f}".format(upper_price) +
                                    " / Rs" + "{:,.0f}".format(lower_price)),
            ]
            for col, (label, value) in zip(
                fc_metric_cols, fc_metric_data
            ):
                with col:
                    val_color = (
                        "#2CA02C" if change_pct > 0 else "#D62728"
                    ) if label == "Expected Change" else "#1F3864"
                    st.markdown(
                        '<div class="metric-box">'
                        '<div class="metric-box-val" style="color:'
                        + val_color + '">' + value + '</div>'
                        '<div class="metric-box-lbl">' + label + '</div>'
                        '</div>',
                        unsafe_allow_html=True
                    )
            st.markdown("<br>", unsafe_allow_html=True)

        fig_fc = go.Figure()
        if not hist_fc.empty:
            fig_fc.add_trace(go.Scatter(
                x=hist_fc["Date"],
                y=hist_fc["Forecast"],
                name="Historical Fitted",
                line=dict(color="#1F77B4", width=1.5)
            ))
        if not fut_fc.empty:
            fig_fc.add_trace(go.Scatter(
                x=fut_fc["Date"],
                y=fut_fc["Forecast"],
                name="30-Day Forecast",
                line=dict(color="#2CA02C", width=2.5)
            ))
            if "Upper_CI" in fut_fc.columns and "Lower_CI" in fut_fc.columns:
                x_band = (
                    list(fut_fc["Date"]) +
                    list(fut_fc["Date"].iloc[::-1])
                )
                y_band = (
                    list(fut_fc["Upper_CI"]) +
                    list(fut_fc["Lower_CI"].iloc[::-1])
                )
                fig_fc.add_trace(go.Scatter(
                    x=x_band, y=y_band,
                    fill="toself",
                    fillcolor="rgba(44,160,44,0.12)",
                    line=dict(color="rgba(255,255,255,0)"),
                    name="80% Confidence Interval"
                ))

        all_y = list(fc_stock["Forecast"].dropna())
        if all_y:
            y_min = min(all_y) * 0.995
            y_max = max(all_y) * 1.005
            fig_fc.add_trace(go.Scatter(
                x=[today_str, today_str],
                y=[y_min, y_max],
                mode="lines",
                line=dict(color="#FF7F0E",width=2,dash="dash"),
                name="Today"
            ))

        fig_fc.update_layout(
            height=420,
            template="plotly_white",
            xaxis_title="Date",
            yaxis_title="Price (Rs)",
            legend=dict(orientation="h", y=1.02),
            margin=dict(t=20, b=30)
        )
        st.plotly_chart(fig_fc, use_container_width=True)

        if not fut_fc.empty:
            direction_color = "#2CA02C" if change_pct > 0 else "#D62728"
            direction_icon  = "📈" if change_pct > 0 else "📉"
            st.markdown(
                '<div style="background:' + direction_color +
                '22;border-left:4px solid ' + direction_color +
                ';padding:12px;border-radius:6px;">'
                '<b style="color:' + direction_color + '">'
                + direction_icon + ' Forecast Direction: '
                + ("Bullish" if change_pct > 0 else "Bearish") +
                '</b><br>'
                'Prophet model predicts ' +
                "{:+.2f}%".format(change_pct) +
                ' change over 30 days. '
                '80% confidence interval: Rs' +
                "{:,.0f}".format(lower_price) +
                ' to Rs' + "{:,.0f}".format(upper_price) +
                '</div>',
                unsafe_allow_html=True
            )

with tab5:
    st.subheader("Risk and Return Metrics")

    if risk_row.empty:
        st.warning("Risk data not available for " + ticker_clean)
    else:
        r = risk_row.iloc[0]

        risk_cols = st.columns(4)
        risk_kpi_data = [
            ("Annual Return",  "{:+.2f}%".format(
                float(r.get("Ann_Return_Pct",0)))),
            ("Annual Volatility", "{:.2f}%".format(
                float(r.get("Ann_Volatility_Pct",0)))),
            ("Sharpe Ratio",   "{:.3f}".format(
                float(r.get("Sharpe_Ratio",0)))),
            ("Max Drawdown",   "{:.2f}%".format(
                float(r.get("Max_Drawdown_Pct",0)))),
        ]

        for col, (label, value) in zip(risk_cols, risk_kpi_data):
            with col:
                if label == "Annual Return":
                    val_color = "#2CA02C" \
                                if float(r.get("Ann_Return_Pct",0)) >= 0 \
                                else "#D62728"
                elif label == "Sharpe Ratio":
                    val_color = "#2CA02C" \
                                if float(r.get("Sharpe_Ratio",0)) >= 1 \
                                else "#FF7F0E" \
                                if float(r.get("Sharpe_Ratio",0)) >= 0 \
                                else "#D62728"
                else:
                    val_color = "#1F3864"
                st.markdown(
                    '<div class="metric-box">'
                    '<div class="metric-box-val" style="color:'
                    + val_color + '">' + value + '</div>'
                    '<div class="metric-box-lbl">' + label + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True)

        risk_detail_cols = st.columns(2)
        with risk_detail_cols[0]:
            risk_rows_tbl = []
            for col_name, display_name, suffix in [
                ("VaR_95_Pct",       "Value at Risk (95%)",  "%"),
                ("CVaR_95_Pct",      "CVaR / Expected Loss",  "%"),
                ("Beta",             "Beta vs NIFTY 50",      "x"),
                ("From_52W_High_Pct","From 52W High",         "%"),
            ]:
                if col_name in r.index and pd.notna(r.get(col_name)):
                    risk_rows_tbl.append({
                        "Metric": display_name,
                        "Value":  str(round(float(r[col_name]),3)) + suffix
                    })
            if risk_rows_tbl:
                st.markdown("**Detailed Risk Metrics**")
                st.dataframe(
                    pd.DataFrame(risk_rows_tbl),
                    use_container_width=True,
                    hide_index=True
                )

        with risk_detail_cols[1]:
            sharpe_val = float(r.get("Sharpe_Ratio",0))
            if sharpe_val >= 2:
                sharpe_rating = "Excellent"
                sharpe_color  = "#1A7A1A"
                sharpe_msg    = "Outstanding risk-adjusted returns"
            elif sharpe_val >= 1:
                sharpe_rating = "Good"
                sharpe_color  = "#2CA02C"
                sharpe_msg    = "Returns justify the risk taken"
            elif sharpe_val >= 0:
                sharpe_rating = "Moderate"
                sharpe_color  = "#FF7F0E"
                sharpe_msg    = "Acceptable but not exceptional"
            else:
                sharpe_rating = "Poor"
                sharpe_color  = "#D62728"
                sharpe_msg    = "Not compensating for risk taken"

            st.markdown("**Sharpe Ratio Assessment**")
            st.markdown(
                '<div style="background:' + sharpe_color +
                '22;border-left:4px solid ' + sharpe_color +
                ';padding:15px;border-radius:6px;">'
                '<b style="color:' + sharpe_color + ';font-size:1.1rem">'
                + sharpe_rating + ' (' + str(round(sharpe_val,3)) + ')'
                '</b><br>'
                + sharpe_msg +
                '<br><br><small>Sharpe > 1 = Good | '
                'Sharpe > 2 = Excellent | '
                'Sharpe < 0 = Returns below risk-free rate</small>'
                '</div>',
                unsafe_allow_html=True
            )

st.markdown("---")
st.caption(
    "Report generated by NIFTY 50 Intelligence System | "
    "Data updated daily after 3:30 PM IST | "
    "Built by Pushkar Singh"
)
