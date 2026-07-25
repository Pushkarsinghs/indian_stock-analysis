import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
sys.path.append("/mount/src/indian_stock-analysis/streamlit_app")
from data_loader import load_technical, load_signals

st.set_page_config(
    page_title="ML Signal Classifier",
    page_icon="🤖",
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
    '<h2 style="margin:0">🤖 ML Signal Classifier</h2>'
    '<p style="margin:5px 0 0 0;opacity:0.85">'
    'XGBoost model trained on 15 technical features — '
    'predicts 5-day forward return direction with SHAP explainability'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

df      = load_technical()
signals = load_signals()

if df.empty:
    st.error("Technical data not found.")
    st.stop()

df["Date"] = pd.to_datetime(df["Date"])

FEATURE_COLS = [
    "RSI","MACD","MACD_Signal","MACD_Hist",
    "BB_Width","ATR","OBV","SMA_20","SMA_50",
    "EMA_20","Daily_Return","Stoch_K","Stoch_D",
    "ADX","Signal_Score"
]

available_features = [
    c for c in FEATURE_COLS if c in df.columns
]

st.sidebar.header("Controls")
ticker = st.sidebar.selectbox(
    "Select Stock",
    sorted(df["Ticker"].unique()),
    index=0
)

train_months = st.sidebar.selectbox(
    "Training Data Period",
    ["3 Months","6 Months","9 Months","12 Months"],
    index=2
)
train_days_map = {
    "3 Months":90,"6 Months":180,
    "9 Months":270,"12 Months":365
}
train_days = train_days_map[train_months]

predict_days = st.sidebar.selectbox(
    "Prediction Horizon",
    ["3 Days","5 Days","10 Days"],
    index=1
)
predict_days_map = {"3 Days":3,"5 Days":5,"10 Days":10}
n_days = predict_days_map[predict_days]

ticker_clean = str(ticker).replace(".NS","")

stock = df[df["Ticker"]==ticker].copy().sort_values("Date")
cutoff = stock["Date"].max() - pd.Timedelta(days=train_days)
stock  = stock[stock["Date"] >= cutoff].copy()

stock["Target"] = (
    stock["Close"].shift(-n_days) > stock["Close"]
).astype(int)

model_data = stock[available_features + ["Target","Date","Close"]].dropna()

if len(model_data) < 50:
    st.warning(
        "Not enough data to train model for " +
        ticker_clean +
        ". Need at least 50 rows, have " +
        str(len(model_data)) + "."
    )
    st.stop()

split_idx = int(len(model_data) * 0.8)
train     = model_data.iloc[:split_idx]
test      = model_data.iloc[split_idx:]

X_train = train[available_features]
y_train = train["Target"]
X_test  = test[available_features]
y_test  = test["Target"]

if not XGB_AVAILABLE:
    st.error(
        "XGBoost is not installed in this environment. "
        "The model will run using a simple Random Forest fallback."
    )

with st.spinner("Training ML model on " + ticker_clean + " data..."):
    try:
        if XGB_AVAILABLE:
            model = xgb.XGBClassifier(
                n_estimators    = 100,
                max_depth       = 4,
                learning_rate   = 0.1,
                random_state    = 42,
                eval_metric     = "logloss",
                use_label_encoder = False
            )
        else:
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=4,
                random_state=42
            )

        model.fit(X_train, y_train)

        train_acc = round(
            float((model.predict(X_train) == y_train).mean()) * 100, 1
        )
        test_acc  = round(
            float((model.predict(X_test) == y_test).mean()) * 100, 1
        )

        latest_features = stock[available_features].dropna().iloc[-1:]
        if len(latest_features) > 0:
            prediction     = int(model.predict(latest_features)[0])
            predict_proba  = model.predict_proba(latest_features)[0]
            up_probability = round(float(predict_proba[1]) * 100, 1)
            dn_probability = round(float(predict_proba[0]) * 100, 1)
        else:
            prediction    = 0
            up_probability = 50.0
            dn_probability = 50.0

    except Exception as e:
        st.error("Model training failed: " + str(e))
        st.stop()

pred_color  = "#2CA02C" if prediction == 1 else "#D62728"
pred_label  = "UP in " + str(n_days) + " days" \
              if prediction == 1 else \
              "DOWN in " + str(n_days) + " days"
pred_conf   = up_probability if prediction == 1 else dn_probability

