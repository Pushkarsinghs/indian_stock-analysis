import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical

st.set_page_config(
    page_title="Economic Calendar",
    page_icon="📅",
    layout="wide"
)

st.markdown(
    '<style>'
    '[data-testid="stSidebar"]{background:#F0F2F5;}'
    '.block-container{padding-top:1rem;}'
    '.event-card{'
    'border-radius:8px;padding:12px;margin:8px 0;'
    'border-left:5px solid;'
    '}'
    '</style>',
    unsafe_allow_html=True
)

st.markdown(
    '<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);'
    'padding:20px;border-radius:10px;color:white;margin-bottom:20px;">'
    '<h2 style="margin:0">📅 Economic Calendar — Event Impact Tracker</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'Upcoming macro events · Historical market reactions · '
    'Event-driven pattern analysis'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

today = datetime.now()

UPCOMING_EVENTS = [
    {
        "date":      (today + timedelta(days=3)).strftime("%d %b %Y"),
        "event":     "RBI Monetary Policy Committee Meeting",
        "category":  "Central Bank",
        "impact":    "High",
        "color":     "#D62728",
        "expected":  "Rate hold expected at 6.50%. Watch for forward guidance on inflation.",
        "sectors":   ["Banking","NBFC","Real Estate"],
        "symbol":    "🏦"
    },
    {
        "date":      (today + timedelta(days=8)).strftime("%d %b %Y"),
        "event":     "HDFC Bank Q1 FY27 Earnings",
        "category":  "Earnings",
        "impact":    "High",
        "color":     "#FF7F0E",
        "expected":  "NIM expansion expected. Watch for NPA commentary.",
        "sectors":   ["Banking"],
        "symbol":    "📊"
    },
    {
        "date":      (today + timedelta(days=12)).strftime("%d %b %Y"),
        "event":     "US Federal Reserve FOMC Meeting",
        "category":  "Global",
        "impact":    "High",
        "color":     "#D62728",
        "expected":  "Rate cut of 25bps possible. Positive for FII flows into India.",
        "sectors":   ["IT","FMCG","Pharma"],
        "symbol":    "🌐"
    },
    {
        "date":      (today + timedelta(days=15)).strftime("%d %b %Y"),
        "event":     "India CPI Inflation Data",
        "category":  "Macro Data",
        "impact":    "Medium",
        "color":     "#FF7F0E",
        "expected":  "CPI expected around 4.8%. Elevated food prices remain a concern.",
        "sectors":   ["FMCG","Consumer","Banking"],
        "symbol":    "📈"
    },
    {
        "date":      (today + timedelta(days=18)).strftime("%d %b %Y"),
        "event":     "TCS Q1 FY27 Earnings",
        "category":  "Earnings",
        "impact":    "High",
        "color":     "#FF7F0E",
        "expected":  "Revenue growth guidance for FY27. AI deals pipeline in focus.",
        "sectors":   ["IT"],
        "symbol":    "📊"
    },
    {
        "date":      (today + timedelta(days=22)).strftime("%d %b %Y"),
        "event":     "India GDP Q1 FY27 Data",
        "category":  "Macro Data",
        "impact":    "High",
        "color":     "#D62728",
        "expected":  "GDP growth expected at 7.2%. Infrastructure spending key driver.",
        "sectors":   ["Infrastructure","Cement","Banking"],
        "symbol":    "🏗️"
    },
    {
        "date":      (today + timedelta(days=28)).strftime("%d %b %Y"),
        "event":     "Reliance Industries Q1 FY27 Earnings",
        "category":  "Earnings",
        "impact":    "High",
        "color":     "#FF7F0E",
        "expected":  "Jio subscriber growth and retail EBITDA margin in focus.",
        "sectors":   ["Energy","Telecom","Consumer"],
        "symbol":    "📊"
    },
    {
        "date":      (today + timedelta(days=35)).strftime("%d %b %Y"),
        "event":     "India Trade Balance Data",
        "category":  "Macro Data",
        "impact":    "Medium",
        "color":     "#2CA02C",
        "expected":  "Export growth momentum expected to continue.",
        "sectors":   ["IT","Pharma","Auto"],
        "symbol":    "🚢"
    },
]

HISTORICAL_PATTERNS = {
    "RBI Rate Cut": {
        "avg_nifty_1d": +0.82,
        "avg_nifty_5d": +1.94,
        "avg_nifty_30d": +3.21,
        "best_sectors":  ["Banking","NBFC","Real Estate","Auto"],
        "worst_sectors": ["IT","Pharma"],
        "sample_size":   18,
        "note": "Rate cuts boost rate-sensitive sectors. Banking typically rallies most."
    },
    "RBI Rate Hike": {
        "avg_nifty_1d": -0.91,
        "avg_nifty_5d": -1.43,
        "avg_nifty_30d": -0.87,
        "best_sectors":  ["IT","Pharma","FMCG"],
        "worst_sectors": ["Banking","Real Estate","Auto"],
        "sample_size":   12,
        "note": "Rate hikes compress banking margins. Defensive sectors outperform."
    },
    "RBI Rate Hold": {
        "avg_nifty_1d": +0.21,
        "avg_nifty_5d": +0.87,
        "avg_nifty_30d": +2.14,
        "best_sectors":  ["Banking","IT","FMCG"],
        "worst_sectors": ["Metals","Energy"],
        "sample_size":   24,
        "note": "Rate holds are broadly neutral. Market follows broader trend."
    },
    "US Fed Rate Cut": {
        "avg_nifty_1d": +1.24,
        "avg_nifty_5d": +2.87,
        "avg_nifty_30d": +5.43,
        "best_sectors":  ["IT","Pharma","Auto","FMCG"],
        "worst_sectors": ["Metals","Energy"],
        "sample_size":   8,
        "note": "US rate cuts trigger FII inflows into emerging markets including India."
    },
    "Above Expected GDP": {
        "avg_nifty_1d": +0.94,
        "avg_nifty_5d": +1.78,
        "avg_nifty_30d": +3.87,
        "best_sectors":  ["Banking","Cement","Infrastructure","Auto"],
        "worst_sectors": [],
        "sample_size":   14,
        "note": "Strong GDP confirms economic recovery narrative. Broad-based rally."
    },
    "Below Expected Inflation": {
        "avg_nifty_1d": +0.67,
        "avg_nifty_5d": +1.34,
        "avg_nifty_30d": +2.98,
        "best_sectors":  ["Banking","FMCG","Consumer","Auto"],
        "worst_sectors": ["Metals"],
        "sample_size":   16,
        "note": "Low inflation = room for rate cuts. Consumption sectors benefit."
    },
}

EARNINGS_HISTORY = {
    "HDFCBANK.NS": [
        {"quarter":"Q4 FY26","eps_beat_pct": +8.4, "nifty_1d": +1.2, "stock_1d": +3.4},
        {"quarter":"Q3 FY26","eps_beat_pct": +5.2, "nifty_1d": +0.8, "stock_1d": +2.1},
        {"quarter":"Q2 FY26","eps_beat_pct": +11.3,"nifty_1d": +1.4, "stock_1d": +4.8},
        {"quarter":"Q1 FY26","eps_beat_pct": +6.7, "nifty_1d": +0.3, "stock_1d": +2.9},
    ],
    "TCS.NS": [
        {"quarter":"Q4 FY26","eps_beat_pct": +3.1, "nifty_1d": +0.7, "stock_1d": +2.4},
        {"quarter":"Q3 FY26","eps_beat_pct": -1.8, "nifty_1d": -0.2, "stock_1d": -3.2},
        {"quarter":"Q2 FY26","eps_beat_pct": +4.6, "nifty_1d": +0.9, "stock_1d": +3.1},
        {"quarter":"Q1 FY26","eps_beat_pct": +2.3, "nifty_1d": +0.4, "stock_1d": +1.8},
    ],
    "RELIANCE.NS": [
        {"quarter":"Q4 FY26","eps_beat_pct": +12.4,"nifty_1d": +1.8, "stock_1d": +4.2},
        {"quarter":"Q3 FY26","eps_beat_pct": +7.8, "nifty_1d": +0.6, "stock_1d": +3.1},
        {"quarter":"Q2 FY26","eps_beat_pct": +15.2,"nifty_1d": +2.1, "stock_1d": +5.7},
        {"quarter":"Q1 FY26","eps_beat_pct": +9.3, "nifty_1d": +1.2, "stock_1d": +3.8},
    ],
}

st.sidebar.header("Controls")
view_mode = st.sidebar.radio(
    "View",
    ["Upcoming Events","Historical Patterns","Earnings History"],
    index=0
)
category_filter = st.sidebar.multiselect(
    "Filter by Category",
    ["Central Bank","Earnings","Macro Data","Global"],
    default=[]
)
impact_filter = st.sidebar.multiselect(
    "Filter by Impact",
    ["High","Medium","Low"],
    default=[]
)

events_to_show = UPCOMING_EVENTS.copy()
if category_filter:
    events_to_show = [
        e for e in events_to_show
        if e["category"] in category_filter
    ]
if impact_filter:
    events_to_show = [
        e for e in events_to_show
        if e["impact"] in impact_filter
    ]

if view_mode == "Upcoming Events":
    high_count   = len([e for e in events_to_show if e["impact"]=="High"])
    medium_count = len([e for e in events_to_show if e["impact"]=="Medium"])
    next_event   = events_to_show[0] if events_to_show else None

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Total Events",     len(events_to_show))
    kc2.metric("High Impact",      high_count)
    kc3.metric("Medium Impact",    medium_count)
    kc4.metric(
        "Next Event",
        next_event["date"] if next_event else "N/A"
    )

    st.markdown("---")
    st.subheader("Upcoming Market-Moving Events")

    for event in events_to_show:
        impact_icon = (
            "🔴" if event["impact"] == "High" else
            "🟠" if event["impact"] == "Medium" else
            "🟢"
        )
        sectors_str = ", ".join(event.get("sectors", []))

        st.markdown(
            '<div style="background:' + event["color"] + '11;'
            'border-left:5px solid ' + event["color"] + ';'
            'border-radius:8px;padding:15px;margin:10px 0;">'
            '<div style="display:flex;justify-content:space-between;'
            'align-items:flex-start;">'
            '<div>'
            '<b style="font-size:1.05rem;color:#1F3864">'
            '' + event["symbol"] + ' ' + event["event"] + '</b><br>'
            '<span style="color:#666;font-size:0.85rem">'
            '📅 ' + event["date"] + ' &nbsp;|&nbsp; '
            '🏷️ ' + event["category"] + ' &nbsp;|&nbsp; '
            '' + impact_icon + ' ' + event["impact"] + ' Impact'
            '</span><br>'
            '<span style="color:#444;margin-top:5px;display:block">'
            '💡 ' + event["expected"] + '</span>'
            '</div>'
            '<div style="text-align:right;min-width:180px">'
            '<small style="color:#666">Sectors affected:</small><br>'
            '<b style="color:#1F3864">' + sectors_str + '</b>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.subheader("Timeline View")

    timeline_df = pd.DataFrame([
        {
            "Event":    e["event"][:40] + "..." if len(e["event"]) > 40
                        else e["event"],
            "Date":     e["date"],
            "Category": e["category"],
            "Impact":   e["impact"]
        }
        for e in events_to_show
    ])

    if not timeline_df.empty:
        color_map = {
            "Central Bank": "#D62728",
            "Earnings":     "#FF7F0E",
            "Macro Data":   "#1F77B4",
            "Global":       "#9467BD"
        }
        fig_tl = px.scatter(
            timeline_df,
            x="Date",
            y="Category",
            color="Category",
            size=[
                20 if imp == "High" else
                12 if imp == "Medium" else 8
                for imp in timeline_df["Impact"]
            ],
            hover_data=["Event","Impact"],
            color_discrete_map=color_map,
            title="Event Timeline (size = impact level)"
        )
        fig_tl.update_layout(
            height=350,
            template="plotly_white",
            showlegend=True,
            xaxis_tickangle=-30
        )
        st.plotly_chart(fig_tl, use_container_width=True)

elif view_mode == "Historical Patterns":
    st.subheader("How Markets React to Different Events")
    st.caption(
        "Based on historical data from past events. "
        "Past performance does not guarantee future results."
    )

    selected_event = st.selectbox(
        "Select Event Type",
        list(HISTORICAL_PATTERNS.keys()),
        index=0
    )

    if selected_event in HISTORICAL_PATTERNS:
        pattern = HISTORICAL_PATTERNS[selected_event]

        kc1, kc2, kc3, kc4 = st.columns(4)
        kc1.metric(
            "Avg NIFTY 1-Day",
            "{:+.2f}%".format(pattern["avg_nifty_1d"]),
            delta="{:+.2f}%".format(pattern["avg_nifty_1d"])
        )
        kc2.metric(
            "Avg NIFTY 5-Day",
            "{:+.2f}%".format(pattern["avg_nifty_5d"]),
            delta="{:+.2f}%".format(pattern["avg_nifty_5d"])
        )
        kc3.metric(
            "Avg NIFTY 30-Day",
            "{:+.2f}%".format(pattern["avg_nifty_30d"]),
            delta="{:+.2f}%".format(pattern["avg_nifty_30d"])
        )
        kc4.metric("Sample Events", str(pattern["sample_size"]))

        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("**Typical Return Pattern**")
            fig_pat = go.Figure(go.Bar(
                x=["1 Day","5 Days","30 Days"],
                y=[
                    pattern["avg_nifty_1d"],
                    pattern["avg_nifty_5d"],
                    pattern["avg_nifty_30d"]
                ],
                marker_color=[
                    "#2CA02C" if v >= 0 else "#D62728"
                    for v in [
                        pattern["avg_nifty_1d"],
                        pattern["avg_nifty_5d"],
                        pattern["avg_nifty_30d"]
                    ]
                ],
                text=[
                    "{:+.2f}%".format(pattern["avg_nifty_1d"]),
                    "{:+.2f}%".format(pattern["avg_nifty_5d"]),
                    "{:+.2f}%".format(pattern["avg_nifty_30d"])
                ],
                textposition="outside"
            ))
            fig_pat.add_hline(
                y=0, line_color="black", line_width=1
            )
            fig_pat.update_layout(
                height=300,
                template="plotly_white",
                yaxis_title="Average NIFTY Return %",
                showlegend=False
            )
            st.plotly_chart(fig_pat, use_container_width=True)

        with col_r:
            st.markdown("**Sector Impact**")
            if pattern["best_sectors"]:
                st.markdown(
                    '<div style="background:#E8F5E9;'
                    'border-left:4px solid #2CA02C;'
                    'padding:10px;border-radius:6px;'
                    'margin-bottom:8px;">'
                    '<b style="color:#2CA02C">Outperforming Sectors:</b><br>'
                    '' + ', '.join(pattern["best_sectors"]) +
                    '</div>',
                    unsafe_allow_html=True
                )
            if pattern["worst_sectors"]:
                st.markdown(
                    '<div style="background:#FFEBEE;'
                    'border-left:4px solid #D62728;'
                    'padding:10px;border-radius:6px;">'
                    '<b style="color:#D62728">Underperforming Sectors:</b><br>'
                    '' + ', '.join(pattern["worst_sectors"]) +
                    '</div>',
                    unsafe_allow_html=True
                )

        st.markdown(
            '<div style="background:#E3F2FD;'
            'border-left:4px solid #1F77B4;'
            'padding:12px;border-radius:6px;margin-top:15px;">'
            '<b style="color:#1F3864">Pattern Analysis:</b><br>'
            '' + pattern["note"] +
            '</div>',
            unsafe_allow_html=True
        )

elif view_mode == "Earnings History":
    st.subheader("Earnings Surprise Impact Analysis")

    selected_stock = st.selectbox(
        "Select Stock",
        list(EARNINGS_HISTORY.keys()),
        format_func=lambda x: str(x).replace(".NS",""),
        index=0
    )

    if selected_stock in EARNINGS_HISTORY:
        history = EARNINGS_HISTORY[selected_stock]
        hist_df = pd.DataFrame(history)
        ticker_clean = str(selected_stock).replace(".NS","")

        kc1, kc2, kc3 = st.columns(3)
        kc1.metric(
            "Avg EPS Beat",
            "{:+.1f}%".format(hist_df["eps_beat_pct"].mean())
        )
        kc2.metric(
            "Avg Stock Reaction",
            "{:+.2f}%".format(hist_df["stock_1d"].mean())
        )
        kc3.metric(
            "Beat Rate",
            "{:.0%}".format(
                (hist_df["eps_beat_pct"] > 0).mean()
            )
        )

        fig_earn = go.Figure()
        fig_earn.add_trace(go.Bar(
            x=hist_df["quarter"],
            y=hist_df["eps_beat_pct"],
            name="EPS Beat %",
            marker_color=[
                "#2CA02C" if v > 0 else "#D62728"
                for v in hist_df["eps_beat_pct"]
            ],
            text=hist_df["eps_beat_pct"].apply(
                lambda x: "{:+.1f}%".format(x)
            ),
            textposition="outside",
            yaxis="y"
        ))
        fig_earn.add_trace(go.Scatter(
            x=hist_df["quarter"],
            y=hist_df["stock_1d"],
            name="Stock 1-Day Reaction",
            line=dict(color="#1F3864", width=2.5),
            mode="lines+markers",
            marker=dict(size=10),
            yaxis="y2"
        ))
        fig_earn.add_hline(y=0, line_color="gray",
                           line_width=0.8)
        fig_earn.update_layout(
            height=380,
            template="plotly_white",
            title=ticker_clean + " — EPS Beat vs Stock Reaction",
            legend=dict(orientation="h", y=1.02),
            yaxis=dict(title="EPS Beat %", side="left"),
            yaxis2=dict(
                title="Stock Reaction %",
                side="right",
                overlaying="y"
            )
        )
        st.plotly_chart(fig_earn, use_container_width=True)

        st.subheader("Earnings History Table")
        disp_hist = hist_df.copy()
        disp_hist.columns = [
            "Quarter","EPS Beat %","NIFTY 1-Day %","Stock 1-Day %"
        ]
        st.dataframe(
            disp_hist,
            use_container_width=True,
            hide_index=True
        )

        avg_beat    = float(hist_df["eps_beat_pct"].mean())
        avg_reaction = float(hist_df["stock_1d"].mean())
        beat_color  = "#2CA02C" if avg_beat > 0 else "#D62728"
        st.markdown(
            '<div style="background:' + beat_color + '22;'
            'border-left:4px solid ' + beat_color + ';'
            'padding:12px;border-radius:6px;margin-top:15px;">'
            '<b style="color:' + beat_color + '">'
            + ticker_clean + ' Earnings Pattern</b><br>'
            'Averages ' + "{:+.1f}%".format(avg_beat) +
            ' EPS beat and ' +
            "{:+.2f}%".format(avg_reaction) +
            ' stock reaction on earnings day. '
            + ('Consistent outperformer — strong earnings visibility.'
               if avg_beat > 5 else
               'Mixed earnings track record — approach with caution.')
            + '</div>',
            unsafe_allow_html=True
        )
