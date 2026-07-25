import streamlit as st
import pandas as pd
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")

from data_loader import (
    load_signals,
    load_sentiment,
    load_risk_metrics,
    load_backtest_summary,
    load_backtest_trades,
    load_technical,
    get_data_freshness
)

st.set_page_config(
    page_title="NIFTY 50 Intelligence System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Data freshness banner ──────────────────────────────
freshness = get_data_freshness()
if freshness["is_fresh"]:
    st.success(
        "Data last updated: **" +
        freshness["last_updated"] +
        "** — refreshes automatically every weekday at 4:30 PM IST"
    )
else:
    st.warning(
        "Data last updated: **" +
        freshness["last_updated"] +
        "** (" + str(freshness["hours_old"]) + " hours ago) — "
        "may not reflect today's market. "
        "Run 00_master_update in Colab and upload fresh CSV files."
    )

st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #1F3864, #2E5EAA);
    padding: 25px 30px;
    border-radius: 12px;
    color: white;
    text-align: center;
    margin-bottom: 25px;
    box-shadow: 0 4px 15px rgba(31,56,100,0.3);
}
.main-header h1 {
    font-size: 2.2rem;
    margin: 0;
    font-weight: 800;
}
.main-header p {
    font-size: 0.95rem;
    opacity: 0.85;
    margin: 6px 0 0 0;
}
.metric-card {
    background: linear-gradient(135deg, #1F3864, #2E5EAA);
    padding: 20px 15px;
    border-radius: 10px;
    color: white;
    text-align: center;
    box-shadow: 0 3px 10px rgba(0,0,0,0.2);
    margin-bottom: 10px;
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.75rem;
    opacity: 0.85;
    margin-top: 5px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.section-header {
    color: #1F3864;
    font-size: 1.1rem;
    font-weight: 700;
    border-bottom: 2px solid #1F77B4;
    padding-bottom: 6px;
    margin: 20px 0 15px 0;
}
[data-testid="stSidebar"] {
    background: #F0F2F5;
}
.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📈 NIFTY 50 Intelligence System</h1>
    <p>End-to-end automated stock market analysis for all 50 NIFTY 50 stocks</p>
    <p>Python · FinBERT NLP · Prophet Forecasting · Portfolio Optimization</p>
</div>
""", unsafe_allow_html=True)

try:
    signals  = load_signals()
    sent     = load_sentiment()
    risk     = load_risk_metrics()
    backtest = load_backtest_summary()
    trades   = load_backtest_trades()
    tech     = load_technical()
except Exception as e:
    st.error("Error loading data: " + str(e))
    st.stop()

bull = len(signals[signals["Signal"].isin(
    ["Strong Buy","Buy","Weak Buy"]
)]) if "Signal" in signals.columns else 0

bear = len(signals[signals["Signal"].isin(
    ["Strong Sell","Sell","Weak Sell"]
)]) if "Signal" in signals.columns else 0

sent_score = round(float(sent["Sentiment_Score"].mean()), 1) \
             if not sent.empty and "Sentiment_Score" in sent.columns \
             else 0

win_rate = round(
    float((backtest["Beat_Benchmark"]=="Yes").mean()) * 100, 1
) if not backtest.empty and "Beat_Benchmark" in backtest.columns \
  else 0

avg_sharpe = round(float(risk["Sharpe_Ratio"].mean()), 3) \
             if not risk.empty and "Sharpe_Ratio" in risk.columns \
             else 0

total_trades = len(trades) if not trades.empty else 0

st.markdown(
    '<p class="section-header">📊 Live Market Snapshot</p>',
    unsafe_allow_html=True
)

c1, c2, c3, c4, c5 = st.columns(5)
for col, val, color, label in [
    (c1, "49",            "#FFFFFF", "Stocks Tracked"),
    (c2, str(bull),       "#90EE90", "Bullish Signals"),
    (c3, str(bear),       "#FF6B6B", "Bearish Signals"),
    (c4, str(sent_score), "#FFD700", "Market Sentiment"),
    (c5, str(avg_sharpe), "#90EE90", "Avg Sharpe Ratio"),
]:
    with col:
        st.markdown(
            '<div class="metric-card">'
            '<div class="metric-value" style="color:' + color + '">'
            + val +
            '</div>'
            '<div class="metric-label">' + label + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

cl, cr = st.columns(2)
with cl:
    st.markdown(
        '<p class="section-header">🟢 Top 5 Gainers Today</p>',
        unsafe_allow_html=True
    )
    if "Daily_Return" in signals.columns:
        g = signals.nlargest(5, "Daily_Return")[
            ["Ticker","Close","Daily_Return","Signal"]
        ].copy()
        g["Daily_Return"] = (
            g["Daily_Return"] * 100
        ).round(2).astype(str) + "%"
        g.columns = ["Ticker","Price (Rs)","Return","Signal"]
        st.dataframe(g, use_container_width=True, hide_index=True)

with cr:
    st.markdown(
        '<p class="section-header">🔴 Top 5 Losers Today</p>',
        unsafe_allow_html=True
    )
    if "Daily_Return" in signals.columns:
        lo = signals.nsmallest(5, "Daily_Return")[
            ["Ticker","Close","Daily_Return","Signal"]
        ].copy()
        lo["Daily_Return"] = (
            lo["Daily_Return"] * 100
        ).round(2).astype(str) + "%"
        lo.columns = ["Ticker","Price (Rs)","Return","Signal"]
        st.dataframe(lo, use_container_width=True, hide_index=True)

st.markdown(
    '<p class="section-header">'
    '⭐ Strong Buy Signals — with FinBERT Confidence'
    '</p>',
    unsafe_allow_html=True
)

if "Signal" in signals.columns:
    strong_buy = signals[signals["Signal"] == "Strong Buy"].copy()

    if not strong_buy.empty:
        if not sent.empty and "Avg_Confidence" in sent.columns:
            strong_buy = strong_buy.merge(
                sent[[
                    "Ticker","Sentiment_Label",
                    "Sentiment_Score","Avg_Confidence"
                ]],
                on="Ticker", how="left"
            )

            def confidence_badge(row):
                conf  = row.get("Avg_Confidence", 0)
                label = str(row.get("Sentiment_Label", "N/A"))
                score = row.get("Sentiment_Score", 50)
                if pd.isna(conf):
                    return "N/A"
                conf  = float(conf)
                score = float(score) if not pd.isna(score) else 50.0
                if conf >= 0.85 and score >= 60:
                    color = "#1A7A1A"
                    badge = "STRONG"
                elif conf >= 0.70:
                    color = "#2CA02C"
                    badge = "GOOD"
                elif conf >= 0.55:
                    color = "#FF7F0E"
                    badge = "MODERATE"
                else:
                    color = "#AAAAAA"
                    badge = "WEAK"
                return (
                    '<span style="background:' + color +
                    ';color:white;padding:2px 8px;'
                    'border-radius:4px;font-size:11px;'
                    'font-weight:bold;">'
                    + badge + ' (' + "{:.0%}".format(conf) + ')'
                    '</span>'
                )

            strong_buy["FinBERT Signal"] = strong_buy.apply(
                confidence_badge, axis=1
            )
            display_cols = [
                c for c in [
                    "Ticker","Close","RSI","Signal_Score",
                    "Signal","FinBERT Signal"
                ] if c in strong_buy.columns
            ]
            html_table = strong_buy[display_cols].sort_values(
                "Signal_Score", ascending=False
            ).to_html(escape=False, index=False)
            st.markdown(html_table, unsafe_allow_html=True)
        else:
            display_cols = [
                c for c in [
                    "Ticker","Close","RSI","Signal_Score","Signal"
                ] if c in strong_buy.columns
            ]
            st.dataframe(
                strong_buy[display_cols].sort_values(
                    "Signal_Score", ascending=False
                ),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No Strong Buy signals currently")

st.markdown(
    '<p class="section-header">📊 Strategy Backtest Summary</p>',
    unsafe_allow_html=True
)

b1, b2, b3 = st.columns(3)
b1.metric("Strategy Win Rate", str(win_rate) + "%")
b2.metric("Total Trades Executed", "{:,}".format(total_trades))
best = ""
if not backtest.empty and "Outperformance_Pct" in backtest.columns:
    best = str(
        backtest.nlargest(1, "Outperformance_Pct")["Ticker"].values[0]
    ).replace(".NS","")
b3.metric("Best Signal Stock", best if best else "N/A")

st.markdown(
    '<p class="section-header">💬 FinBERT Sentiment Snapshot</p>',
    unsafe_allow_html=True
)

if not sent.empty and "Sentiment_Label" in sent.columns:
    s1, s2 = st.columns(2)
    with s1:
        st.subheader("🟢 Most Bullish (FinBERT)")
        bull_sent = sent[sent["Sentiment_Label"].isin(
            ["Positive","Very Positive"]
        )]
        if not bull_sent.empty:
            st.dataframe(
                bull_sent.nlargest(5, "Sentiment_Score")[
                    ["Ticker","Sentiment_Label",
                     "Sentiment_Score","Avg_Confidence"]
                ],
                use_container_width=True, hide_index=True
            )
    with s2:
        st.subheader("🔴 Most Bearish (FinBERT)")
        bear_sent = sent[sent["Sentiment_Label"].isin(
            ["Negative","Very Negative"]
        )]
        if not bear_sent.empty:
            st.dataframe(
                bear_sent.nsmallest(5, "Sentiment_Score")[
                    ["Ticker","Sentiment_Label",
                     "Sentiment_Score","Avg_Confidence"]
                ],
                use_container_width=True, hide_index=True
            )

st.markdown(
    '<p class="section-header">'
    '✨ Golden Cross and Death Cross Signals'
    '</p>',
    unsafe_allow_html=True
)

try:
    if not tech.empty and "SMA_50" in tech.columns \
            and "SMA_200" in tech.columns:
        tech["Date"] = pd.to_datetime(tech["Date"])
        cross_rows   = []

        for ticker in tech["Ticker"].unique():
            stock = tech[
                tech["Ticker"] == ticker
            ].sort_values("Date")
            stock = stock.dropna(subset=["SMA_50","SMA_200"])

            if len(stock) < 3:
                continue

            latest   = stock.iloc[-1]
            prev     = stock.iloc[-2]
            sma50    = float(latest["SMA_50"])
            sma200   = float(latest["SMA_200"])
            sma50_p  = float(prev["SMA_50"])
            sma200_p = float(prev["SMA_200"])

            if sma50_p < sma200_p and sma50 > sma200:
                cross_rows.append({
                    "Ticker":     str(ticker).replace(".NS",""),
                    "Signal":     "Golden Cross",
                    "SMA 50":     "{:,.2f}".format(sma50),
                    "SMA 200":    "{:,.2f}".format(sma200),
                    "Price (Rs)": "{:,.2f}".format(
                        float(latest["Close"])),
                    "Type":       "bullish"
                })
            elif sma50_p > sma200_p and sma50 < sma200:
                cross_rows.append({
                    "Ticker":     str(ticker).replace(".NS",""),
                    "Signal":     "Death Cross",
                    "SMA 50":     "{:,.2f}".format(sma50),
                    "SMA 200":    "{:,.2f}".format(sma200),
                    "Price (Rs)": "{:,.2f}".format(
                        float(latest["Close"])),
                    "Type":       "bearish"
                })

        if cross_rows:
            cross_df = pd.DataFrame(cross_rows)
            golden   = cross_df[cross_df["Type"] == "bullish"]
            death    = cross_df[cross_df["Type"] == "bearish"]

            cc1, cc2 = st.columns(2)
            with cc1:
                if not golden.empty:
                    st.markdown(
                        '<div style="background:#E8F5E9;'
                        'border-left:4px solid #2CA02C;'
                        'padding:12px;border-radius:8px;">'
                        '<b style="color:#2CA02C">'
                        '✨ Golden Cross Detected</b>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                    st.dataframe(
                        golden.drop(columns=["Type"]),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No Golden Cross signals today")
            with cc2:
                if not death.empty:
                    st.markdown(
                        '<div style="background:#FFEBEE;'
                        'border-left:4px solid #D62728;'
                        'padding:12px;border-radius:8px;">'
                        '<b style="color:#D62728">'
                        '💀 Death Cross Detected</b>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                    st.dataframe(
                        death.drop(columns=["Type"]),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No Death Cross signals today")
        else:
            st.info(
                "No Golden Cross or Death Cross signals today. "
                "These are rare events — typically a few per month."
            )
    else:
        st.info("Technical data not available for cross signals.")

except Exception as e:
    st.warning(
        "Cross signal calculation skipped: " + str(e)
    )

st.markdown("---")
st.markdown(
    "**📈 NIFTY 50 Intelligence System** | "
    "Built by **Pushkar Singh** | "
    "Python · FinBERT · Prophet · LSTM · PyPortfolioOpt | "
    "*Data refreshes daily after 3:30 PM IST*"
)