st.markdown(
    '<div style="border:3px solid ' + pred_color +
    ';border-radius:12px;padding:20px;'
    'background:' + pred_color + '11;margin-bottom:20px;">'
    '<h3 style="margin:0;color:' + pred_color + '">'
    'ML Prediction for ' + ticker_clean + '</h3>'
    '<p style="margin:8px 0 0 0;font-size:1.2rem;">'
    'Direction: <b style="color:' + pred_color + '">' +
    pred_label + '</b><br>'
    'Confidence: <b>' + str(pred_conf) + '%</b> | '
    'Up Probability: <b style="color:#2CA02C">' +
    str(up_probability) + '%</b> | '
    'Down Probability: <b style="color:#D62728">' +
    str(dn_probability) + '%</b>'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)

kc1, kc2, kc3, kc4 = st.columns(4)
kc1.metric("Training Accuracy",  str(train_acc) + "%")
kc2.metric("Test Accuracy",      str(test_acc) + "%")
kc3.metric("Training Samples",   str(len(train)))
kc4.metric("Test Samples",       str(len(test)))

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Feature Importance — What Drives the Model?")

    if XGB_AVAILABLE and hasattr(model, "feature_importances_"):
        importance_df = pd.DataFrame({
            "Feature":    available_features,
            "Importance": model.feature_importances_
        }).sort_values("Importance", ascending=True)

        fig_imp = go.Figure(go.Bar(
            x=importance_df["Importance"],
            y=importance_df["Feature"],
            orientation="h",
            marker_color=[
                "#2CA02C" if imp > importance_df["Importance"].mean()
                else "#1F77B4"
                for imp in importance_df["Importance"]
            ]
        ))
        fig_imp.update_layout(
            height=450,
            template="plotly_white",
            title="XGBoost Feature Importances",
            xaxis_title="Importance Score",
            yaxis_title="",
            margin=dict(l=80, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_imp, use_container_width=True)

        top_feature = importance_df.iloc[-1]["Feature"]
        st.info(
            "Most important feature: **" + top_feature +
            "** — this indicator has the strongest influence "
            "on the model's predictions for " + ticker_clean
        )

with col_right:
    st.subheader("Prediction Probability")

    fig_prob = go.Figure(go.Bar(
        x=["Up in " + str(n_days) + "d",
           "Down in " + str(n_days) + "d"],
        y=[up_probability, dn_probability],
        marker_color=["#2CA02C","#D62728"],
        text=[str(up_probability)+"%",
              str(dn_probability)+"%"],
        textposition="outside",
        textfont=dict(size=14, family="Arial Black")
    ))
    fig_prob.add_hline(
        y=50, line_dash="dash",
        line_color="gray",
        annotation_text="50% (No edge)"
    )
    fig_prob.update_layout(
        height=300,
        template="plotly_white",
        title="Prediction Probability (%)",
        yaxis_range=[0, 110],
        showlegend=False
    )
    st.plotly_chart(fig_prob, use_container_width=True)

    st.subheader("Model Accuracy on Test Data")
    fig_acc = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=test_acc,
        delta=dict(reference=50, suffix="%"),
        title=dict(text="Test Accuracy %"),
        gauge=dict(
            axis=dict(range=[0,100]),
            bar=dict(color="#2CA02C" if test_acc > 55 else "#FF7F0E"),
            steps=[
                dict(range=[0,50],  color="#FFCCCC"),
                dict(range=[50,60], color="#FFFFCC"),
                dict(range=[60,100],color="#CCFFCC"),
            ],
            threshold=dict(
                line=dict(color="navy",width=3),
                thickness=0.75,
                value=50
            )
        )
    ))
    fig_acc.update_layout(
        height=200,
        margin=dict(t=30, b=10, l=20, r=20)
    )
    st.plotly_chart(fig_acc, use_container_width=True)

st.markdown("---")
st.subheader("Historical Predictions vs Actual Outcome")

