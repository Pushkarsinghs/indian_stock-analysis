import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical

st.set_page_config(
    page_title="Options Chain",
    page_icon="⛓️",
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
    '<h2 style="margin:0">⛓️ Options Chain Analysis</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Put/Call Ratio · Max Pain · Open Interest · '
    'Implied Volatility — live from NSE'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

NIFTY_SYMBOLS = [
    "NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK",
    "INFY", "ICICIBANK", "HINDUNILVR", "ITC", "SBIN",
    "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK",
    "ASIANPAINT", "MARUTI", "SUNPHARMA", "TITAN",
    "BAJFINANCE", "WIPRO", "ONGC", "NTPC", "TECHM",
    "HCLTECH", "TATASTEEL", "TATAMOTORS", "NESTLEIND",
    "DRREDDY", "CIPLA", "COALINDIA", "ADANIENT",
    "BAJAJFINSV", "HEROMOTOCO", "HINDALCO", "UPL",
    "APOLLOHOSP", "INDUSINDBK"
]

st.sidebar.header("Controls")
symbol = st.sidebar.selectbox("Select Symbol", NIFTY_SYMBOLS, index=0)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Data Source:** NSE India (live)\n\n"
    "Options data updates during market hours "
    "(9:15 AM to 3:30 PM IST)"
)


def fetch_nse_options(sym):
    if sym in ["NIFTY", "BANKNIFTY"]:
        url = (
            "https://www.nseindia.com/api/option-chain-indices"
            "?symbol=" + sym
        )
    else:
        url = (
            "https://www.nseindia.com/api/option-chain-equities"
            "?symbol=" + sym
        )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
        "Referer":         "https://www.nseindia.com/",
    }
    try:
        session = requests.Session()
        session.get(
            "https://www.nseindia.com",
            headers=headers, timeout=5
        )
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def parse_options_data(data):
    if not data or "records" not in data:
        return None, None, []
    records      = data["records"]
    expiry_dates = records.get("expiryDates", [])
    underlying   = records.get("underlyingValue", 0)
    raw_data     = records.get("data", [])
    rows = []
    for record in raw_data:
        strike  = record.get("strikePrice", 0)
        expiry  = record.get("expiryDate", "")
        ce_data = record.get("CE", {})
        pe_data = record.get("PE", {})
        rows.append({
            "Strike":    strike,
            "Expiry":    expiry,
            "CE_OI":     ce_data.get("openInterest",           0),
            "CE_Chg_OI": ce_data.get("changeinOpenInterest",   0),
            "CE_Volume": ce_data.get("totalTradedVolume",      0),
            "CE_IV":     ce_data.get("impliedVolatility",      0),
            "CE_LTP":    ce_data.get("lastPrice",              0),
            "PE_OI":     pe_data.get("openInterest",           0),
            "PE_Chg_OI": pe_data.get("changeinOpenInterest",   0),
            "PE_Volume": pe_data.get("totalTradedVolume",      0),
            "PE_IV":     pe_data.get("impliedVolatility",      0),
            "PE_LTP":    pe_data.get("lastPrice",              0),
        })
    if not rows:
        return None, underlying, expiry_dates
    return pd.DataFrame(rows), underlying, expiry_dates


def compute_max_pain(options_df):
    strikes    = sorted(options_df["Strike"].unique())
    total_pain = []
    k_vals     = options_df["Strike"].values.astype(float)
    ce_oi_vals = options_df["CE_OI"].fillna(0).values.astype(float)
    pe_oi_vals = options_df["PE_OI"].fillna(0).values.astype(float)
    for s in strikes:
        s = float(s)
        call_pain = float(sum(
            max(0.0, s - k) * oi
            for k, oi in zip(k_vals, ce_oi_vals)
        ))
        put_pain = float(sum(
            max(0.0, k - s) * oi
            for k, oi in zip(k_vals, pe_oi_vals)
        ))
        total_pain.append({
            "Strike":     s,
            "Total_Pain": call_pain + put_pain
        })
    pain_df = pd.DataFrame(total_pain)
    if pain_df.empty:
        return 0.0
    return float(pain_df.loc[pain_df["Total_Pain"].idxmin(), "Strike"])


