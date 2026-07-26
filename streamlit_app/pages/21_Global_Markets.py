import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical

st.set_page_config(
    page_title="Global Markets",
    page_icon="🌐",
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
    '<h2 style="margin:0">🌐 Global Market Correlation Dashboard</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'How NIFTY 50 moves with global indices and commodities — '
    'live data updated daily'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

GLOBAL_ASSETS = {
    "S&P 500 (USA)":        {"ticker": "^GSPC",    "category": "Equity",    "country": "USA"},
    "Nasdaq (USA Tech)":    {"ticker": "^IXIC",    "category": "Equity",    "country": "USA"},
    "Dow Jones (USA)":      {"ticker": "^DJI",     "category": "Equity",    "country": "USA"},
    "FTSE 100 (UK)":        {"ticker": "^FTSE",    "category": "Equity",    "country": "UK"},
    "DAX (Germany)":        {"ticker": "^GDAXI",   "category": "Equity",    "country": "Germany"},
    "Nikkei 225 (Japan)":   {"ticker": "^N225",    "category": "Equity",    "country": "Japan"},
    "Hang Seng (HK)":       {"ticker": "^HSI",     "category": "Equity",    "country": "Hong Kong"},
    "Shanghai (China)":     {"ticker": "000001.SS","category": "Equity",    "country": "China"},
    "Crude Oil (WTI)":      {"ticker": "CL=F",     "category": "Commodity", "country": "Global"},
    "Crude Oil (Brent)":    {"ticker": "BZ=F",     "category": "Commodity", "country": "Global"},
    "Gold":                 {"ticker": "GC=F",     "category": "Commodity", "country": "Global"},
    "Silver":               {"ticker": "SI=F",     "category": "Commodity", "country": "Global"},
    "USD/INR":              {"ticker": "USDINR=X", "category": "Currency",  "country": "India"},
    "US Dollar Index":      {"ticker": "DX-Y.NYB", "category": "Currency",  "country": "Global"},
    "US 10Y Bond Yield":    {"ticker": "^TNX",     "category": "Bond",      "country": "USA"},
    "VIX (Fear Index)":     {"ticker": "^VIX",     "category": "Volatility","country": "Global"},
}

NIFTY_PROXY = "^NSEI"

st.sidebar.header("Controls")
period = st.sidebar.selectbox(
    "Analysis Period",
    ["1 Month","3 Months","6 Months","1 Year"],
    index=1
)
days_map = {
    "1 Month": "1mo",
    "3 Months":"3mo",
    "6 Months":"6mo",
    "1 Year":  "1y"
}
yf_period = days_map[period]

category_filter = st.sidebar.multiselect(
    "Filter by Category",
    ["Equity","Commodity","Currency","Bond","Volatility"],
    default=["Equity","Commodity","Currency"]
)


@st.cache_data(ttl=3600)
def fetch_global_data(period_str):
    all_data = {}
    tickers_to_fetch = [NIFTY_PROXY] + [
        v["ticker"] for v in GLOBAL_ASSETS.values()
    ]

    for ticker in tickers_to_fetch:
        try:
            data = yf.Ticker(ticker).history(period=period_str)
            if not data.empty:
                data.index = pd.to_datetime(data.index)
                if data.index.tz is not None:
                    data.index = data.index.tz_localize(None)
                all_data[ticker] = data["Close"]
        except Exception:
            pass

    return all_data


with st.spinner("Fetching global market data..."):
    raw_data = fetch_global_data(yf_period)

if not raw_data:
    st.error(
        "Could not fetch global market data. "
        "Please try again later."
    )
    st.stop()

nifty_data = raw_data.get(NIFTY_PROXY, pd.Series())

filtered_assets = {
    k: v for k, v in GLOBAL_ASSETS.items()
    if not category_filter or v["category"] in category_filter
}

snapshot_rows = []
for name, info in GLOBAL_ASSETS.items():
    ticker = info["ticker"]
    series = raw_data.get(ticker, pd.Series())
    if series.empty or len(series) < 2:
        continue

    curr  = float(series.iloc[-1])
    prev  = float(series.iloc[-2])
    chg   = round((curr - prev) / prev * 100, 2)
    start = float(series.iloc[0])
    period_chg = round((curr - start) / start * 100, 2)

    snapshot_rows.append({
        "Market":        name,
        "Category":      info["category"],
        "Country":       info["country"],
        "Latest":        round(curr, 2),
        "1-Day Change %":chg,
        period + " Change %": period_chg
    })

snapshot_df = pd.DataFrame(snapshot_rows)

if not snapshot_df.empty:
    pos_today = int((snapshot_df["1-Day Change %"] > 0).sum())
    neg_today = int((snapshot_df["1-Day Change %"] < 0).sum())
    avg_day   = round(float(snapshot_df["1-Day Change %"].mean()), 2)

    nifty_today = 0.0
    if not nifty_data.empty and len(nifty_data) >= 2:
        nifty_today = round(
            (float(nifty_data.iloc[-1]) -
             float(nifty_data.iloc[-2])) /
            float(nifty_data.iloc[-2]) * 100, 2
        )

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric(
        "NIFTY 50 Today",
        "{:+.2f}%".format(nifty_today),
        delta="{:+.2f}%".format(nifty_today)
    )
    kc2.metric("Global Markets Up", str(pos_today))
    kc3.metric("Global Markets Down", str(neg_today))
    kc4.metric(
        "Avg Global Change",
        "{:+.2f}%".format(avg_day)
    )

st.markdown("---")

tab1, tab2, tab3 = st.tabs([
    "📊 Market Snapshot",
    "🔗 Correlation Heatmap",
    "📈 Performance Chart"
])

with tab1:
    st.subheader("Global Market Snapshot")

    if not snapshot_df.empty:
        period_col = period + " Change %"
        display_df = snapshot_df.copy()

        fig_snap = go.Figure()

        categories = display_df["Category"].unique()
        colors_by_cat = {
            "Equity":     "#1F77B4",
            "Commodity":  "#FF7F0E",
            "Currency":   "#9467BD",
            "Bond":       "#2CA02C",
            "Volatility": "#D62728"
        }

        for cat in categories:
            cat_df = display_df[display_df["Category"] == cat]
            if period_col not in cat_df.columns:
                continue
            bar_colors = [
                "#2CA02C" if float(v) >= 0 else "#D62728"
                for v in cat_df[period_col]
            ]
            fig_snap.add_trace(go.Bar(
                x=cat_df["Market"],
                y=cat_df[period_col],
                name=cat,
                marker_color=bar_colors,
                text=["{:+.1f}%".format(float(v))
                      for v in cat_df[period_col]],
                textposition="outside"
            ))

        fig_snap.add_hline(y=0, line_color="black", line_width=1)
        fig_snap.update_layout(
            height=450,
            template="plotly_white",
            title="Global Market Returns — " + period,
            yaxis_title="Return %",
            xaxis_tickangle=-30,
            showlegend=True,
            legend=dict(orientation="h", y=1.02)
        )
        st.plotly_chart(fig_snap, use_container_width=True)

        st.subheader("Market Data Table")
        if period_col in display_df.columns:
            disp_sorted = display_df.sort_values(
                period_col, ascending=False
            )
        else:
            disp_sorted = display_df

        st.dataframe(
            disp_sorted.reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )

with tab2:
    st.subheader("Correlation with NIFTY 50")

    if nifty_data.empty:
        st.warning("NIFTY data not available for correlation.")
    else:
        nifty_returns = nifty_data.pct_change().dropna()
        corr_rows     = []

        for name, info in filtered_assets.items():
            ticker = info["ticker"]
            series = raw_data.get(ticker, pd.Series())
            if series.empty or len(series) < 10:
                continue

            asset_returns = series.pct_change().dropna()
            aligned = pd.DataFrame({
                "nifty": nifty_returns,
                "asset": asset_returns
            }).dropna()

            if len(aligned) < 5:
                continue

            corr = float(aligned.corr().loc["nifty","asset"])
            corr_rows.append({
                "Market":    name,
                "Category":  info["category"],
                "Country":   info["country"],
                "Correlation with NIFTY": round(corr, 3)
            })

        if corr_rows:
            corr_df = pd.DataFrame(corr_rows).sort_values(
                "Correlation with NIFTY", ascending=True
            )

            corr_colors = [
                "#D62728" if float(c) < -0.3 else
                "#FF7F0E" if float(c) < 0 else
                "#90EE90" if float(c) < 0.5 else
                "#2CA02C"
                for c in corr_df["Correlation with NIFTY"]
            ]

            fig_corr = go.Figure(go.Bar(
                x=corr_df["Correlation with NIFTY"],
                y=corr_df["Market"],
                orientation="h",
                marker_color=corr_colors,
                text=["{:.3f}".format(float(v))
                      for v in corr_df["Correlation with NIFTY"]],
                textposition="outside"
            ))
            fig_corr.add_vline(x=0, line_color="black", line_width=1)
            fig_corr.add_vline(
                x=0.5, line_dash="dash",
                line_color="#2CA02C",
                annotation_text="High positive"
            )
            fig_corr.add_vline(
                x=-0.3, line_dash="dash",
                line_color="#D62728",
                annotation_text="Inverse"
            )
            fig_corr.update_layout(
                height=500,
                template="plotly_white",
                title="Correlation with NIFTY 50 — " + period,
                xaxis_title="Correlation Coefficient (-1 to +1)",
                xaxis_range=[-1.1, 1.1]
            )
            st.plotly_chart(fig_corr, use_container_width=True)

            st.markdown("**What the correlations mean:**")
            st.markdown("""
| Correlation | Meaning | Trading Implication |
|---|---|---|
| 0.7 to 1.0 | Highly correlated | Moves together — when S&P 500 rises NIFTY follows |
| 0.3 to 0.7 | Moderately correlated | General trend alignment but with divergences |
| -0.3 to 0.3 | Low correlation | Independent movement |
| -0.3 to -1.0 | Inverse correlation | Opposite movement — gold often rises when stocks fall |
            """)

with tab3:
    st.subheader("Normalized Performance Comparison")
    st.caption(
        "All assets normalized to 100 at start of period "
        "for direct comparison"
    )

    selected_for_chart = st.multiselect(
        "Select markets to compare",
        list(GLOBAL_ASSETS.keys()),
        default=[
            k for k in list(GLOBAL_ASSETS.keys())
            if GLOBAL_ASSETS[k]["category"] in ["Equity","Commodity"]
        ][:6]
    )

    fig_perf = go.Figure()

    if not nifty_data.empty:
        norm_nifty = nifty_data / float(nifty_data.iloc[0]) * 100
        fig_perf.add_trace(go.Scatter(
            x=norm_nifty.index,
            y=norm_nifty.values,
            name="NIFTY 50",
            line=dict(color="#FF7F0E", width=3)
        ))

    CHART_COLORS = [
        "#1F77B4","#2CA02C","#D62728","#9467BD",
        "#8C564B","#E377C2","#17BECF","#BCBD22"
    ]

    for idx, name in enumerate(selected_for_chart):
        ticker = GLOBAL_ASSETS[name]["ticker"]
        series = raw_data.get(ticker, pd.Series())
        if series.empty or len(series) < 2:
            continue
        norm = series / float(series.iloc[0]) * 100
        fig_perf.add_trace(go.Scatter(
            x=norm.index,
            y=norm.values,
            name=name,
            line=dict(
                color=CHART_COLORS[idx % len(CHART_COLORS)],
                width=1.5
            )
        ))

    fig_perf.add_hline(
        y=100,
        line_dash="dot",
        line_color="gray",
        annotation_text="Start (100)"
    )
    fig_perf.update_layout(
        height=500,
        template="plotly_white",
        title="Normalized Performance — " + period + " (Base=100)",
        xaxis_title="Date",
        yaxis_title="Normalized Value (Base=100)",
        legend=dict(orientation="h", y=1.02)
    )
    st.plotly_chart(fig_perf, use_container_width=True)
