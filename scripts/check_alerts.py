"""
scripts/check_alerts.py

Checks predefined alert conditions against latest stock data.
Sends email notifications when conditions are triggered.
Run via GitHub Actions every 30 minutes during market hours.
"""

import pandas as pd
import numpy as np
import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

print("=" * 55)
print("  ALERT CHECKER")
print("  " + now.strftime("%d %b %Y %H:%M:%S") + " IST")
print("=" * 55)

DATA_DIR   = "streamlit_app/data"
ALERT_FILE = "scripts/alerts_config.json"

SENDER_EMAIL   = os.environ.get("ALERT_EMAIL",    "")
SENDER_PASS    = os.environ.get("ALERT_PASSWORD", "")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", SENDER_EMAIL)

DEFAULT_ALERTS = [
    {
        "name":        "RSI Oversold Alert",
        "type":        "rsi_below",
        "threshold":   30,
        "tickers":     "all",
        "description": "Alert when any NIFTY 50 stock RSI drops below 30"
    },
    {
        "name":        "RSI Overbought Alert",
        "type":        "rsi_above",
        "threshold":   75,
        "tickers":     "all",
        "description": "Alert when any NIFTY 50 stock RSI exceeds 75"
    },
    {
        "name":        "Strong Buy Signal Alert",
        "type":        "signal",
        "signal_val":  "Strong Buy",
        "tickers":     "all",
        "description": "Alert when any stock gets Strong Buy signal"
    },
    {
        "name":        "Strong Sell Signal Alert",
        "type":        "signal",
        "signal_val":  "Strong Sell",
        "tickers":     "all",
        "description": "Alert when any stock gets Strong Sell signal"
    }
]


def load_latest_data():
    signals_path = os.path.join(DATA_DIR, "latest_signals.csv")
    if not os.path.exists(signals_path):
        print("  ERROR: latest_signals.csv not found")
        return pd.DataFrame()
    df = pd.read_csv(signals_path)
    print("  Loaded " + str(len(df)) + " stocks from latest_signals.csv")
    return df


def check_all_alerts(df, alerts):
    triggered = []

    for alert in alerts:
        alert_type = alert.get("type", "")
        tickers    = alert.get("tickers", "all")

        if tickers == "all":
            check_df = df.copy()
        else:
            check_df = df[df["Ticker"].isin(tickers)].copy()

        if alert_type == "rsi_below":
            threshold  = float(alert.get("threshold", 30))
            triggered_stocks = check_df[
                check_df["RSI"].fillna(50) < threshold
            ]
            for _, row in triggered_stocks.iterrows():
                triggered.append({
                    "alert_name": alert["name"],
                    "ticker":     str(row["Ticker"]).replace(".NS",""),
                    "value":      round(float(row.get("RSI",0)), 1),
                    "message":    "RSI = " + str(round(float(row.get("RSI",0)),1)) +
                                  " (below " + str(threshold) + ")",
                    "signal":     str(row.get("Signal","N/A")),
                    "price":      round(float(row.get("Close",0)), 2)
                })

        elif alert_type == "rsi_above":
            threshold  = float(alert.get("threshold", 75))
            triggered_stocks = check_df[
                check_df["RSI"].fillna(50) > threshold
            ]
            for _, row in triggered_stocks.iterrows():
                triggered.append({
                    "alert_name": alert["name"],
                    "ticker":     str(row["Ticker"]).replace(".NS",""),
                    "value":      round(float(row.get("RSI",0)), 1),
                    "message":    "RSI = " + str(round(float(row.get("RSI",0)),1)) +
                                  " (above " + str(threshold) + ")",
                    "signal":     str(row.get("Signal","N/A")),
                    "price":      round(float(row.get("Close",0)), 2)
                })

        elif alert_type == "signal":
            signal_val = alert.get("signal_val", "Strong Buy")
            triggered_stocks = check_df[
                check_df["Signal"].fillna("") == signal_val
            ]
            for _, row in triggered_stocks.iterrows():
                triggered.append({
                    "alert_name": alert["name"],
                    "ticker":     str(row["Ticker"]).replace(".NS",""),
                    "value":      str(row.get("Signal_Score","N/A")),
                    "message":    "Signal = " + signal_val,
                    "signal":     signal_val,
                    "price":      round(float(row.get("Close",0)), 2)
                })

    return triggered


def send_email_alert(triggered_alerts):
    if not SENDER_EMAIL or not SENDER_PASS:
        print("  Email credentials not set — printing alerts only")
        for a in triggered_alerts:
            print(
                "  ALERT: " + a["alert_name"] +
                " | " + a["ticker"] +
                " | " + a["message"] +
                " | Price: Rs" + str(a["price"])
            )
        return

    subject = (
        "NIFTY 50 Alert: " + str(len(triggered_alerts)) +
        " conditions triggered — " +
        now.strftime("%d %b %Y %H:%M IST")
    )

    html_rows = ""
    for a in triggered_alerts:
        signal_color = (
            "#2CA02C" if "Buy"  in a.get("signal","") else
            "#D62728" if "Sell" in a.get("signal","") else
            "#666666"
        )
        html_rows += (
            "<tr>"
            "<td style='padding:8px;border:1px solid #ddd'><b>" +
            a["ticker"] + "</b></td>"
            "<td style='padding:8px;border:1px solid #ddd'>" +
            a["alert_name"] + "</td>"
            "<td style='padding:8px;border:1px solid #ddd'>" +
            a["message"] + "</td>"
            "<td style='padding:8px;border:1px solid #ddd;color:" +
            signal_color + "'><b>" + a.get("signal","N/A") + "</b></td>"
            "<td style='padding:8px;border:1px solid #ddd'>Rs" +
            str(a["price"]) + "</td>"
            "</tr>"
        )

    html_body = """
    <html><body>
    <div style="font-family:Arial,sans-serif;max-width:700px;">
    <div style="background:#1F3864;color:white;padding:20px;border-radius:8px;">
    <h2 style="margin:0">📈 NIFTY 50 Intelligence System</h2>
    <p style="margin:5px 0 0 0;opacity:0.85">
    """ + str(len(triggered_alerts)) + """ alert(s) triggered at """ + now.strftime("%H:%M IST") + """
    </p>
    </div>
    <table style="width:100%;border-collapse:collapse;margin-top:15px;">
    <tr style="background:#1F3864;color:white;">
    <th style="padding:10px;text-align:left">Stock</th>
    <th style="padding:10px;text-align:left">Alert</th>
    <th style="padding:10px;text-align:left">Condition</th>
    <th style="padding:10px;text-align:left">Signal</th>
    <th style="padding:10px;text-align:left">Price</th>
    </tr>
    """ + html_rows + """
    </table>
    <p style="color:#666;font-size:0.85rem;margin-top:15px;">
    View full analysis at <a href="https://investor01x.streamlit.app">
    investor01x.streamlit.app</a><br>
    Data as of """ + now.strftime("%d %b %Y %H:%M IST") + """
    </p>
    </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECEIVER_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASS)
            smtp.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("  Email sent to " + RECEIVER_EMAIL)
        print("  Subject: " + subject)
    except Exception as e:
        print("  Email failed: " + str(e))


df = load_latest_data()

if df.empty:
    print("  No data available — exiting")
    exit(0)

triggered = check_all_alerts(df, DEFAULT_ALERTS)

print("\n  Alerts triggered: " + str(len(triggered)))
for a in triggered:
    print(
        "    " + a["alert_name"] + " | " +
        a["ticker"] + " | " + a["message"]
    )

if triggered:
    send_email_alert(triggered)
else:
    print("  No alerts triggered today")

print("\n  Done")