def build_synthetic_data(underlying_val, sym):
    atm_strike  = round(underlying_val / 50) * 50
    strikes     = list(range(
        int(atm_strike - 500),
        int(atm_strike + 550),
        50
    ))
    expiry_dates = ["31-Jul-2026", "07-Aug-2026", "14-Aug-2026"]
    np.random.seed(42)
    rows = []
    for strike in strikes:
        dist      = abs(strike - underlying_val)
        moneyness = dist / max(underlying_val, 1)
        base_ce   = max(0, int(
            np.random.normal(500000, 150000) * (1 - moneyness * 3)
        ))
        base_pe   = max(0, int(
            np.random.normal(450000, 130000) *
            (1 + (atm_strike - strike) / max(atm_strike, 1) * 2)
        ))
        ce_iv = max(5.0, float(np.random.normal(15 + moneyness * 20, 2)))
        pe_iv = max(5.0, float(np.random.normal(16 + moneyness * 22, 2)))
        rows.append({
            "Strike":    float(strike),
            "Expiry":    expiry_dates[0],
            "CE_OI":     base_ce,
            "CE_Chg_OI": int(np.random.normal(10000, 30000)),
            "CE_Volume": int(abs(np.random.normal(50000, 20000))),
            "CE_IV":     round(ce_iv, 2),
            "CE_LTP":    max(0.05, round(
                max(0.0, underlying_val - strike) +
                float(np.random.exponential(50)), 2
            )),
            "PE_OI":     base_pe,
            "PE_Chg_OI": int(np.random.normal(-5000, 25000)),
            "PE_Volume": int(abs(np.random.normal(45000, 18000))),
            "PE_IV":     round(pe_iv, 2),
            "PE_LTP":    max(0.05, round(
                max(0.0, strike - underlying_val) +
                float(np.random.exponential(50)), 2
            )),
        })
    return pd.DataFrame(rows), expiry_dates


with st.spinner("Fetching live options data from NSE..."):
    data = fetch_nse_options(symbol)

is_live     = False
used_expiry = "Demo"

if data is None:
    st.warning(
        "Could not fetch live options data from NSE right now. "
        "NSE sometimes blocks automated requests outside market hours "
        "or from cloud servers. Showing a demo with synthetic data."
    )
    tech = load_technical()
    if tech.empty:
        st.error("No data available.")
        st.stop()
    tech["Date"] = pd.to_datetime(tech["Date"])
    ticker_map = {
        "RELIANCE":  "RELIANCE.NS",
        "TCS":       "TCS.NS",
        "HDFCBANK":  "HDFCBANK.NS",
        "INFY":      "INFY.NS",
        "ICICIBANK": "ICICIBANK.NS",
        "SBIN":      "SBIN.NS",
        "NIFTY":     "HDFCBANK.NS",
        "BANKNIFTY": "SBIN.NS"
    }
    mapped  = ticker_map.get(symbol, "RELIANCE.NS")
    stock   = tech[tech["Ticker"] == mapped].sort_values("Date")
    underlying = float(stock["Close"].iloc[-1]) if not stock.empty else 20000.0
    options_df, expiry_dates = build_synthetic_data(underlying, symbol)
    used_expiry = expiry_dates[0]
    st.info(
        "Showing **synthetic demo data** for " + symbol +
        " (underlying price: Rs" + "{:,.2f}".format(underlying) +
        "). Live data requires NSE access during market hours."
    )
else:
    options_df, underlying, expiry_dates = parse_options_data(data)
    if options_df is None or options_df.empty:
        st.error("Options data received but could not be parsed.")
        st.stop()
    is_live = True
    st.success(
        "Live NSE data loaded for **" + symbol +
        "** | Underlying: **Rs" +
        "{:,.2f}".format(float(underlying or 0)) + "**"
    )
    if expiry_dates:
        used_expiry = st.selectbox(
            "Select Expiry Date", expiry_dates, index=0
        )
        options_df = options_df[
            options_df["Expiry"] == used_expiry
        ].copy()
    else:
        used_expiry = "N/A"

options_df = options_df.sort_values("Strike").reset_index(drop=True)
for col in ["CE_OI", "PE_OI", "CE_Volume", "PE_Volume"]:
    if col in options_df.columns:
        options_df[col] = options_df[col].fillna(0)

total_ce_oi = float(options_df["CE_OI"].sum())
total_pe_oi = float(options_df["PE_OI"].sum())
pcr         = round(total_pe_oi / total_ce_oi, 3) if total_ce_oi > 0 else 0.0