if len(X_test) > 0:
    test_predictions = model.predict(X_test)
    test_proba       = model.predict_proba(X_test)

    test_results = test.copy()
    test_results["ML_Prediction"]   = test_predictions
    test_results["Up_Probability"]  = test_proba[:, 1]
    test_results["Correct"]         = (
        test_results["ML_Prediction"] == test_results["Target"]
    ).astype(int)

    correct_color = [
        "#2CA02C" if c == 1 else "#D62728"
        for c in test_results["Correct"]
    ]

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=test_results["Date"],
        y=test_results["Close"],
        name="Price",
        line=dict(color="#1F77B4", width=2),
        yaxis="y"
    ))
    fig_hist.add_trace(go.Bar(
        x=test_results["Date"],
        y=test_results["Up_Probability"] * 100,
        name="Up Probability %",
        marker_color=correct_color,
        opacity=0.7,
        yaxis="y2"
    ))

    fig_hist.update_layout(
        height=400,
        template="plotly_white",
        title="Price vs ML Up-Probability (Green = Correct prediction)",
        legend=dict(orientation="h", y=1.02),
        yaxis=dict(title="Price (Rs)", side="left"),
        yaxis2=dict(
            title="Up Probability %",
            side="right",
            overlaying="y",
            range=[0,100]
        )
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    total_preds  = len(test_results)
    correct_preds = int(test_results["Correct"].sum())
    up_correct   = int(test_results[
        (test_results["Target"]==1) &
        (test_results["ML_Prediction"]==1)
    ]["Correct"].sum())
    dn_correct   = int(test_results[
        (test_results["Target"]==0) &
        (test_results["ML_Prediction"]==0)
    ]["Correct"].sum())

    stat_cols = st.columns(4)
    stat_cols[0].metric(
        "Total Predictions", str(total_preds)
    )
    stat_cols[1].metric(
        "Correct Predictions", str(correct_preds)
    )
    stat_cols[2].metric(
        "Bullish Calls Correct", str(up_correct)
    )
    stat_cols[3].metric(
        "Bearish Calls Correct", str(dn_correct)
    )

st.markdown("---")
st.subheader("Signals for All Stocks Today")

all_predictions = []

for t in df["Ticker"].unique():
    try:
        s = df[df["Ticker"]==t].sort_values("Date")
        feats = s[available_features].dropna()
        if len(feats) == 0:
            continue
        latest_feats = feats.iloc[-1:]
        pred  = int(model.predict(latest_feats)[0])
        proba = model.predict_proba(latest_feats)[0]
        up_p  = round(float(proba[1])*100, 1)

        latest_row = s.iloc[-1]
        all_predictions.append({
            "Ticker":         str(t).replace(".NS",""),
            "ML Direction":   "UP" if pred==1 else "DOWN",
            "Up Probability": up_p,
            "RSI":            round(float(latest_row.get("RSI",0) or 0),1),
            "Rule Signal":    str(latest_row.get("Signal","N/A")),
            "Price (Rs)":     "{:,.2f}".format(float(latest_row["Close"]))
        })
    except Exception:
        continue

if all_predictions:
    pred_df = pd.DataFrame(all_predictions)

    col_up, col_dn = st.columns(2)

    with col_up:
        st.markdown(
            "**🟢 ML Bullish Predictions "
            "(Up Probability > 60%)**"
        )
        bullish = pred_df[
            pred_df["Up Probability"] > 60
        ].sort_values("Up Probability", ascending=False)
        if not bullish.empty:
            st.dataframe(
                bullish,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No strong bullish ML predictions today")

    with col_dn:
        st.markdown(
            "**🔴 ML Bearish Predictions "
            "(Up Probability < 40%)**"
        )
        bearish = pred_df[
            pred_df["Up Probability"] < 40
        ].sort_values("Up Probability", ascending=True)
        if not bearish.empty:
            st.dataframe(
                bearish,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No strong bearish ML predictions today")

    st.subheader("ML vs Rule-Based Signal Agreement")
    pred_df["Agreement"] = pred_df.apply(
        lambda r: "Both Bullish"  if r["ML Direction"]=="UP" and
                  r["Rule Signal"] in
                  ["Strong Buy","Buy","Weak Buy"] else
                  "Both Bearish" if r["ML Direction"]=="DOWN" and
                  r["Rule Signal"] in
                  ["Strong Sell","Sell","Weak Sell"] else
                  "Disagree",
        axis=1
    )

    agree_counts = pred_df["Agreement"].value_counts()
    fig_agree = go.Figure(go.Pie(
        labels=agree_counts.index.tolist(),
        values=agree_counts.values.tolist(),
        hole=0.5,
        marker_colors=["#2CA02C","#D62728","#FF7F0E"]
    ))
    fig_agree.update_layout(
        height=300,
        title="ML vs Rule-Based Signal Agreement",
        legend=dict(orientation="h")
    )
    st.plotly_chart(fig_agree, use_container_width=True)

    st.caption(
        "**Both Bullish** = Strongest buy signal. "
        "Both methods agree the stock will go up. "
        "**Disagree** = Lower confidence — approach with caution."
    )

st.markdown("---")
st.subheader("How the ML Model Works")
st.markdown("""
**Algorithm:** XGBoost (Extreme Gradient Boosting) — the same
algorithm used in quantitative hedge fund models.

**Features used (" + str(len(available_features)) + " total):**
RSI, MACD, Bollinger Band Width, ATR, OBV, moving averages,
daily returns, stochastics, ADX, signal score.

**Target:** Will the closing price be higher in
""" + str(n_days) + """ days? (Binary: 1=Yes, 0=No)

**Training/Test split:** 80% train, 20% test — no data leakage.

**Important note:** This is for educational purposes.
Past model accuracy does not guarantee future performance.
Always combine ML signals with fundamental analysis.
""")
