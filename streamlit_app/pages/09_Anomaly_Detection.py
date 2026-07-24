import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical

st.set_page_config(
    page_title="Anomaly Detection",
    page_icon="🚨",
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
    '<h2 style="margin:0">🚨 Anomaly Detection — Unusual Market Activity</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Statistical detection using Z-score analysis across all 50 NIFTY stocks'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

df = load_technical()
if df.empty:
    st.error("Technical data not found.")
    st.stop()

df["Date"] = pd.to_datetime(df["Date"])

st.sidebar.header("Controls")
lookback_days = st.sidebar.selectbox(
    "Baseline Period",
    ["30 Days","60 Days","90 Days"],
    index=1
)
lookback_map = {"30 Days":30,"60 Days":60,"90 Days":90}
lookback     = lookback_map[lookback_days]

zscore_threshold = st.sidebar.slider(
    "Z-Score Threshold",
    min_value=1.5, max_value=4.0,
    value=2.5, step=0.1
)

anomaly_type = st.sidebar.multiselect(
    "Anomaly Types",
    ["Price Spike Up","Price Spike Down","Volume Spike"],
    default=["Price Spike Up","Price Spike Down","Volume Spike"]
)

max_date = df["Date"].max()
cutoff   = max_date - pd.Timedelta(days=lookback)
df_base  = df[df["Date"] >= cutoff].copy()

anomaly_rows = []

for ticker in df_base["Ticker"].unique():
    stock = df_base[
        df_base["Ticker"] == ticker
    ].copy().sort_values("Date")

    if len(stock) < 20:
        continue

    returns = stock["Daily_Return"].dropna()
    volumes = stock["Volume"].dropna()

    if len(returns) < 10 or len(volumes) < 10:
        continue

    ret_mean = float(returns.mean())
    ret_std  = float(returns.std())
    vol_mean = float(volumes.mean())
    vol_std  = float(volumes.std())

    if ret_std == 0 or vol_std == 0:
        continue

    latest = stock.iloc[-1]

    ret_today = float(latest["Daily_Return"]) \
                if pd.notna(latest.get("Daily_Return")) else 0.0
    vol_today = float(latest["Volume"]) \
                if pd.notna(latest.get("Volume")) else 0.0

    ret_zscore = (ret_today - ret_mean) / ret_std
    vol_zscore = (vol_today - vol_mean) / vol_std

    ticker_clean = str(ticker).replace(".NS","")

    if "Price Spike Up" in anomaly_type:
        if ret_zscore > zscore_threshold:
            anomaly_rows.append({
                "Ticker":    ticker_clean,
                "Date":      str(latest["Date"].date()),
                "Type":      "Price Spike Up",
                "Value":     "{:+.2f}%".format(ret_today*100),
                "Z-Score":   round(ret_zscore, 2),
                "Close":     "{:,.2f}".format(float(latest["Close"])),
                "Signal":    str(latest.get("Signal","N/A")),
                "Severity":  "Extreme" if ret_zscore > 4 else
                             "High"    if ret_zscore > 3 else
                             "Medium",
                "_sort":     abs(ret_zscore)
            })

    if "Price Spike Down" in anomaly_type:
        if ret_zscore < -zscore_threshold:
            anomaly_rows.append({
                "Ticker":    ticker_clean,
                "Date":      str(latest["Date"].date()),
                "Type":      "Price Spike Down",
                "Value":     "{:+.2f}%".format(ret_today*100),
                "Z-Score":   round(ret_zscore, 2),
                "Close":     "{:,.2f}".format(float(latest["Close"])),
                "Signal":    str(latest.get("Signal","N/A")),
                "Severity":  "Extreme" if ret_zscore < -4 else
                             "High"    if ret_zscore < -3 else
                             "Medium",
                "_sort":     abs(ret_zscore)
            })

    if "Volume Spike" in anomaly_type:
        if vol_zscore > zscore_threshold:
            anomaly_rows.append({
                "Ticker":    ticker_clean,
                "Date":      str(latest["Date"].date()),
                "Type":      "Volume Spike",
                "Value":     "{:,.0f}".format(vol_today),
                "Z-Score":   round(vol_zscore, 2),
                "Close":     "{:,.2f}".format(float(latest["Close"])),
                "Signal":    str(latest.get("Signal","N/A")),
                "Severity":  "Extreme" if vol_zscore > 4 else
                             "High"    if vol_zscore > 3 else
                             "Medium",
                "_sort":     abs(vol_zscore)
            })

total_anomalies = len(anomaly_rows)
extreme_count   = len([r for r in anomaly_rows if r["Severity"]=="Extreme"])
high_count      = len([r for r in anomaly_rows if r["Severity"]=="High"])
price_up_count  = len([r for r in anomaly_rows if r["Type"]=="Price Spike Up"])
vol_count       = len([r for r in anomaly_rows if r["Type"]=="Volume Spike"])

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total Anomalies",  total_anomalies)
c2.metric("Extreme Severity", extreme_count)
c3.metric("High Severity",    high_count)
c4.metric("Price Spikes Up",  price_up_count)
c5.metric("Volume Spikes",    vol_count)

st.markdown("---")

if not anomaly_rows:
    st.success(
        "No anomalies detected with Z-Score threshold "
        + str(zscore_threshold) +
        ". Markets are moving normally today."
    )
else:
    anomaly_df = pd.DataFrame(anomaly_rows).sort_values(
        "_sort", ascending=False
    ).drop(columns=["_sort"])

    st.subheader(
        "Detected Anomalies — " +
        str(max_date.date()) +
        " (sorted by Z-Score)"
    )

    def color_row(row):
        styles = []
        for col in row.index:
            if col == "Severity":
                if row[col] == "Extreme":
                    styles.append(
                        "background-color:#FFCCCC;"
                        "color:#8B0000;font-weight:bold"
                    )
                elif row[col] == "High":
                    styles.append(
                        "background-color:#FFE4CC;"
                        "color:#D62728"
                    )
                else:
                    styles.append(
                        "background-color:#FFFFCC;"
                        "color:#FF7F0E"
                    )
            elif col == "Type":
                if row[col] == "Price Spike Up":
                    styles.append("color:#2CA02C;font-weight:bold")
                elif row[col] == "Price Spike Down":
                    styles.append("color:#D62728;font-weight:bold")
                else:
                    styles.append("color:#1F77B4;font-weight:bold")
            else:
                styles.append("")
        return styles

    styled = anomaly_df.style.apply(color_row, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.subheader("Z-Score Chart — How Extreme is Each Anomaly?")
    top15 = anomaly_df.head(15).copy()
    bar_colors = []
    for _, row in top15.iterrows():
        if row["Type"] == "Price Spike Up":
            bar_colors.append("#2CA02C")
        elif row["Type"] == "Price Spike Down":
            bar_colors.append("#D62728")
        else:
            bar_colors.append("#1F77B4")

    fig_bar = go.Figure(go.Bar(
        x=top15["Ticker"],
        y=top15["Z-Score"].abs(),
        marker_color=bar_colors,
        text=top15["Type"],
        textposition="outside",
        textfont=dict(size=9)
    ))
    fig_bar.add_hline(
        y=float(zscore_threshold),
        line_dash="dash",
        line_color="gray",
        annotation_text="Threshold (" + str(zscore_threshold) + ")"
    )
    fig_bar.update_layout(
        height=350,
        template="plotly_white",
        xaxis_title="Stock",
        yaxis_title="Absolute Z-Score",
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Historical View — Inspect One Stock")
    anomaly_tickers = sorted(anomaly_df["Ticker"].unique().tolist())
    selected_ticker = st.selectbox(
        "Select stock to inspect",
        anomaly_tickers,
        index=0
    )

    full_ticker = selected_ticker + ".NS"
    stock_hist  = df[
        (df["Ticker"] == full_ticker) &
        (df["Date"]   >= cutoff)
    ].sort_values("Date").copy()

    if not stock_hist.empty:
        col_l, col_r = st.columns(2)

        with col_l:
            ret_mean_h = float(stock_hist["Daily_Return"].mean())
            ret_std_h  = float(stock_hist["Daily_Return"].std())

            if ret_std_h > 0:
                stock_hist["Return_ZScore"] = (
                    stock_hist["Daily_Return"] - ret_mean_h
                ) / ret_std_h

                anomaly_dates = stock_hist[
                    stock_hist["Return_ZScore"].abs() >
                    float(zscore_threshold)
                ]

                fig_ret = go.Figure()
                fig_ret.add_trace(go.Scatter(
                    x=stock_hist["Date"],
                    y=stock_hist["Daily_Return"] * 100,
                    name="Daily Return %",
                    line=dict(color="#1F77B4", width=1.5)
                ))
                if not anomaly_dates.empty:
                    fig_ret.add_trace(go.Scatter(
                        x=anomaly_dates["Date"],
                        y=anomaly_dates["Daily_Return"] * 100,
                        mode="markers",
                        marker=dict(
                            color="#D62728", size=10
                        ),
                        name="Anomaly Days"
                    ))
                fig_ret.add_hline(
                    y=0, line_color="black", line_width=0.8
                )
                fig_ret.update_layout(
                    height=300,
                    template="plotly_white",
                    title=selected_ticker + " — Returns with Anomalies",
                    yaxis_title="Return %",
                    legend=dict(orientation="h", y=1.02)
                )
                st.plotly_chart(fig_ret, use_container_width=True)

        with col_r:
            vol_mean_h = float(stock_hist["Volume"].mean())
            vol_std_h  = float(stock_hist["Volume"].std())

            if vol_std_h > 0:
                stock_hist["Volume_ZScore"] = (
                    stock_hist["Volume"] - vol_mean_h
                ) / vol_std_h

                vol_colors = [
                    "#D62728"
                    if float(z) > float(zscore_threshold)
                    else "#1F77B4"
                    for z in stock_hist["Volume_ZScore"].fillna(0)
                ]
                fig_vol = go.Figure(go.Bar(
                    x=stock_hist["Date"],
                    y=stock_hist["Volume"],
                    marker_color=vol_colors
                ))
                fig_vol.update_layout(
                    height=300,
                    template="plotly_white",
                    title=selected_ticker + " — Volume (Red=Anomaly)",
                    yaxis_title="Volume",
                    showlegend=False
                )
                st.plotly_chart(fig_vol, use_container_width=True)

st.markdown("---")
st.subheader("How Anomaly Detection Works")
st.markdown("""
**Z-Score:** `Z = (Today Value - Historical Mean) / Std Deviation`

| Z-Score | Meaning | Action |
|---|---|---|
| Above 4.0 | Extreme — 1 in 15,000 chance | Investigate immediately |
| 3.0 to 4.0 | High — very unusual | Watch closely |
| 2.5 to 3.0 | Medium — somewhat unusual | Monitor |
| Below 2.5 | Normal | No action needed |

Volume spikes often precede news events by hours — early detection gives you an informational edge.
""")