max_pain_strike = compute_max_pain(options_df)

underlying_val = float(underlying or options_df["Strike"].median())

atm_row = options_df.iloc[
    (options_df["Strike"] - underlying_val).abs().argsort()[:1]
]
atm_ce_iv = float(atm_row["CE_IV"].values[0]) if not atm_row.empty else 0.0
atm_pe_iv = float(atm_row["PE_IV"].values[0]) if not atm_row.empty else 0.0
atm_iv    = round((atm_ce_iv + atm_pe_iv) / 2, 2)

if pcr > 1.2:
    pcr_signal = "Extremely Bearish"
    pcr_color  = "#8B0000"
elif pcr > 0.9:
    pcr_signal = "Moderately Bearish"
    pcr_color  = "#D62728"
elif pcr > 0.7:
    pcr_signal = "Neutral"
    pcr_color  = "#FF7F0E"
elif pcr > 0.5:
    pcr_signal = "Moderately Bullish"
    pcr_color  = "#2CA02C"
else:
    pcr_signal = "Extremely Bullish"
    pcr_color  = "#1A7A1A"

kc1, kc2, kc3, kc4, kc5 = st.columns(5)
kc1.metric(
    "Underlying Price",
    "Rs" + "{:,.2f}".format(underlying_val)
)
kc2.metric("Put/Call Ratio", str(pcr))
kc3.metric("PCR Signal",     pcr_signal)
kc4.metric(
    "Max Pain Strike",
    "Rs" + "{:,.0f}".format(max_pain_strike)
)
kc5.metric("ATM IV", str(atm_iv) + "%")

st.markdown(
    '<div style="background:' + pcr_color + '22;'
    'border-left:5px solid ' + pcr_color + ';'
    'padding:12px;border-radius:8px;margin:15px 0;">'
    '<b style="color:' + pcr_color + '">Market Sentiment: ' +
    pcr_signal + '</b><br>'
    'PCR of ' + str(pcr) + ' indicates ' +
    (
        "more PUT buying — market participants are hedging downside."
        if pcr > 1 else
        "more CALL buying — market participants are bullish on upside."
    ) +
    '</div>',
    unsafe_allow_html=True
)

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Open Interest",
    "🎯 Max Pain",
    "📈 Implied Volatility",
    "📋 Full Chain"
])

