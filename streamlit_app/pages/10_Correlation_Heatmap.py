import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical

st.set_page_config(
    page_title="Correlation Heatmap",
    page_icon="🔗",
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
    '<h2 style="margin:0">🔗 Correlation Heatmap — Stock Return Correlations</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Shows how stocks move together. '
    'Use this to build a diversified portfolio.'
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

period = st.sidebar.selectbox(
    "Time Period",
    ["1 Month","3 Months","6 Months","1 Year"],
    index=2
)
days_map = {"1 Month":30,"3 Months":90,"6 Months":180,"1 Year":365}
days     = days_map[period]

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

all_sectors = sorted(set(SECTOR_MAP.values()))
selected_sectors = st.sidebar.multiselect(
    "Filter by Sector (optional)",
    all_sectors,
    default=[],
    help="Leave empty to show all sectors"
)

view_mode = st.sidebar.radio(
    "View Mode",
    ["Full Heatmap (All Stocks)", "Sector Average Correlation"],
    index=0
)

cutoff = df["Date"].max() - pd.Timedelta(days=days)
recent = df[df["Date"] >= cutoff].copy()

if selected_sectors:
    recent["Sector"] = recent["Ticker"].map(SECTOR_MAP)
    recent = recent[recent["Sector"].isin(selected_sectors)]

if recent.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# Build returns pivot table
returns_pivot = recent.pivot_table(
    index="Date",
    columns="Ticker",
    values="Daily_Return"
)
returns_pivot = returns_pivot.dropna(thresh=int(len(returns_pivot)*0.7), axis=1)
returns_pivot = returns_pivot.ffill().bfill()

if returns_pivot.shape[1] < 2:
    st.warning("Not enough stocks with sufficient data for correlation.")
    st.stop()

corr_matrix = returns_pivot.corr()

# ════════════════════════════════════════
# VIEW 1 — Full Heatmap
# ════════════════════════════════════════
if view_mode == "Full Heatmap (All Stocks)":

    ticker_labels = [
        str(t).replace(".NS","")
        for t in corr_matrix.columns
    ]

    fig = go.Figure(go.Heatmap(
        z=corr_matrix.values,
        x=ticker_labels,
        y=ticker_labels,
        colorscale=[
            [0.0,  "#D62728"],
            [0.25, "#FF9999"],
            [0.5,  "#FFFFFF"],
            [0.75, "#99CC99"],
            [1.0,  "#2CA02C"]
        ],
        zmin=-1, zmax=1,
        colorbar=dict(
            title="Correlation",
            tickvals=[-1,-0.5,0,0.5,1],
            ticktext=["-1.0","−0.5","0.0","0.5","1.0"]
        ),
        hovertemplate=(
            "Stock 1: %{x}<br>"
            "Stock 2: %{y}<br>"
            "Correlation: %{z:.3f}"
            "<extra></extra>"
        )
    ))

    fig.update_layout(
        height=700,
        title=dict(
            text="Stock Return Correlation Matrix — " + period,
            font=dict(size=14, color="#1F3864")
        ),
        xaxis=dict(tickfont=dict(size=8)),
        yaxis=dict(tickfont=dict(size=8)),
        margin=dict(t=60, b=60, l=80, r=60)
    )
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# VIEW 2 — Sector Average Correlation
# ════════════════════════════════════════
else:
    ticker_to_sector = {
        str(t): str(SECTOR_MAP.get(t, "Unknown"))
        for t in corr_matrix.columns
    }

    sector_list = sorted(set(ticker_to_sector.values()))
    sector_corr = pd.DataFrame(
        index=sector_list, columns=sector_list, dtype=float
    )

    for s1 in sector_list:
        for s2 in sector_list:
            t1_list = [
                t for t, s in ticker_to_sector.items()
                if s == s1 and t in corr_matrix.columns
            ]
            t2_list = [
                t for t, s in ticker_to_sector.items()
                if s == s2 and t in corr_matrix.columns
            ]
            if not t1_list or not t2_list:
                sector_corr.loc[s1, s2] = 0.0
                continue
            vals = []
            for t1 in t1_list:
                for t2 in t2_list:
                    if t1 != t2 and t1 in corr_matrix and t2 in corr_matrix:
                        v = float(corr_matrix.loc[t1, t2])
                        if not np.isnan(v):
                            vals.append(v)
            sector_corr.loc[s1, s2] = round(
                float(np.mean(vals)), 3
            ) if vals else 0.0

    sector_corr = sector_corr.astype(float)

    fig = go.Figure(go.Heatmap(
        z=sector_corr.values,
        x=sector_list,
        y=sector_list,
        colorscale=[
            [0.0,  "#D62728"],
            [0.25, "#FF9999"],
            [0.5,  "#FFFFFF"],
            [0.75, "#99CC99"],
            [1.0,  "#2CA02C"]
        ],
        zmin=-1, zmax=1,
        text=sector_corr.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=10),
        colorbar=dict(title="Avg Correlation")
    ))

    fig.update_layout(
        height=550,
        title=dict(
            text="Sector Average Correlation — " + period,
            font=dict(size=14, color="#1F3864")
        ),
        margin=dict(t=60, b=80, l=100, r=60)
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Most and Least Correlated Pairs ───────────────────────
st.subheader("Most and Least Correlated Stock Pairs")

pairs = []
cols  = list(corr_matrix.columns)
for i in range(len(cols)):
    for j in range(i + 1, len(cols)):
        val = float(corr_matrix.iloc[i, j])
        if not np.isnan(val):
            pairs.append({
                "Stock 1":     str(cols[i]).replace(".NS",""),
                "Stock 2":     str(cols[j]).replace(".NS",""),
                "Correlation": round(val, 3)
            })

pairs_df = pd.DataFrame(pairs).sort_values(
    "Correlation", ascending=False
)

col_l, col_r = st.columns(2)

with col_l:
    st.markdown(
        "**Most Correlated Pairs** — move together "
        "(avoid holding both for diversification)"
    )
    top10 = pairs_df.head(10)
    fig_top = px.bar(
        top10,
        x="Correlation",
        y=top10["Stock 1"] + " / " + top10["Stock 2"],
        orientation="h",
        color="Correlation",
        color_continuous_scale=["#FFFFFF","#2CA02C"],
        range_color=[0, 1]
    )
    fig_top.update_layout(
        height=350,
        template="plotly_white",
        showlegend=False,
        yaxis_title="",
        margin=dict(l=120, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_top, use_container_width=True)

with col_r:
    st.markdown(
        "**Least Correlated Pairs** — move independently "
        "(good for diversification)"
    )
    bot10 = pairs_df.tail(10).sort_values("Correlation")
    fig_bot = px.bar(
        bot10,
        x="Correlation",
        y=bot10["Stock 1"] + " / " + bot10["Stock 2"],
        orientation="h",
        color="Correlation",
        color_continuous_scale=["#D62728","#FFFFFF"],
        range_color=[-1, 0]
    )
    fig_bot.update_layout(
        height=350,
        template="plotly_white",
        showlegend=False,
        yaxis_title="",
        margin=dict(l=120, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_bot, use_container_width=True)

# ── Portfolio diversification checker ─────────────────────
st.markdown("---")
st.subheader("Portfolio Diversification Checker")
st.caption(
    "Select the stocks you currently hold "
    "to see how correlated your portfolio is"
)

all_tickers_clean = sorted([
    str(t).replace(".NS","")
    for t in corr_matrix.columns
])

portfolio_stocks = st.multiselect(
    "Your Portfolio Stocks",
    all_tickers_clean,
    default=all_tickers_clean[:5]
)

if len(portfolio_stocks) >= 2:
    port_full = [t + ".NS" for t in portfolio_stocks]
    port_corr_cols = [
        t for t in port_full if t in corr_matrix.columns
    ]

    if len(port_corr_cols) >= 2:
        port_matrix = corr_matrix.loc[
            port_corr_cols, port_corr_cols
        ]
        port_labels  = [
            str(t).replace(".NS","")
            for t in port_matrix.columns
        ]

        upper_triangle = []
        n = len(port_matrix.columns)
        for i in range(n):
            for j in range(i+1, n):
                upper_triangle.append(
                    float(port_matrix.iloc[i,j])
                )

        avg_corr = round(float(np.mean(upper_triangle)), 3) \
                   if upper_triangle else 0.0

        if avg_corr > 0.7:
            div_rating = "Poor"
            div_color  = "#D62728"
            div_msg    = ("Your stocks are highly correlated. "
                          "A market crash would hit all of them simultaneously.")
        elif avg_corr > 0.5:
            div_rating = "Moderate"
            div_color  = "#FF7F0E"
            div_msg    = ("Moderate diversification. "
                          "Consider adding stocks from unrelated sectors.")
        elif avg_corr > 0.3:
            div_rating = "Good"
            div_color  = "#2CA02C"
            div_msg    = ("Good diversification. "
                          "Your stocks have a reasonable spread of correlation.")
        else:
            div_rating = "Excellent"
            div_color  = "#1A7A1A"
            div_msg    = ("Excellent diversification. "
                          "Your stocks move largely independently.")

        st.markdown(
            '<div style="background:' + div_color + '22;'
            'border-left:5px solid ' + div_color + ';'
            'padding:15px;border-radius:8px;margin:15px 0;">'
            '<b style="color:' + div_color + ';font-size:1.1rem;">'
            'Diversification Rating: ' + div_rating + '</b><br>'
            'Average Correlation: ' + str(avg_corr) + '<br>'
            '' + div_msg +
            '</div>',
            unsafe_allow_html=True
        )

        port_fig = go.Figure(go.Heatmap(
            z=port_matrix.values,
            x=port_labels,
            y=port_labels,
            colorscale=[
                [0.0,  "#D62728"],
                [0.5,  "#FFFFFF"],
                [1.0,  "#2CA02C"]
            ],
            zmin=-1, zmax=1,
            text=port_matrix.values.round(2),
            texttemplate="%{text}",
            textfont=dict(size=12)
        ))
        port_fig.update_layout(
            height=400,
            title=dict(
                text="Your Portfolio Correlation Matrix",
                font=dict(color="#1F3864")
            ),
            margin=dict(t=50, b=50, l=80, r=40)
        )
        st.plotly_chart(port_fig, use_container_width=True)

st.markdown("---")
st.subheader("How to Use This Page")
st.markdown("""
| Correlation | Meaning | Portfolio Impact |
|---|---|---|
| **0.8 to 1.0** | Highly correlated — move almost identically | Not diversified |
| **0.5 to 0.8** | Moderately correlated | Some diversification |
| **0.2 to 0.5** | Weakly correlated — somewhat independent | Good diversification |
| **-1.0 to 0.2** | Low or negative correlation — move independently | Excellent diversification |

**Rule of thumb:** A well-diversified portfolio should have an
average pairwise correlation below 0.5.
""")
