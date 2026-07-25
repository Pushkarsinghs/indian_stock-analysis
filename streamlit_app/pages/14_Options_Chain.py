import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical, load_signals

st.set_page_config(
    page_title="Options Chain",
    page_icon="⛓️",
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
    '<h2 style="margin:0">⛓️ Options Chain Analysis</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Put/Call Ratio · Max Pain · Open Interest · '
    'Implied Volatility — live from NSE'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

NIFTY_SYMBOLS = [
    "NIFTY","BANKNIFTY","RELIANCE","TCS","HDFCBANK",
    "INFY","ICICIBANK","HINDUNILVR","ITC","SBIN",
    "BHARTIARTL","KOTAKBANK","LT","AXISBANK",
    "ASIANPAINT","MARUTI","SUNPHARMA","TITAN",
    "BAJFINANCE","WIPRO","ONGC","NTPC","TECHM",
    "HCLTECH","TATASTEEL","TATAMOTORS","NESTLEIND",
    "DRREDDY","CIPLA","COALINDIA","ADANIENT",
    "BAJAJFINSV","HEROMOTOCO","HINDALCO","UPL",
    "APOLLOHOSP","INDUSINDBK"
]

st.sidebar.header("Controls")
symbol = st.sidebar.selectbox(
    "Select Symbol",
    NIFTY_SYMBOLS,
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Data Source:** NSE India (live)\n\n"
    "Options data updates during market hours "
    "(9:15 AM to 3:30 PM IST)"
)

def fetch_nse_options(symbol):
    """
    Fetch options chain data from NSE India.
    Returns a dict with the options data or None on failure.
    """
    if symbol in ["NIFTY","BANKNIFTY"]:
        url = (
            "https://www.nseindia.com/api/option-chain-indices"
            "?symbol=" + symbol
        )
    else:
        url = (
            "https://www.nseindia.com/api/option-chain-equities"
            "?symbol=" + symbol
        )

    headers = {
        "User-Agent":      (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept":          (
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
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def parse_options_data(data):
    """
    Parse the NSE options JSON into a clean DataFrame.
    Returns (options_df, underlying_price, expiry_dates)
    """
    if not data or "records" not in data:
        return None, None, []

    records     = data["records"]
    expiry_dates = records.get("expiryDates", [])
    underlying  = records.get("underlyingValue", 0)
    raw_data    = records.get("data", [])

    rows = []
    for record in raw_data:
        strike = record.get("strikePrice", 0)
        expiry = record.get("expiryDate", "")

        ce_data = record.get("CE", {})
        pe_data = record.get("PE", {})

        row = {
            "Strike":     strike,
            "Expiry":     expiry,
            "CE_OI":      ce_data.get("openInterest",           0),
            "CE_Chg_OI":  ce_data.get("changeinOpenInterest",   0),
            "CE_Volume":  ce_data.get("totalTradedVolume",      0),
            "CE_IV":      ce_data.get("impliedVolatility",      0),
            "CE_LTP":     ce_data.get("lastPrice",              0),
            "CE_Bid":     ce_data.get("bidprice",               0),
            "CE_Ask":     ce_data.get("askPrice",               0),
            "PE_OI":      pe_data.get("openInterest",           0),
            "PE_Chg_OI":  pe_data.get("changeinOpenInterest",   0),
            "PE_Volume":  pe_data.get("totalTradedVolume",      0),
            "PE_IV":      pe_data.get("impliedVolatility",      0),
            "PE_LTP":     pe_data.get("lastPrice",              0),
            "PE_Bid":     pe_data.get("bidprice",               0),
            "PE_Ask":     pe_data.get("askPrice",               0),
        }
        rows.append(row)

    if not rows:
        return None, underlying, expiry_dates

    df = pd.DataFrame(rows)
    return df, underlying, expiry_dates


def compute_max_pain(options_df):
    """
    Computes the Max Pain strike price.
    Max Pain = strike where total option value is minimized.
    This is the price where most options expire worthless.
    """
    strikes = sorted(options_df["Strike"].unique())
    total_pain = []

    for s in strikes:
        call_pain = float(
            (options_df["Strike"].clip(upper=s) - s).clip(lower=0) *
            options_df["CE_OI"] * (-1)
        ).sum()
        call_pain = float(
            ((s - options_df["Strike"]).clip(lower=0) *
             options_df["CE_OI"]).sum()
        )
        put_pain = float(
            ((options_df["Strike"] - s).clip(lower=0) *
             options_df["PE_OI"]).sum()
        )
        total_pain.append({
            "Strike":     s,
            "Total_Pain": call_pain + put_pain
        })

    pain_df = pd.DataFrame(total_pain)
    if pain_df.empty:
        return 0
    max_pain_strike = float(
        pain_df.loc[pain_df["Total_Pain"].idxmin(), "Strike"]
    )
    return max_pain_strike


with st.spinner("Fetching live options data from NSE..."):
    data = fetch_nse_options(symbol)

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
    mapped = ticker_map.get(symbol, "RELIANCE.NS")
    stock  = tech[tech["Ticker"]==mapped].sort_values("Date")
    underlying = float(stock["Close"].iloc[-1]) \
                 if not stock.empty else 20000.0

    atm_strike   = round(underlying / 50) * 50
    strikes      = list(range(
        int(atm_strike - 500),
        int(atm_strike + 550),
        50
    ))
    expiry_dates = ["24-Jul-2026","31-Jul-2026","07-Aug-2026"]

    np.random.seed(42)
    rows = []
    for strike in strikes:
        dist = abs(strike - underlying)
        moneyness = dist / underlying

        base_ce_oi = max(0, int(
            np.random.normal(500000, 150000) *
            (1 - moneyness * 3)
        ))
        base_pe_oi = max(0, int(
            np.random.normal(450000, 130000) *
            (1 + (atm_strike - strike) / atm_strike * 2)
        ))
        ce_iv = max(5, float(np.random.normal(
            15 + moneyness * 20, 2
        )))
        pe_iv = max(5, float(np.random.normal(
            16 + moneyness * 22, 2
        )))

        rows.append({
            "Strike":    strike,
            "Expiry":    expiry_dates[0],
            "CE_OI":     base_ce_oi,
            "CE_Chg_OI": int(np.random.normal(10000, 30000)),
            "CE_Volume": int(abs(np.random.normal(50000, 20000))),
            "CE_IV":     round(ce_iv, 2),
            "CE_LTP":    max(0.05, round(
                max(0, underlying - strike) +
                float(np.random.exponential(50)), 2)),
            "CE_Bid":    0,
            "CE_Ask":    0,
            "PE_OI":     base_pe_oi,
            "PE_Chg_OI": int(np.random.normal(-5000, 25000)),
            "PE_Volume": int(abs(np.random.normal(45000, 18000))),
            "PE_IV":     round(pe_iv, 2),
            "PE_LTP":    max(0.05, round(
                max(0, strike - underlying) +
                float(np.random.exponential(50)), 2)),
            "PE_Bid":    0,
            "PE_Ask":    0,
        })

    options_df   = pd.DataFrame(rows)
    is_live      = False
    used_expiry  = expiry_dates[0]

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
            "Select Expiry Date",
            expiry_dates,
            index=0
        )
        options_df = options_df[
            options_df["Expiry"] == used_expiry
        ].copy()
    else:
        used_expiry = "N/A"

options_df = options_df.sort_values("Strike").reset_index(drop=True)
options_df[["CE_OI","PE_OI","CE_Volume","PE_Volume"]] = \
    options_df[["CE_OI","PE_OI","CE_Volume","PE_Volume"]].fillna(0)

total_ce_oi = float(options_df["CE_OI"].sum())
total_pe_oi = float(options_df["PE_OI"].sum())
pcr         = round(total_pe_oi / total_ce_oi, 3) \
              if total_ce_oi > 0 else 0.0

max_pain_strike = compute_max_pain(options_df)

atm_row = options_df.iloc[
    (options_df["Strike"] - float(underlying or 0)).abs().argsort()[:1]
]
atm_ce_iv = float(atm_row["CE_IV"].values[0]) \
            if not atm_row.empty else 0.0
atm_pe_iv = float(atm_row["PE_IV"].values[0]) \
            if not atm_row.empty else 0.0
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
    "Rs" + "{:,.2f}".format(float(underlying or 0))
)
kc2.metric("Put/Call Ratio", str(pcr))
kc3.metric("PCR Signal",     pcr_signal)
kc4.metric("Max Pain Strike","Rs" + "{:,.0f}".format(max_pain_strike))
kc5.metric("ATM IV",         str(atm_iv) + "%")

st.markdown(
    '<div style="background:' + pcr_color + '22;'
    'border-left:5px solid ' + pcr_color + ';'
    'padding:12px;border-radius:8px;margin:15px 0;">'
    '<b style="color:' + pcr_color + '">Market Sentiment: ' +
    pcr_signal + '</b><br>'
    'PCR of ' + str(pcr) +
    ' indicates ' + (
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

    filter_strikes = 15
    underlying_val = float(underlying or options_df["Strike"].median())
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
        x=float(underlying_val),
        line_dash="dash",
        line_color="#1F3864",
        line_width=2,
        annotation_text="Current Price",
        annotation_position="top right"
    )
    fig_oi.add_vline(
        x=float(max_pain_strike),
        line_dash="dot",
        line_color="#FF7F0E",
        line_width=2,
        annotation_text="Max Pain",
        annotation_position="top left"
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
            ["Strike","CE_OI","CE_IV","CE_LTP"]
        ].copy()
        top_ce.columns = [
            "Strike","Call OI","Call IV %","Call LTP"
        ]
        st.dataframe(
            top_ce, use_container_width=True, hide_index=True
        )
        st.caption(
            "High Call OI = resistance zone. "
            "Market makers want price to stay below these strikes."
        )

    with col_r:
        st.markdown("**Top 5 Put OI Strikes — Support Levels**")
        top_pe = options_df.nlargest(5, "PE_OI")[
            ["Strike","PE_OI","PE_IV","PE_LTP"]
        ].copy()
        top_pe.columns = [
            "Strike","Put OI","Put IV %","Put LTP"
        ]
        st.dataframe(
            top_pe, use_container_width=True, hide_index=True
        )
        st.caption(
            "High Put OI = support zone. "
            "Market makers want price to stay above these strikes."
        )

with tab2:
    st.subheader("Max Pain Analysis")
    st.markdown(
        "**Max Pain Theory:** At expiry, the underlying price "
        "tends to gravitate toward the strike where the "
        "maximum number of options expire worthless. "
        "This benefits option sellers (usually institutional players)."
    )

    pain_rows = []
    strikes_list = sorted(options_df["Strike"].unique())

    for s in strikes_list:
        ce_pain = float(
            ((s - options_df["Strike"]).clip(lower=0) *
             options_df["CE_OI"]).sum()
        )
        pe_pain = float(
            ((options_df["Strike"] - s).clip(lower=0) *
             options_df["PE_OI"]).sum()
        )
        pain_rows.append({
            "Strike":     float(s),
            "Call_Pain":  ce_pain,
            "Put_Pain":   pe_pain,
            "Total_Pain": ce_pain + pe_pain
        })

    pain_df = pd.DataFrame(pain_rows)

    if not pain_df.empty:
        fig_pain = go.Figure()
        fig_pain.add_trace(go.Scatter(
            x=pain_df["Strike"],
            y=pain_df["Total_Pain"],
            name="Total Pain Value",
            line=dict(color="#1F3864", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(31,56,100,0.1)"
        ))

        min_pain_strike = float(
            pain_df.loc[
                pain_df["Total_Pain"].idxmin(), "Strike"
            ]
        )
        min_pain_val = float(pain_df["Total_Pain"].min())

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
            x=float(underlying_val),
            line_dash="dot",
            line_color="#D62728",
            line_width=2,
            annotation_text="Current Price",
            annotation_position="top left"
        )

        fig_pain.update_layout(
            height=400,
            template="plotly_white",
            title="Max Pain Chart — Lowest Total Pain = Rs" +
                  "{:,.0f}".format(min_pain_strike),
            xaxis_title="Strike Price (Rs)",
            yaxis_title="Total Pain Value (Rs)"
        )
        st.plotly_chart(fig_pain, use_container_width=True)

        distance = float(underlying_val) - float(min_pain_strike)
        dist_pct  = round(distance / float(underlying_val) * 100, 2)

        if abs(dist_pct) < 1:
            dist_msg = (
                "Current price is very close to Max Pain. "
                "Expect sideways movement near expiry."
            )
            dist_color = "#FF7F0E"
        elif distance > 0:
            dist_msg = (
                "Current price is " + str(abs(dist_pct)) +
                "% ABOVE Max Pain. "
                "Selling pressure may push price down toward Rs" +
                "{:,.0f}".format(min_pain_strike) + " near expiry."
            )
            dist_color = "#D62728"
        else:
            dist_msg = (
                "Current price is " + str(abs(dist_pct)) +
                "% BELOW Max Pain. "
                "Buying pressure may push price up toward Rs" +
                "{:,.0f}".format(min_pain_strike) + " near expiry."
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
        (options_df["CE_IV"] > 0) |
        (options_df["PE_IV"] > 0)
    ].copy()

    if not iv_df.empty:
        fig_iv = go.Figure()
        valid_ce = iv_df[iv_df["CE_IV"] > 0]
        valid_pe = iv_df[iv_df["PE_IV"] > 0]

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
            x=float(underlying_val),
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

        st.markdown("**Volatility Interpretation**")

        iv_skew = atm_pe_iv - atm_ce_iv
        if iv_skew > 2:
            skew_msg = (
                "**Put skew detected** (Put IV > Call IV by " +
                str(round(iv_skew, 1)) + "%) — "
                "Market is pricing in downside risk. "
                "Institutional players are buying protection."
            )
            skew_color = "#D62728"
        elif iv_skew < -2:
            skew_msg = (
                "**Call skew detected** (Call IV > Put IV by " +
                str(round(abs(iv_skew), 1)) + "%) — "
                "Market is pricing in upside breakout. "
                "Players are positioning for a rally."
            )
            skew_color = "#2CA02C"
        else:
            skew_msg = (
                "**Symmetric IV** — market is balanced between "
                "upside and downside expectations."
            )
            skew_color = "#FF7F0E"

        st.markdown(
            '<div style="background:' + skew_color + '22;'
            'border-left:5px solid ' + skew_color + ';'
            'padding:12px;border-radius:8px;">'
            '' + skew_msg +
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")
        st.markdown("**What IV tells you:**")
        st.markdown("""
| IV Level | Interpretation | Strategy |
|---|---|---|
| Below 15% | Low volatility — calm market | Good time to buy options |
| 15% to 25% | Normal volatility | Standard strategies work |
| 25% to 40% | High volatility — uncertain market | Consider selling options |
| Above 40% | Extremely high — major event expected | Avoid buying, sell spreads |
        """)

with tab4:
    st.subheader("Full Options Chain")

    display_chain = options_df[[
        "Strike","CE_OI","CE_Chg_OI","CE_Volume",
        "CE_IV","CE_LTP","PE_LTP","PE_IV",
        "PE_Volume","PE_Chg_OI","PE_OI"
    ]].copy()

    display_chain.columns = [
        "Strike",
        "CE OI","CE Chg OI","CE Vol",
        "CE IV%","CE LTP",
        "PE LTP","PE IV%",
        "PE Vol","PE Chg OI","PE OI"
    ]

    atm_val = float(underlying_val)

    def highlight_atm(row):
        strike = float(row["Strike"])
        styles = []
        is_atm = abs(strike - atm_val) <= 50
        for col in row.index:
            if is_atm:
                styles.append(
                    "background-color:#FFF3CD;"
                    "font-weight:bold"
                )
            else:
                styles.append("")
        return styles

    styled_chain = display_chain.style.apply(
        highlight_atm, axis=1
    )
    st.dataframe(
        styled_chain,
        use_container_width=True,
        hide_index=True,
        height=500
    )

    st.caption(
        "Yellow rows = At-the-money (ATM) strikes. "
        "CE = Call option. PE = Put option. "
        "OI = Open Interest (number of contracts outstanding)."
    )

st.markdown("---")
st.subheader("Options Concepts Guide")
st.markdown("""
**Put/Call Ratio (PCR):**
- PCR > 1.2 → Very bearish market sentiment
- PCR 0.8–1.2 → Neutral / slightly bearish
- PCR < 0.8 → Bullish market sentiment

**Max Pain:**
The strike price at which all options expire worthless,
causing maximum loss to option buyers and maximum profit
to option sellers. Near expiry, prices often drift
toward Max Pain.

**Open Interest:**
Total number of outstanding option contracts.
High OI at a strike = strong support or resistance.
Institutions use OI to identify key price levels.

**Implied Volatility:**
The market's expectation of future price movement.
High IV = expensive options (sell premium).
Low IV = cheap options (buy premium).
""")
