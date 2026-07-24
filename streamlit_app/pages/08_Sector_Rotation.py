import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical

st.set_page_config(
    page_title="Sector Rotation",
    page_icon="🔄",
    layout="wide"
)

st.markdown(
    '<style>[data-testid="stSidebar"]{background:#F0F2F5;}'
    '.block-container{padding-top:1rem;}</style>',
    unsafe_allow_html=True
)
st.markdown(
    '<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);'
    'padding:20px;border-radius:10px;color:white;margin-bottom:20px;">'
    '<h2 style="margin:0">🔄 Sector Rotation Radar</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Which sectors are Leading, Weakening, Improving or Lagging right now'
    '</p></div>',
    unsafe_allow_html=True
)

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

df = load_technical()
if df.empty:
    st.error("Data not found. Please check data files.")
    st.stop()

df["Date"]   = pd.to_datetime(df["Date"])
df["Sector"] = df["Ticker"].map(SECTOR_MAP)

st.sidebar.header("Controls")
lookback = st.sidebar.selectbox(
    "Analysis Period",
    ["2 Weeks","1 Month","3 Months"],
    index=1
)
days_map = {"2 Weeks":14,"1 Month":30,"3 Months":90}
days     = days_map[lookback]

max_date = df["Date"].max()
cutoff   = max_date - pd.Timedelta(days=days)
recent   = df[df["Date"] >= cutoff].copy()

nifty_return = recent.groupby("Date")["Daily_Return"].mean()

