
import streamlit as st
import pandas as pd
import sys
sys.path.append('/content/streamlit_app')
from data_loader import (load_signals, load_sentiment,
                          load_risk_metrics, load_backtest_trades, load_backtest_summary)

st.set_page_config(
    page_title = "NIFTY 50 Intelligence System",
    page_icon  = "📈",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

# ── Custom CSS ──
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
    .main-header h1 { font-size: 2.2rem; margin: 0; }
    .main-header p  { font-size: 1rem; opacity: 0.85; margin: 5px 0 0 0; }

    .metric-card {
        background: linear-gradient(135deg, #1F3864, #2E5EAA);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .metric-label {
        font-size: 0.8rem;
        opacity: 0.85;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .section-header {
        color: #1F3864;
        font-size: 1.2rem;
        font-weight: 700;
        border-bottom: 2px solid #1F77B4;
        padding-bottom: 5px;
        margin: 20px 0 15px 0;
    }

    [data-testid="stSidebar"] {
        background: #F0F2F5;
    }

    .stDataFrame { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="main-header">
    <h1>📈 NIFTY 50 Intelligence System</h1>
    <p>End-to-end stock market analysis for all 50 NIFTY 50 stocks</p>
    <p>Python · FinBERT NLP · Prophet · LSTM · PyPortfolioOpt · Power BI</p>
</div>
""", unsafe_allow_html=True)

# ── Load Data ──
signals  = load_signals()
sent     = load_sentiment()
risk     = load_risk_metrics()
backtest = load_backtest_summary()

# ── Calculate KPIs ──
bull  = len(signals[signals["Signal"].isin(
    ["Strong Buy","Buy","Weak Buy"]
)])
bear  = len(signals[signals["Signal"].isin(
    ["Strong Sell","Sell","Weak Sell"]
)])
sent_score = round(sent["Sentiment_Score"].mean(), 1) \
             if not sent.empty else 0
win_rate   = round(
    (backtest["Beat_Benchmark"]=="Yes").mean()*100, 1
) if not backtest.empty else 0
avg_sharpe = round(risk["Sharpe_Ratio"].mean(), 3) \
             if not risk.empty else 0

# ── KPI Row 1 ──
st.markdown('<p class="section-header">📊 Market Snapshot</p>',
            unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">49</div>
        <div class="metric-label">Stocks Tracked</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:#90EE90">{bull}</div>
        <div class="metric-label">🟢 Bullish Signals</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:#FF6B6B">{bear}</div>
        <div class="metric-label">🔴 Bearish Signals</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:#FFD700">{sent_score}</div>
        <div class="metric-label">💬 Market Sentiment</div>
    </div>""", unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:#90EE90">{avg_sharpe}</div>
        <div class="metric-label">📊 Avg Sharpe Ratio</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Signal Summary ──
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<p class="section-header">🟢 Top 5 Gainers</p>',
                unsafe_allow_html=True)
    if "Daily_Return" in signals.columns:
        gainers = signals.nlargest(5, "Daily_Return")[
            ["Ticker","Close","Daily_Return","Signal"]
        ].copy()
        gainers["Daily_Return"] = (
            gainers["Daily_Return"]*100
        ).round(2).astype(str) + "%"
        gainers.columns = ["Ticker","Price (₹)","Return","Signal"]
        st.dataframe(
            gainers, use_container_width=True, hide_index=True
        )

with col_right:
    st.markdown('<p class="section-header">🔴 Top 5 Losers</p>',
                unsafe_allow_html=True)
    if "Daily_Return" in signals.columns:
        losers = signals.nsmallest(5, "Daily_Return")[
            ["Ticker","Close","Daily_Return","Signal"]
        ].copy()
        losers["Daily_Return"] = (
            losers["Daily_Return"]*100
        ).round(2).astype(str) + "%"
        losers.columns = ["Ticker","Price (₹)","Return","Signal"]
        st.dataframe(
            losers, use_container_width=True, hide_index=True
        )

# ── Strong Buy Signals ──
st.markdown('<p class="section-header">⭐ Strong Buy Signals Right Now</p>',
            unsafe_allow_html=True)
strong_buy = signals[signals["Signal"] == "Strong Buy"][
    ["Ticker","Close","RSI","Signal_Score","Signal"]
].copy() if "Signal" in signals.columns else pd.DataFrame()

if not strong_buy.empty:
    st.dataframe(
        strong_buy.sort_values(
            "Signal_Score", ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No Strong Buy signals currently")

# ── Backtest Summary ──
st.markdown(
    '<p class="section-header">📊 Strategy Backtest Summary</p>',
    unsafe_allow_html=True
)
col_b1, col_b2, col_b3 = st.columns(3)
with col_b1:
    st.metric("Strategy Win Rate", f"{win_rate}%")
with col_b2:
    total_trades = len(load_backtest_trades()) \
                   if not backtest.empty else 0
    st.metric("Total Trades Executed", total_trades)
with col_b3:
    best = backtest.nlargest(1,"Outperformance_Pct")[
        "Ticker"
    ].values[0] if not backtest.empty else "N/A"
    st.metric("Best Signal Stock", best.replace(".NS",""))

# ── Footer ──
# ── Golden Cross / Death Cross Alerts ────────────────────
st.markdown(
    '<p class="section-header">'
    '✨ Golden Cross and Death Cross Signals'
    '</p>',
    unsafe_allow_html=True
)

try:
    tech = load_technical()
    if not tech.empty and "SMA_50" in tech.columns and "SMA_200" in tech.columns:
        tech["Date"] = pd.to_datetime(tech["Date"])
        cross_rows   = []

        for ticker in tech["Ticker"].unique():
            stock = tech[tech["Ticker"] == ticker].sort_values("Date")
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
                    "Signal":     "✨ Golden Cross",
                    "SMA 50":     "{:,.2f}".format(sma50),
                    "SMA 200":    "{:,.2f}".format(sma200),
                    "Price (Rs)": "{:,.2f}".format(
                                      float(latest["Close"])),
                    "Type":       "bullish"
                })

            elif sma50_p > sma200_p and sma50 < sma200:
                cross_rows.append({
                    "Ticker":     str(ticker).replace(".NS",""),
                    "Signal":     "💀 Death Cross",
                    "SMA 50":     "{:,.2f}".format(sma50),
                    "SMA 200":    "{:,.2f}".format(sma200),
                    "Price (Rs)": "{:,.2f}".format(
                                      float(latest["Close"])),
                    "Type":       "bearish"
                })

        if cross_rows:
            cross_df = pd.DataFrame(cross_rows)
            golden   = cross_df[cross_df["Type"]=="bullish"]
            death    = cross_df[cross_df["Type"]=="bearish"]

            cc1, cc2 = st.columns(2)
            with cc1:
                if not golden.empty:
                    st.markdown(
                        '<div style="background:#E8F5E9;border-left:'
                        '4px solid #2CA02C;padding:12px;border-radius:8px;">'
                        '<b style="color:#2CA02C">✨ Golden Cross Detected</b>'
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
                        '<div style="background:#FFEBEE;border-left:'
                        '4px solid #D62728;padding:12px;border-radius:8px;">'
                        '<b style="color:#D62728">💀 Death Cross Detected</b>'
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
                "No Golden Cross or Death Cross signals detected today. "
                "These signals are rare — typically a few per month."
            )
    else:
        st.info("Technical data not available for cross signals.")

except Exception as e:
    st.info("Cross signal calculation encountered an issue: " + str(e))
st.markdown(
    '<p class="section-header">⭐ Strong Buy Signals — with FinBERT Confidence</p>',
    unsafe_allow_html=True
)

if "Signal" in signals.columns:
    strong_buy = signals[
        signals["Signal"] == "Strong Buy"
    ].copy()

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
                label = str(row.get("Sentiment_Label","N/A"))
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
                    f'<span style="background:{color};color:white;'
                    f'padding:2px 8px;border-radius:4px;'
                    f'font-size:11px;font-weight:bold;">'
                    f'{badge} ({conf:.0%})</span>'
                )

            strong_buy["FinBERT Signal"] = strong_buy.apply(
                confidence_badge, axis=1
            )

            display_cols = [
                "Ticker","Close","RSI","Signal_Score",
                "Signal","FinBERT Signal"
            ]
            display_cols = [
                c for c in display_cols
                if c in strong_buy.columns
            ]
            display_html = strong_buy[display_cols].sort_values(
                "Signal_Score", ascending=False
            ).to_html(escape=False, index=False)

            st.markdown(display_html, unsafe_allow_html=True)
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
        st.info("No Strong Buy signals currently — market is neutral")
st.markdown("""
**📈 NIFTY 50 Intelligence System** |
Built by **Pushkar Singh** |
Python · FinBERT · Prophet · LSTM · PyPortfolioOpt · Power BI |
[GitHub](https://github.com/YourUsername/indian-stock-analysis)

*Data refreshes daily after 3:30 PM IST*
""")

# Import needed for backtest trades
def load_backtest_trades():
    import pandas as pd
    return pd.read_csv("/content/streamlit_data/backtest_trades_powerbi.csv")