with tab1:
    st.subheader("Open Interest — Where is Big Money Positioned?")

    nearby = options_df[
        (options_df["Strike"] >= underlying_val * 0.92) &
        (options_df["Strike"] <= underlying_val * 1.08)
    ].copy()
    if len(nearby) < 5:
        nearby = options_df.copy()

    fig_oi = go.Figure()
    fig_oi.add_trace(go.Bar(
        x=nearby["Strike"],
        y=nearby["CE_OI"],
        name="Call OI",
        marker_color="#D62728",
        opacity=0.85
    ))
    fig_oi.add_trace(go.Bar(
        x=nearby["Strike"],
        y=nearby["PE_OI"],
        name="Put OI",
        marker_color="#2CA02C",
        opacity=0.85
    ))
    fig_oi.add_vline(
        x=underlying_val,
        line_dash="dash",
        line_color="#1F3864",
        line_width=2,
        annotation_text="Current Price"
    )
    fig_oi.add_vline(
        x=float(max_pain_strike),
        line_dash="dot",
        line_color="#FF7F0E",
        line_width=2,
        annotation_text="Max Pain"
    )
    fig_oi.update_layout(
        height=450,
        template="plotly_white",
        barmode="group",
        title="Call vs Put Open Interest by Strike",
        xaxis_title="Strike Price (Rs)",
        yaxis_title="Open Interest (Contracts)",
        legend=dict(orientation="h", y=1.02)
    )
    st.plotly_chart(fig_oi, use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Top 5 Call OI Strikes — Resistance Levels**")
        top_ce = options_df.nlargest(5, "CE_OI")[
            ["Strike", "CE_OI", "CE_IV", "CE_LTP"]
        ].copy()
        top_ce.columns = ["Strike", "Call OI", "Call IV %", "Call LTP"]
        st.dataframe(top_ce, use_container_width=True, hide_index=True)
        st.caption(
            "High Call OI = resistance zone. "
            "Market makers want price to stay below these strikes."
        )
    with col_r:
        st.markdown("**Top 5 Put OI Strikes — Support Levels**")
        top_pe = options_df.nlargest(5, "PE_OI")[
            ["Strike", "PE_OI", "PE_IV", "PE_LTP"]
        ].copy()
        top_pe.columns = ["Strike", "Put OI", "Put IV %", "Put LTP"]
        st.dataframe(top_pe, use_container_width=True, hide_index=True)
        st.caption(
            "High Put OI = support zone. "
            "Market makers want price to stay above these strikes."
        )

with tab2:
    st.subheader("Max Pain Analysis")
    st.markdown(
        "**Max Pain Theory:** At expiry, the underlying price "
        "tends to gravitate toward the strike where the "
        "maximum number of options expire worthless."
    )

    k_vals     = options_df["Strike"].values.astype(float)
    ce_oi_vals = options_df["CE_OI"].fillna(0).values.astype(float)
    pe_oi_vals = options_df["PE_OI"].fillna(0).values.astype(float)

    pain_rows    = []
    strikes_list = sorted(options_df["Strike"].unique())

    for s in strikes_list:
        s = float(s)
        ce_pain = float(sum(
            max(0.0, s - k) * oi
            for k, oi in zip(k_vals, ce_oi_vals)
        ))
        put_pain = float(sum(
            max(0.0, k - s) * oi
            for k, oi in zip(k_vals, pe_oi_vals)
        ))
        pain_rows.append({
            "Strike":     s,
            "Call_Pain":  ce_pain,
            "Put_Pain":   put_pain,
            "Total_Pain": ce_pain + put_pain
        })

    pain_df = pd.DataFrame(pain_rows)

    if not pain_df.empty:
        min_pain_strike = float(
            pain_df.loc[pain_df["Total_Pain"].idxmin(), "Strike"]
        )

        fig_pain = go.Figure()
        fig_pain.add_trace(go.Scatter(
            x=pain_df["Strike"],
            y=pain_df["Total_Pain"],
            name="Total Pain Value",
            line=dict(color="#1F3864", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(31,56,100,0.1)"
        ))
        fig_pain.add_vline(
            x=min_pain_strike,
            line_dash="dash",
            line_color="#FF7F0E",
            line_width=3,
            annotation_text="Max Pain = Rs" +
                            "{:,.0f}".format(min_pain_strike),
            annotation_position="top right",
            annotation_font_color="#FF7F0E"
        )
        fig_pain.add_vline(
            x=underlying_val,
            line_dash="dot",
            line_color="#D62728",
            line_width=2,
            annotation_text="Current Price",
            annotation_position="top left"
        )
        fig_pain.update_layout(
            height=400,
            template="plotly_white",
            title="Max Pain Chart — Min Total Pain at Rs" +
                  "{:,.0f}".format(min_pain_strike),
            xaxis_title="Strike Price (Rs)",
            yaxis_title="Total Pain Value (Rs)"
        )
        st.plotly_chart(fig_pain, use_container_width=True)

        distance  = underlying_val - min_pain_strike
        dist_pct  = round(distance / max(underlying_val, 1) * 100, 2)

        if abs(dist_pct) < 1:
            dist_msg   = "Current price is very close to Max Pain. Expect sideways movement near expiry."
            dist_color = "#FF7F0E"
        elif distance > 0:
            dist_msg   = (
                "Current price is " + str(abs(dist_pct)) +
                "% ABOVE Max Pain. Selling pressure may push price "
                "toward Rs" + "{:,.0f}".format(min_pain_strike) +
                " near expiry."
            )
            dist_color = "#D62728"
        else:
            dist_msg   = (
                "Current price is " + str(abs(dist_pct)) +
                "% BELOW Max Pain. Buying pressure may push price "
                "toward Rs" + "{:,.0f}".format(min_pain_strike) +
                " near expiry."
            )
            dist_color = "#2CA02C"

        st.markdown(
            '<div style="background:' + dist_color + '22;'
            'border-left:5px solid ' + dist_color + ';'
            'padding:12px;border-radius:8px;">'
            '<b style="color:' + dist_color +
            '">Max Pain Analysis</b><br>' + dist_msg +
            '</div>',
            unsafe_allow_html=True
        )

with tab3:
    st.subheader("Implied Volatility Analysis")

    iv_df = options_df[
        (options_df["CE_IV"] > 0) | (options_df["PE_IV"] > 0)
    ].copy()

    if not iv_df.empty:
        valid_ce = iv_df[iv_df["CE_IV"] > 0]
        valid_pe = iv_df[iv_df["PE_IV"] > 0]

        fig_iv = go.Figure()
        if not valid_ce.empty:
            fig_iv.add_trace(go.Scatter(
                x=valid_ce["Strike"],
                y=valid_ce["CE_IV"],
                name="Call IV",
                line=dict(color="#D62728", width=2),
                mode="lines+markers",
                marker=dict(size=5)
            ))
        if not valid_pe.empty:
            fig_iv.add_trace(go.Scatter(
                x=valid_pe["Strike"],
                y=valid_pe["PE_IV"],
                name="Put IV",
                line=dict(color="#2CA02C", width=2),
                mode="lines+markers",
                marker=dict(size=5)
            ))
        fig_iv.add_vline(
            x=underlying_val,
            line_dash="dash",
            line_color="#1F3864",
            line_width=2,
            annotation_text="ATM"
        )
        fig_iv.update_layout(
            height=400,
            template="plotly_white",
            title="Implied Volatility Smile / Skew",
            xaxis_title="Strike Price (Rs)",
            yaxis_title="Implied Volatility (%)",
            legend=dict(orientation="h", y=1.02)
        )
        st.plotly_chart(fig_iv, use_container_width=True)

        iv_skew = atm_pe_iv - atm_ce_iv
        if iv_skew > 2:
            skew_msg   = "**Put skew detected** — Market is pricing in downside risk."
            skew_color = "#D62728"
        elif iv_skew < -2:
            skew_msg   = "**Call skew detected** — Market is pricing in upside breakout."
            skew_color = "#2CA02C"
        else:
            skew_msg   = "**Symmetric IV** — Market is balanced between upside and downside."
            skew_color = "#FF7F0E"

        st.markdown(
            '<div style="background:' + skew_color + '22;'
            'border-left:5px solid ' + skew_color + ';'
            'padding:12px;border-radius:8px;">'
            + skew_msg +
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")
        st.markdown("""
**What IV tells you:**

| IV Level | Interpretation | Strategy |
|---|---|---|
| Below 15% | Low volatility | Good time to buy options |
| 15% to 25% | Normal volatility | Standard strategies work |
| 25% to 40% | High volatility | Consider selling options |
| Above 40% | Extremely high | Avoid buying, sell spreads |
        """)
    else:
        st.info("No IV data available for this selection.")

with tab4:
    st.subheader("Full Options Chain")

    display_cols = [
        c for c in [
            "Strike", "CE_OI", "CE_Chg_OI", "CE_Volume",
            "CE_IV", "CE_LTP", "PE_LTP", "PE_IV",
            "PE_Volume", "PE_Chg_OI", "PE_OI"
        ] if c in options_df.columns
    ]
    display_chain = options_df[display_cols].copy()
    display_chain.columns = [
        "Strike", "CE OI", "CE Chg OI", "CE Vol",
        "CE IV%", "CE LTP", "PE LTP", "PE IV%",
        "PE Vol", "PE Chg OI", "PE OI"
    ][:len(display_chain.columns)]

    def highlight_atm(row):
        strike  = float(row["Strike"])
        is_atm  = abs(strike - underlying_val) <= 50
        base    = "background-color:#FFF3CD;font-weight:bold" if is_atm else ""
        return [base] * len(row)

    styled_chain = display_chain.style.apply(highlight_atm, axis=1)
    st.dataframe(
        styled_chain,
        use_container_width=True,
        hide_index=True,
        height=500
    )
    st.caption(
        "Yellow rows = ATM strikes. "
        "CE = Call. PE = Put. "
        "OI = Open Interest."
    )

st.markdown("---")
st.subheader("Options Concepts Guide")
st.markdown("""
**Put/Call Ratio (PCR):**
- PCR > 1.2 → Very bearish sentiment
- PCR 0.8 to 1.2 → Neutral
- PCR < 0.8 → Bullish sentiment

**Max Pain:** Strike where most options expire worthless.
Near expiry, prices often drift toward Max Pain.

**Open Interest:** High OI at a strike = strong support or resistance.

**Implied Volatility:** Market expectation of future movement.
High IV = expensive options. Low IV = cheap options.
""")