sector_data = []
for sector in df["Sector"].dropna().unique():
    sector_df = recent[recent["Sector"] == sector]
    if len(sector_df) < 10:
        continue

    sect_ret = sector_df.groupby("Date")["Daily_Return"].mean()
    aligned  = pd.DataFrame({
        "sector": sect_ret,
        "nifty":  nifty_return
    }).dropna()

    if len(aligned) < 5:
        continue

    nifty_safe = aligned["nifty"].replace(0, 0.0001)
    rs         = (aligned["sector"] / nifty_safe)
    rs_mean    = float(rs.mean())
    rs_momentum = float(rs.diff(max(1, len(rs)//5)).mean())

    stocks_in_sector = sector_df["Ticker"].unique()
    avg_return = float(
        sector_df.groupby("Ticker")["Daily_Return"]
        .mean().mean() * 100 * 252
    )

    sector_data.append({
        "Sector":       sector,
        "RS":           round(rs_mean, 4),
        "Momentum":     round(rs_momentum, 4),
        "Avg_Ann_Return": round(avg_return, 2),
        "Num_Stocks":   len(stocks_in_sector)
    })

if not sector_data:
    st.warning("Not enough data to compute sector rotation.")
    st.stop()

sector_df_plot = pd.DataFrame(sector_data)

def get_quadrant(rs, mom):
    if rs > 1 and mom > 0:   return "Leading"
    if rs > 1 and mom <= 0:  return "Weakening"
    if rs <= 1 and mom > 0:  return "Improving"
    return "Lagging"

sector_df_plot["Quadrant"] = sector_df_plot.apply(
    lambda r: get_quadrant(r["RS"], r["Momentum"]), axis=1
)

quad_colors = {
    "Leading":   "#2CA02C",
    "Weakening": "#FF7F0E",
    "Improving": "#1F77B4",
    "Lagging":   "#D62728"
}
sector_df_plot["Color"] = sector_df_plot["Quadrant"].map(quad_colors)

rs_mid  = float(sector_df_plot["RS"].median())
mom_mid = 0.0

st.subheader("Sector Rotation Quadrant Chart")
st.caption(
    "RS > median and Momentum > 0 = Leading  |  "
    "RS > median and Momentum < 0 = Weakening  |  "
    "RS < median and Momentum > 0 = Improving  |  "
    "RS < median and Momentum < 0 = Lagging"
)

fig = go.Figure()

for _, row in sector_df_plot.iterrows():
    fig.add_trace(go.Scatter(
        x=[float(row["RS"])],
        y=[float(row["Momentum"])],
        mode="markers+text",
        marker=dict(
            size=max(20, int(row["Num_Stocks"]) * 5),
            color=row["Color"],
            opacity=0.85,
            line=dict(color="white", width=2)
        ),
        text=[str(row["Sector"])],
        textposition="top center",
        textfont=dict(size=11, color="#1F3864"),
        name=str(row["Sector"]),
        hovertemplate=(
            "<b>" + str(row["Sector"]) + "</b><br>"
            "Quadrant: " + str(row["Quadrant"]) + "<br>"
            "Relative Strength: " + str(round(float(row["RS"]),3)) + "<br>"
            "Momentum: " + str(round(float(row["Momentum"]),4)) + "<br>"
            "Ann Return: " + str(row["Avg_Ann_Return"]) + "%<br>"
            "Stocks: " + str(row["Num_Stocks"]) +
            "<extra></extra>"
        ),
        showlegend=False
    ))

fig.add_vline(
    x=rs_mid, line_dash="dash",
    line_color="gray", line_width=1
)
fig.add_hline(
    y=mom_mid, line_dash="dash",
    line_color="gray", line_width=1
)

x_min = float(sector_df_plot["RS"].min()) * 0.95
x_max = float(sector_df_plot["RS"].max()) * 1.05
y_min = float(sector_df_plot["Momentum"].min())
y_max = float(sector_df_plot["Momentum"].max())
y_pad = max(abs(y_min), abs(y_max)) * 0.3

label_font = dict(size=13, family="Arial Black")
fig.add_annotation(
    x=x_max*0.99, y=y_max + y_pad*0.5,
    text="LEADING", showarrow=False,
    font=dict(color="#2CA02C", size=13, family="Arial Black"),
    xanchor="right"
)
fig.add_annotation(
    x=x_max*0.99, y=y_min - y_pad*0.5,
    text="WEAKENING", showarrow=False,
    font=dict(color="#FF7F0E", size=13, family="Arial Black"),
    xanchor="right"
)
fig.add_annotation(
    x=x_min*1.01, y=y_max + y_pad*0.5,
    text="IMPROVING", showarrow=False,
    font=dict(color="#1F77B4", size=13, family="Arial Black"),
    xanchor="left"
)
fig.add_annotation(
    x=x_min*1.01, y=y_min - y_pad*0.5,
    text="LAGGING", showarrow=False,
    font=dict(color="#D62728", size=13, family="Arial Black"),
    xanchor="left"
)

fig.update_layout(
    height=580,
    template="plotly_white",
    xaxis_title="Relative Strength vs NIFTY 50",
    yaxis_title="Momentum (Change in Relative Strength)",
    xaxis=dict(range=[x_min, x_max]),
    yaxis=dict(range=[y_min - y_pad, y_max + y_pad]),
    margin=dict(t=40, b=60, l=60, r=40)
)

st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Sector Summary Table")
    display = sector_df_plot[[
        "Sector","Quadrant","RS","Momentum",
        "Avg_Ann_Return","Num_Stocks"
    ]].sort_values("RS", ascending=False).copy()
    display.columns = [
        "Sector","Quadrant","Rel Strength",
        "Momentum","Ann Return %","Stocks"
    ]
    st.dataframe(display, use_container_width=True, hide_index=True)

with col2:
    st.subheader("Stocks in Each Quadrant")
    for quadrant, color in quad_colors.items():
        sectors_in_quad = sector_df_plot[
            sector_df_plot["Quadrant"] == quadrant
        ]["Sector"].tolist()

        if not sectors_in_quad:
            continue

        stocks_list = []
        for sector in sectors_in_quad:
            sector_stocks = [
                t.replace(".NS","")
                for t, s in SECTOR_MAP.items()
                if s == sector
            ]
            stocks_list.extend(sector_stocks)

        st.markdown(
            f'<div style="background:{color}22;border-left:4px solid {color};'
            f'padding:10px;border-radius:5px;margin-bottom:8px;">'
            f'<b style="color:{color}">{quadrant}</b>: '
            f'{", ".join(sectors_in_quad)}'
            f'</div>',
            unsafe_allow_html=True
        )

st.markdown("---")
st.subheader("How to Use This Chart")
st.markdown("""
| Quadrant | What it means | What to do |
|---|---|---|
| 🟢 **Leading** | Strong momentum, beating NIFTY | Consider buying stocks in these sectors |
| 🟠 **Weakening** | Was strong, now slowing down | Watch carefully, consider reducing exposure |
| 🔵 **Improving** | Was weak, now picking up momentum | Early entry opportunity |
| 🔴 **Lagging** | Weak and getting weaker | Avoid or reduce exposure |
""")
