import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical

st.set_page_config(
    page_title="Strategy Builder",
    page_icon="⚙️",
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
    '<h2 style="margin:0">⚙️ Custom Strategy Backtester</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Build your own trading rules and see how they would have performed '
    'over the past year vs buy-and-hold'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

df = load_technical()
if df.empty:
    st.error("Technical data not found.")
    st.stop()

df["Date"] = pd.to_datetime(df["Date"])

st.sidebar.header("Strategy Configuration")

all_tickers = sorted(df["Ticker"].unique().tolist())
selected_tickers = st.sidebar.multiselect(
    "Select Stocks to Backtest",
    all_tickers,
    default=all_tickers[:5],
    format_func=lambda x: str(x).replace(".NS", "")
)

st.sidebar.markdown("---")
st.sidebar.subheader("Entry Rules (Buy When)")

use_rsi_entry = st.sidebar.checkbox("RSI below threshold", value=True)
rsi_entry_threshold = st.sidebar.slider(
    "RSI Entry Threshold",
    min_value=10, max_value=60,
    value=35, step=1,
    disabled=not use_rsi_entry
)

use_macd_entry = st.sidebar.checkbox(
    "MACD crosses above Signal Line", value=True
)

use_sma_entry = st.sidebar.checkbox(
    "Price above SMA 50", value=False
)

use_bb_entry = st.sidebar.checkbox(
    "Price touches Lower Bollinger Band", value=False
)

st.sidebar.markdown("---")
st.sidebar.subheader("Exit Rules (Sell When)")

use_rsi_exit = st.sidebar.checkbox("RSI above threshold", value=True)
rsi_exit_threshold = st.sidebar.slider(
    "RSI Exit Threshold",
    min_value=50, max_value=90,
    value=65, step=1,
    disabled=not use_rsi_exit
)

use_macd_exit = st.sidebar.checkbox(
    "MACD crosses below Signal Line", value=False
)

use_sma_exit = st.sidebar.checkbox(
    "Price below SMA 50", value=False
)

st.sidebar.markdown("---")
st.sidebar.subheader("Risk Management")

stop_loss_pct = st.sidebar.slider(
    "Stop Loss %",
    min_value=0.0, max_value=20.0,
    value=5.0, step=0.5
)

take_profit_pct = st.sidebar.slider(
    "Take Profit %",
    min_value=0.0, max_value=50.0,
    value=15.0, step=0.5
)

initial_capital = st.sidebar.number_input(
    "Initial Capital (Rs)",
    min_value=10000,
    max_value=10000000,
    value=100000,
    step=10000
)

def check_entry(row, prev_row=None):
    conditions_met = []

    if use_rsi_entry:
        rsi = float(row.get("RSI", 50) or 50)
        conditions_met.append(rsi < rsi_entry_threshold)

    if use_macd_entry and prev_row is not None:
        macd_now  = float(row.get("MACD", 0) or 0)
        sig_now   = float(row.get("MACD_Signal", 0) or 0)
        macd_prev = float(prev_row.get("MACD", 0) or 0)
        sig_prev  = float(prev_row.get("MACD_Signal", 0) or 0)
        crossed_above = (macd_prev < sig_prev) and (macd_now > sig_now)
        conditions_met.append(crossed_above)

    if use_sma_entry:
        close = float(row.get("Close", 0) or 0)
        sma50 = float(row.get("SMA_50", 0) or 0)
        if sma50 > 0:
            conditions_met.append(close > sma50)

    if use_bb_entry:
        close  = float(row.get("Close", 0) or 0)
        bb_low = float(row.get("BB_Lower", 0) or 0)
        if bb_low > 0:
            conditions_met.append(close <= bb_low * 1.01)

    if not conditions_met:
        return False
    return all(conditions_met)


def check_exit(row, prev_row=None, entry_price=None):
    conditions_met = []

    if use_rsi_exit:
        rsi = float(row.get("RSI", 50) or 50)
        conditions_met.append(rsi > rsi_exit_threshold)

    if use_macd_exit and prev_row is not None:
        macd_now  = float(row.get("MACD", 0) or 0)
        sig_now   = float(row.get("MACD_Signal", 0) or 0)
        macd_prev = float(prev_row.get("MACD", 0) or 0)
        sig_prev  = float(prev_row.get("MACD_Signal", 0) or 0)
        crossed_below = (macd_prev > sig_prev) and (macd_now < sig_now)
        conditions_met.append(crossed_below)

    if use_sma_exit:
        close = float(row.get("Close", 0) or 0)
        sma50 = float(row.get("SMA_50", 0) or 0)
        if sma50 > 0:
            conditions_met.append(close < sma50)

    if entry_price is not None and entry_price > 0:
        curr_price = float(row.get("Close", 0) or 0)
        ret = (curr_price - entry_price) / entry_price * 100
        if stop_loss_pct > 0 and ret <= -stop_loss_pct:
            return True, "Stop Loss"
        if take_profit_pct > 0 and ret >= take_profit_pct:
            return True, "Take Profit"

    if conditions_met and all(conditions_met):
        return True, "Signal Exit"

    return False, ""


def run_backtest(stock_df, capital):
    stock_df = stock_df.sort_values("Date").reset_index(drop=True)
    stock_df = stock_df.dropna(subset=["Close"])

    if len(stock_df) < 20:
        return None, None, []

    position     = 0
    cash         = float(capital)
    shares       = 0.0
    entry_price  = 0.0
    equity_curve = []
    trades       = []

    for i in range(1, len(stock_df)):
        row      = stock_df.iloc[i]
        prev_row = stock_df.iloc[i - 1]
        price    = float(row["Close"])
        date     = row["Date"]

        if position == 0:
            if check_entry(row, prev_row):
                shares      = cash / price
                cash        = 0.0
                position    = 1
                entry_price = price
                trades.append({
                    "Date":        date,
                    "Action":      "BUY",
                    "Price":       round(price, 2),
                    "Reason":      "Entry Signal"
                })
        else:
            should_exit, reason = check_exit(row, prev_row, entry_price)
            if should_exit:
                cash     = shares * price
                ret_pct  = round((price - entry_price) / entry_price * 100, 2)
                shares   = 0.0
                position = 0
                trades.append({
                    "Date":        date,
                    "Action":      "SELL",
                    "Price":       round(price, 2),
                    "Return %":    ret_pct,
                    "Reason":      reason
                })

        current_value = cash + (shares * price)
        equity_curve.append({
            "Date":     date,
            "Equity":   round(current_value, 2),
            "Close":    price
        })

    equity_df = pd.DataFrame(equity_curve)

    if equity_df.empty:
        return None, None, []

    first_price = float(stock_df["Close"].iloc[0])
    bh_shares   = capital / first_price
    equity_df["BuyHold"] = bh_shares * equity_df["Close"]

    return equity_df, pd.DataFrame(trades), trades


if not selected_tickers:
    st.warning("Select at least one stock from the sidebar.")
    st.stop()

entry_rules  = []
exit_rules   = []
if use_rsi_entry:  entry_rules.append("RSI < " + str(rsi_entry_threshold))
if use_macd_entry: entry_rules.append("MACD crosses above Signal")
if use_sma_entry:  entry_rules.append("Price > SMA 50")
if use_bb_entry:   entry_rules.append("Price touches BB Lower")
if use_rsi_exit:   exit_rules.append("RSI > " + str(rsi_exit_threshold))
if use_macd_exit:  exit_rules.append("MACD crosses below Signal")
if use_sma_exit:   exit_rules.append("Price < SMA 50")

col_rules1, col_rules2 = st.columns(2)
with col_rules1:
    st.markdown(
        '<div style="background:#E8F5E9;border-left:4px solid #2CA02C;'
        'padding:12px;border-radius:6px;">'
        '<b style="color:#2CA02C">Entry Rules (ALL must be true):</b><br>'
        + ("<br>".join(["• " + r for r in entry_rules]) if entry_rules
           else "• No entry rules set") +
        '</div>',
        unsafe_allow_html=True
    )
with col_rules2:
    st.markdown(
        '<div style="background:#FFEBEE;border-left:4px solid #D62728;'
        'padding:12px;border-radius:6px;">'
        '<b style="color:#D62728">Exit Rules (ANY triggers exit):</b><br>'
        + ("<br>".join(["• " + r for r in exit_rules]) if exit_rules
           else "• No exit rules set") +
        "<br>• Stop Loss: " + str(stop_loss_pct) + "%" +
        "<br>• Take Profit: " + str(take_profit_pct) + "%" +
        '</div>',
        unsafe_allow_html=True
    )

st.markdown("---")

if not entry_rules:
    st.error(
        "Please select at least one entry rule in the sidebar "
        "before running the backtest."
    )
    st.stop()

with st.spinner("Running backtest across selected stocks..."):
    all_results  = []
    all_trades   = []
    summary_rows = []

    for ticker in selected_tickers:
        stock = df[df["Ticker"] == ticker].copy()
        equity_df, trades_df, raw_trades = run_backtest(
            stock, initial_capital
        )

        if equity_df is None:
            continue

        final_equity = float(equity_df["Equity"].iloc[-1])
        final_bh     = float(equity_df["BuyHold"].iloc[-1])
        strat_ret    = round((final_equity / initial_capital - 1) * 100, 2)
        bh_ret       = round((final_bh / initial_capital - 1) * 100, 2)
        outperf      = round(strat_ret - bh_ret, 2)
        num_trades   = len([t for t in raw_trades if t["Action"] == "BUY"])

        sell_trades = [t for t in raw_trades if t.get("Return %") is not None]
        wins        = [t for t in sell_trades if float(t.get("Return %", 0)) > 0]
        win_rate    = round(len(wins) / len(sell_trades) * 100, 1) \
                      if sell_trades else 0.0

        returns_list = equity_df["Equity"].pct_change().dropna()
        max_dd = 0.0
        if len(equity_df) > 1:
            cum     = equity_df["Equity"]
            rolling = cum.cummax()
            dd      = (cum - rolling) / rolling * 100
            max_dd  = round(float(dd.min()), 2)

        equity_df["Ticker"] = ticker
        all_results.append(equity_df)

        if trades_df is not None and not trades_df.empty:
            trades_df["Ticker"] = ticker
            all_trades.append(trades_df)

        summary_rows.append({
            "Ticker":             str(ticker).replace(".NS", ""),
            "Strategy Return %":  strat_ret,
            "Buy-Hold Return %":  bh_ret,
            "Outperformance %":   outperf,
            "Total Trades":       num_trades,
            "Win Rate %":         win_rate,
            "Max Drawdown %":     max_dd,
            "Beat Benchmark":     "Yes" if outperf > 0 else "No"
        })

summary_df = pd.DataFrame(summary_rows)

if summary_df.empty:
    st.warning("No results generated. Check your strategy rules.")
    st.stop()

st.subheader("Backtest Results Summary")

avg_strat = round(float(summary_df["Strategy Return %"].mean()), 2)
avg_bh    = round(float(summary_df["Buy-Hold Return %"].mean()), 2)
beat_count = int((summary_df["Beat Benchmark"] == "Yes").sum())
avg_win   = round(float(summary_df["Win Rate %"].mean()), 1)

kc1, kc2, kc3, kc4, kc5 = st.columns(5)
kc1.metric(
    "Avg Strategy Return",
    str(avg_strat) + "%",
    delta=str(round(avg_strat - avg_bh, 2)) + "% vs BH"
)
kc2.metric("Avg Buy-Hold Return", str(avg_bh) + "%")
kc3.metric(
    "Stocks Beat Benchmark",
    str(beat_count) + "/" + str(len(summary_df))
)
kc4.metric("Avg Win Rate", str(avg_win) + "%")
kc5.metric(
    "Total Trades",
    str(int(summary_df["Total Trades"].sum()))
)

st.markdown("---")

st.dataframe(
    summary_df.sort_values("Outperformance %", ascending=False),
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.subheader("Equity Curve — Strategy vs Buy and Hold")

if all_results:
    equity_combined = pd.concat(all_results, ignore_index=True)

    best_ticker = summary_df.sort_values(
        "Outperformance %", ascending=False
    ).iloc[0]["Ticker"] + ".NS"

    best_eq = equity_combined[
        equity_combined["Ticker"] == best_ticker
    ]

    if not best_eq.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=best_eq["Date"],
            y=best_eq["Equity"],
            name="Your Strategy",
            line=dict(color="#2CA02C", width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=best_eq["Date"],
            y=best_eq["BuyHold"],
            name="Buy and Hold",
            line=dict(color="#1F77B4", width=1.5, dash="dash")
        ))
        fig.add_hline(
            y=initial_capital,
            line_dash="dot",
            line_color="gray",
            annotation_text="Starting Capital"
        )
        fig.update_layout(
            height=420,
            template="plotly_white",
            title="Best Performing Stock: " +
                  best_ticker.replace(".NS", ""),
            xaxis_title="Date",
            yaxis_title="Portfolio Value (Rs)",
            legend=dict(orientation="h", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Outperformance by Stock")
summ_sorted = summary_df.sort_values("Outperformance %", ascending=True)
colors = [
    "#2CA02C" if float(v) >= 0 else "#D62728"
    for v in summ_sorted["Outperformance %"]
]
fig_bar = go.Figure(go.Bar(
    x=summ_sorted["Outperformance %"],
    y=summ_sorted["Ticker"],
    orientation="h",
    marker_color=colors,
    text=["{:+.1f}%".format(float(v))
          for v in summ_sorted["Outperformance %"]],
    textposition="outside"
))
fig_bar.add_vline(x=0, line_color="black", line_width=1)
fig_bar.update_layout(
    height=max(300, len(summ_sorted) * 30),
    template="plotly_white",
    xaxis_title="Outperformance vs Buy-Hold (%)"
)
st.plotly_chart(fig_bar, use_container_width=True)

if all_trades:
    trades_combined = pd.concat(all_trades, ignore_index=True)
    if not trades_combined.empty:
        st.markdown("---")
        st.subheader("Trade Log")
        display_cols = [
            c for c in
            ["Ticker","Date","Action","Price","Return %","Reason"]
            if c in trades_combined.columns
        ]
        st.dataframe(
            trades_combined[display_cols].sort_values(
                "Date", ascending=False
            ).head(50),
            use_container_width=True,
            hide_index=True
        )

st.markdown("---")
st.caption(
    "Backtesting uses historical data only. "
    "Past performance does not guarantee future results. "
    "Transaction costs and slippage are not included."
)
