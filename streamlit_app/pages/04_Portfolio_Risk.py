import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_risk_metrics, load_portfolio_allocation, load_portfolio_performance

st.set_page_config(page_title="Portfolio and Risk", page_icon="💼", layout="wide")
st.markdown('<style>[data-testid="stSidebar"]{background:#F0F2F5;}</style>', unsafe_allow_html=True)
st.markdown('<div style="background:linear-gradient(135deg,#1F3864,#2E5EAA);padding:20px;border-radius:10px;color:white;margin-bottom:20px;"><h2 style="margin:0">💼 Portfolio and Risk Analysis - Efficient Frontier</h2></div>', unsafe_allow_html=True)

risk  = load_risk_metrics()
alloc = load_portfolio_allocation()
perf  = load_portfolio_performance()

total_val  = float(alloc["Value_INR"].sum()) if not alloc.empty and "Value_INR" in alloc.columns else 0
avg_sharpe = float(risk["Sharpe_Ratio"].mean()) if not risk.empty and "Sharpe_Ratio" in risk.columns else 0
best_t     = str(risk.nlargest(1,"Sharpe_Ratio")["Ticker"].values[0]).replace(".NS","") if not risk.empty else "N/A"

c1,c2,c3,c4 = st.columns(4)
c1.metric("Portfolio Value",  "Rs" + "{:,.0f}".format(total_val))
c2.metric("Avg Sharpe Ratio", "{:.3f}".format(avg_sharpe))
c3.metric("Best Sharpe Stock", best_t)
c4.metric("Stocks in Portfolio", len(alloc))

st.markdown("---")
st.subheader("🎲 Monte Carlo Portfolio Stress Test")
st.caption(
    "Simulates 1,000 possible future 30-day scenarios "
    "based on historical return distributions"
)

if not risk.empty and "Ann_Volatility_Pct" in risk.columns:

    mc_ticker = st.selectbox(
        "Select stock to stress test",
        [c for c in sorted(risk["Ticker"].unique())],
        format_func=lambda x: str(x).replace(".NS",""),
        key="mc_ticker_select"
    )

    mc_investment = st.number_input(
        "Investment Amount (Rs)",
        min_value=10000,
        max_value=10000000,
        value=100000,
        step=10000,
        key="mc_investment"
    )

    mc_days = st.selectbox(
        "Forecast Horizon",
        [15, 30, 60, 90],
        index=1,
        key="mc_days"
    )

    mc_simulations = 1000

    mc_row = risk[risk["Ticker"] == mc_ticker]
    if not mc_row.empty:
        ann_ret = float(mc_row["Ann_Return_Pct"].values[0]) / 100
        ann_vol = float(mc_row["Ann_Volatility_Pct"].values[0]) / 100

        daily_ret = ann_ret / 252
        daily_vol = ann_vol / np.sqrt(252)

        np.random.seed(42)
        simulated_paths = np.zeros((mc_simulations, mc_days))

        for sim in range(mc_simulations):
            daily_returns = np.random.normal(
                daily_ret, daily_vol, mc_days
            )
            cumulative = np.cumprod(1 + daily_returns)
            simulated_paths[sim] = mc_investment * cumulative

        final_values = simulated_paths[:, -1]

        p10  = round(float(np.percentile(final_values, 10)),  0)
        p25  = round(float(np.percentile(final_values, 25)),  0)
        p50  = round(float(np.percentile(final_values, 50)),  0)
        p75  = round(float(np.percentile(final_values, 75)),  0)
        p90  = round(float(np.percentile(final_values, 90)),  0)
        prob_profit = round(float((final_values > mc_investment).mean()) * 100, 1)
        prob_loss10 = round(float((final_values < mc_investment * 0.9).mean()) * 100, 1)
        prob_gain20 = round(float((final_values > mc_investment * 1.2).mean()) * 100, 1)

        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("10th Percentile (Worst)",   "Rs" + "{:,.0f}".format(p10))
        mc2.metric("25th Percentile",            "Rs" + "{:,.0f}".format(p25))
        mc3.metric("50th Percentile (Expected)", "Rs" + "{:,.0f}".format(p50))
        mc4.metric("75th Percentile",            "Rs" + "{:,.0f}".format(p75))
        mc5.metric("90th Percentile (Best)",     "Rs" + "{:,.0f}".format(p90))

        prob_color = "#2CA02C" if prob_profit > 60 else "#D62728"
        st.markdown(
            '<div style="background:' + prob_color + '22;'
            'border-left:5px solid ' + prob_color + ';'
            'padding:12px;border-radius:8px;margin:12px 0;">'
            '<b style="color:' + prob_color + '">Monte Carlo Results for ' +
            str(mc_ticker).replace(".NS","") + ' over ' + str(mc_days) + ' days:</b><br>'
            'Probability of profit: <b>' + str(prob_profit) + '%</b> | '
            'Probability of 10%+ loss: <b>' + str(prob_loss10) + '%</b> | '
            'Probability of 20%+ gain: <b>' + str(prob_gain20) + '%</b>'
            '</div>',
            unsafe_allow_html=True
        )

        fig_mc = go.Figure()

        show_paths = min(200, mc_simulations)
        for i in range(show_paths):
            alpha = 0.03
            color = (
                "rgba(44,160,44," + str(alpha) + ")"
                if simulated_paths[i, -1] > mc_investment
                else "rgba(214,39,40," + str(alpha) + ")"
            )
            fig_mc.add_trace(go.Scatter(
                x=list(range(mc_days)),
                y=simulated_paths[i],
                mode="lines",
                line=dict(color=color, width=1),
                showlegend=False,
                hoverinfo="skip"
            ))

        days_range = list(range(mc_days))
        fig_mc.add_trace(go.Scatter(
            x=days_range,
            y=[float(np.percentile(simulated_paths[:, d], 10))
               for d in range(mc_days)],
            name="10th Percentile",
            line=dict(color="#D62728", width=2, dash="dash")
        ))
        fig_mc.add_trace(go.Scatter(
            x=days_range,
            y=[float(np.percentile(simulated_paths[:, d], 50))
               for d in range(mc_days)],
            name="50th Percentile (Expected)",
            line=dict(color="#1F3864", width=2.5)
        ))
        fig_mc.add_trace(go.Scatter(
            x=days_range,
            y=[float(np.percentile(simulated_paths[:, d], 90))
               for d in range(mc_days)],
            name="90th Percentile",
            line=dict(color="#2CA02C", width=2, dash="dash")
        ))
        fig_mc.add_hline(
            y=mc_investment,
            line_dash="dot",
            line_color="gray",
            annotation_text="Starting Capital"
        )
        fig_mc.update_layout(
            height=450,
            template="plotly_white",
            title="Monte Carlo Simulation — " + str(mc_simulations) +
                  " Scenarios for " + str(mc_ticker).replace(".NS",""),
            xaxis_title="Days",
            yaxis_title="Portfolio Value (Rs)",
            legend=dict(orientation="h", y=1.02)
        )
        st.plotly_chart(fig_mc, use_container_width=True)

        st.caption(
            "Green paths = profitable scenarios. "
            "Red paths = loss scenarios. "
            "Based on historical volatility of " +
            str(round(ann_vol * 100, 1)) + "% per year."
        )
        
st.markdown("---")
cl, cr = st.columns(2)
with cl:
    st.subheader("Portfolio Allocation")
    if not alloc.empty and "Value_INR" in alloc.columns:
        name_col = "Company" if "Company" in alloc.columns else "Ticker"
        fig1 = px.pie(alloc,names=name_col,values="Value_INR",hole=0.3,title="Rs" + "{:,.0f}".format(total_val))
        fig1.update_traces(textposition="outside",textinfo="label+percent")
        st.plotly_chart(fig1, use_container_width=True)
        show_cols = [c for c in ["Company","Shares","Price","Value_INR","Weight_Pct"] if c in alloc.columns]
        st.dataframe(alloc[show_cols].sort_values("Value_INR",ascending=False) if "Value_INR" in alloc.columns else alloc[show_cols], use_container_width=True, hide_index=True)
with cr:
    st.subheader("Risk vs Return")
    if not risk.empty and "Ann_Volatility_Pct" in risk.columns:
        fig2 = px.scatter(risk,x="Ann_Volatility_Pct",y="Ann_Return_Pct",color="Sharpe_Ratio",
                          color_continuous_scale=["#D62728","#FFFFFF","#2CA02C"],hover_data=["Ticker"],
                          labels={"Ann_Volatility_Pct":"Volatility (%)","Ann_Return_Pct":"Return (%)"})
        fig2.add_vline(x=20,line_dash="dash",line_color="#D62728",annotation_text="High Risk")
        fig2.add_hline(y=0,line_dash="dash",line_color="black")
        fig2.update_layout(height=450,template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)

st.subheader("Sharpe Ratio by Stock")
if not risk.empty and "Sharpe_Ratio" in risk.columns:
    ss            = risk.sort_values("Sharpe_Ratio",ascending=True)
    bar_colors    = ["#2CA02C" if float(v)>=0 else "#D62728" for v in ss["Sharpe_Ratio"]]
    ticker_labels = [str(t).replace(".NS","") for t in ss["Ticker"]]
    fig3 = go.Figure(go.Bar(x=ss["Sharpe_Ratio"],y=ticker_labels,orientation="h",marker_color=bar_colors))
    fig3.add_vline(x=1.0,line_dash="dash",line_color="navy",annotation_text="Good Sharpe")
    fig3.add_vline(x=0,line_color="black",line_width=0.8)
    fig3.update_layout(height=600,template="plotly_white",xaxis_title="Sharpe Ratio")
    st.plotly_chart(fig3, use_container_width=True)

if not perf.empty:
    st.subheader("Portfolio Strategy Comparison")
    st.dataframe(perf, use_container_width=True, hide_index=True)
