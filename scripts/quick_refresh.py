"""
scripts/quick_refresh.py

Daily data refresh for NIFTY 50 Intelligence System.
Uses curl_cffi to bypass Yahoo Finance bot detection on cloud servers.
Saves 7 CSV files to streamlit_app/data/
"""

import pandas as pd
import numpy as np
import ta
import os
import sys
import time
import warnings
import traceback
from datetime import datetime

warnings.filterwarnings("ignore")

OUTPUT_DIR = "streamlit_app/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

START_TIME = datetime.now()
print("=" * 60)
print(f"  NIFTY 50 QUICK REFRESH")
print(f"  Started: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Output:  {OUTPUT_DIR}")
print("=" * 60)

# ── Import yfinance with curl_cffi session ──────────────
try:
    from curl_cffi import requests as curl_requests
    import yfinance as yf
    session = curl_requests.Session(impersonate="chrome110")
    USE_SESSION = True
    print("  curl_cffi session ready — Yahoo Finance bypass active")
except Exception as e:
    try:
        import yfinance as yf
        session = None
        USE_SESSION = False
        print(f"  curl_cffi not available ({e}), using standard yfinance")
    except Exception as e2:
        print(f"  CRITICAL: yfinance not available: {e2}")
        sys.exit(1)

NIFTY_50 = [
    "RELIANCE.NS",  "TCS.NS",       "HDFCBANK.NS",  "INFY.NS",
    "ICICIBANK.NS", "HINDUNILVR.NS","ITC.NS",        "SBIN.NS",
    "BHARTIARTL.NS","KOTAKBANK.NS", "LT.NS",         "AXISBANK.NS",
    "ASIANPAINT.NS","MARUTI.NS",    "SUNPHARMA.NS",  "TITAN.NS",
    "ULTRACEMCO.NS","BAJFINANCE.NS","WIPRO.NS",      "ONGC.NS",
    "NTPC.NS",      "POWERGRID.NS", "TECHM.NS",      "HCLTECH.NS",
    "JSWSTEEL.NS",  "TATASTEEL.NS", "TATAMOTORS.NS", "NESTLEIND.NS",
    "DRREDDY.NS",   "DIVISLAB.NS",  "CIPLA.NS",      "COALINDIA.NS",
    "BPCL.NS",      "GRASIM.NS",    "ADANIENT.NS",   "ADANIPORTS.NS",
    "BAJAJFINSV.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS", "EICHERMOT.NS",
    "BRITANNIA.NS", "HINDALCO.NS",  "UPL.NS",        "SBILIFE.NS",
    "HDFCLIFE.NS",  "APOLLOHOSP.NS","TATACONSUM.NS", "INDUSINDBK.NS",
    "M&M.NS",       "LTF.NS"
]

SECTOR_MAP = {
    "RELIANCE.NS":"Energy",        "TCS.NS":"IT",
    "HDFCBANK.NS":"Banking",       "INFY.NS":"IT",
    "ICICIBANK.NS":"Banking",      "HINDUNILVR.NS":"FMCG",
    "ITC.NS":"FMCG",               "SBIN.NS":"Banking",
    "BHARTIARTL.NS":"Telecom",     "KOTAKBANK.NS":"Banking",
    "LT.NS":"Infrastructure",      "AXISBANK.NS":"Banking",
    "ASIANPAINT.NS":"Paints",      "MARUTI.NS":"Auto",
    "SUNPHARMA.NS":"Pharma",       "TITAN.NS":"Consumer",
    "ULTRACEMCO.NS":"Cement",      "BAJFINANCE.NS":"NBFC",
    "WIPRO.NS":"IT",               "ONGC.NS":"Energy",
    "NTPC.NS":"Power",             "POWERGRID.NS":"Power",
    "TECHM.NS":"IT",               "HCLTECH.NS":"IT",
    "JSWSTEEL.NS":"Steel",         "TATASTEEL.NS":"Steel",
    "TATAMOTORS.NS":"Auto",        "NESTLEIND.NS":"FMCG",
    "DRREDDY.NS":"Pharma",         "DIVISLAB.NS":"Pharma",
    "CIPLA.NS":"Pharma",           "COALINDIA.NS":"Mining",
    "BPCL.NS":"Energy",            "GRASIM.NS":"Cement",
    "ADANIENT.NS":"Conglomerate",  "ADANIPORTS.NS":"Ports",
    "BAJAJFINSV.NS":"NBFC",        "BAJAJ-AUTO.NS":"Auto",
    "HEROMOTOCO.NS":"Auto",        "EICHERMOT.NS":"Auto",
    "BRITANNIA.NS":"FMCG",         "HINDALCO.NS":"Metals",
    "UPL.NS":"Agrochemicals",      "SBILIFE.NS":"Insurance",
    "HDFCLIFE.NS":"Insurance",     "APOLLOHOSP.NS":"Healthcare",
    "TATACONSUM.NS":"FMCG",        "INDUSINDBK.NS":"Banking",
    "M&M.NS":"Auto",               "LTF.NS":"NBFC"
}

COMPANY_NAMES = {
    "RELIANCE.NS":"Reliance Industries",
    "TCS.NS":"TCS Tata Consultancy",
    "HDFCBANK.NS":"HDFC Bank",
    "INFY.NS":"Infosys",
    "ICICIBANK.NS":"ICICI Bank",
    "HINDUNILVR.NS":"Hindustan Unilever",
    "ITC.NS":"ITC Limited",
    "SBIN.NS":"State Bank India SBI",
    "BHARTIARTL.NS":"Bharti Airtel",
    "KOTAKBANK.NS":"Kotak Mahindra Bank",
    "LT.NS":"Larsen Toubro",
    "AXISBANK.NS":"Axis Bank",
    "ASIANPAINT.NS":"Asian Paints",
    "MARUTI.NS":"Maruti Suzuki",
    "SUNPHARMA.NS":"Sun Pharma",
    "TITAN.NS":"Titan Company",
    "ULTRACEMCO.NS":"UltraTech Cement",
    "BAJFINANCE.NS":"Bajaj Finance",
    "WIPRO.NS":"Wipro",
    "ONGC.NS":"ONGC Oil Gas",
    "NTPC.NS":"NTPC Power",
    "POWERGRID.NS":"Power Grid India",
    "TECHM.NS":"Tech Mahindra",
    "HCLTECH.NS":"HCL Technologies",
    "JSWSTEEL.NS":"JSW Steel",
    "TATASTEEL.NS":"Tata Steel",
    "TATAMOTORS.NS":"Tata Motors",
    "NESTLEIND.NS":"Nestle India",
    "DRREDDY.NS":"Dr Reddys Laboratories",
    "DIVISLAB.NS":"Divis Laboratories",
    "CIPLA.NS":"Cipla Pharma",
    "COALINDIA.NS":"Coal India",
    "BPCL.NS":"BPCL Bharat Petroleum",
    "GRASIM.NS":"Grasim Industries",
    "ADANIENT.NS":"Adani Enterprises",
    "ADANIPORTS.NS":"Adani Ports",
    "BAJAJFINSV.NS":"Bajaj Finserv",
    "BAJAJ-AUTO.NS":"Bajaj Auto",
    "HEROMOTOCO.NS":"Hero MotoCorp",
    "EICHERMOT.NS":"Eicher Motors",
    "BRITANNIA.NS":"Britannia Industries",
    "HINDALCO.NS":"Hindalco Aluminium",
    "UPL.NS":"UPL Agrochemicals",
    "SBILIFE.NS":"SBI Life Insurance",
    "HDFCLIFE.NS":"HDFC Life Insurance",
    "APOLLOHOSP.NS":"Apollo Hospitals",
    "TATACONSUM.NS":"Tata Consumer Products",
    "INDUSINDBK.NS":"IndusInd Bank",
    "M&M.NS":"Mahindra Mahindra",
    "LTF.NS":"L&T Finance"
}


def save_csv(df, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False)
    size = os.path.getsize(path) / 1024
    print(f"  SAVED  {filename:<47}  {len(df):>6} rows  {size:>7.1f} KB")
    return path


def fetch_ticker_data(ticker):
    for attempt in range(3):
        try:
            if USE_SESSION:
                ticker_obj = yf.Ticker(ticker, session=session)
            else:
                ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period="1y", auto_adjust=True)
            if not df.empty:
                return df, None
            raise ValueError("Empty dataframe")
        except Exception as e:
            if attempt < 2:
                wait = (attempt + 1) * 5
                print(f"  RETRY [{attempt+1}/2] {ticker} — waiting {wait}s")
                time.sleep(wait)
            else:
                return None, str(e)
    return None, "Max retries exceeded"


# ════════════════════════════════════════
# STEP 1 — FETCH PRICE DATA
# ════════════════════════════════════════
print(f"\n[STEP 1/4] Fetching 1-year price history...")
print("-" * 60)

all_data = []
failed   = []

for i, ticker in enumerate(NIFTY_50, 1):
    df, error = fetch_ticker_data(ticker)
    if df is not None:
        df["Ticker"] = ticker
        df["Sector"] = SECTOR_MAP.get(ticker, "Unknown")
        df.reset_index(inplace=True)
        all_data.append(df)
        print(f"  OK  [{i:02d}/{len(NIFTY_50)}]  {ticker:<22}  {len(df)} rows")
    else:
        print(f"  FAIL [{i:02d}/{len(NIFTY_50)}]  {ticker:<22}  {error}")
        failed.append(ticker)
    time.sleep(0.4)

print(f"\n  Fetched: {len(all_data)}/{len(NIFTY_50)} stocks")

if not all_data:
    print("CRITICAL: No data fetched. Stopping.")
    sys.exit(1)

raw_df = pd.concat(all_data, ignore_index=True)
raw_df["Date"] = pd.to_datetime(raw_df["Date"])

if hasattr(raw_df["Date"].dt, "tz") and raw_df["Date"].dt.tz is not None:
    raw_df["Date"] = raw_df["Date"].dt.tz_localize(None)

raw_df = raw_df[
    ["Date","Ticker","Sector","Open","High","Low","Close","Volume"]
].copy()
raw_df.drop_duplicates(subset=["Date","Ticker"], inplace=True)
raw_df.dropna(subset=["Close"], inplace=True)
raw_df.sort_values(["Ticker","Date"], inplace=True)
raw_df["Daily_Return"] = (
    raw_df.groupby("Ticker")["Close"].pct_change().round(4)
)
raw_df["Price_Change"]     = (raw_df["Close"] - raw_df["Open"]).round(2)
raw_df["Price_Change_Pct"] = (
    (raw_df["Price_Change"] / raw_df["Open"]) * 100
).round(2)
raw_df.reset_index(drop=True, inplace=True)

latest_date = raw_df["Date"].max()
print(f"  Latest date in data: {latest_date.date()}")
print(f"  Total rows: {len(raw_df):,}")

save_csv(raw_df, "nifty50_for_powerbi.csv")

latest_day = raw_df[raw_df["Date"] == latest_date].copy()
save_csv(latest_day, "nifty50_latest_day.csv")


# ════════════════════════════════════════
# STEP 2 — TECHNICAL ANALYSIS
# ════════════════════════════════════════
print(f"\n[STEP 2/4] Computing technical indicators...")
print("-" * 60)

tech_results = []
tech_failed  = []

for i, ticker in enumerate(raw_df["Ticker"].unique(), 1):
    try:
        s = (
            raw_df[raw_df["Ticker"] == ticker]
            .copy()
            .sort_values("Date")
            .reset_index(drop=True)
        )
        if len(s) < 30:
            continue

        s["SMA_20"]      = ta.trend.SMAIndicator(s["Close"], 20).sma_indicator()
        s["SMA_50"]      = ta.trend.SMAIndicator(s["Close"], 50).sma_indicator()
        s["SMA_200"]     = ta.trend.SMAIndicator(s["Close"], 200).sma_indicator()
        s["EMA_20"]      = ta.trend.EMAIndicator(s["Close"], 20).ema_indicator()
        s["EMA_26"]      = ta.trend.EMAIndicator(s["Close"], 26).ema_indicator()
        macd_obj         = ta.trend.MACD(s["Close"])
        s["MACD"]        = macd_obj.macd()
        s["MACD_Signal"] = macd_obj.macd_signal()
        s["MACD_Hist"]   = macd_obj.macd_diff()
        s["ADX"]         = ta.trend.ADXIndicator(
            s["High"], s["Low"], s["Close"]
        ).adx()
        s["RSI"]         = ta.momentum.RSIIndicator(s["Close"], 14).rsi()
        stoch            = ta.momentum.StochasticOscillator(
            s["High"], s["Low"], s["Close"]
        )
        s["Stoch_K"]     = stoch.stoch()
        s["Stoch_D"]     = stoch.stoch_signal()
        bb               = ta.volatility.BollingerBands(s["Close"])
        s["BB_Upper"]    = bb.bollinger_hband()
        s["BB_Middle"]   = bb.bollinger_mavg()
        s["BB_Lower"]    = bb.bollinger_lband()
        s["BB_Width"]    = bb.bollinger_wband()
        s["ATR"]         = ta.volatility.AverageTrueRange(
            s["High"], s["Low"], s["Close"]
        ).average_true_range()
        s["OBV"]         = ta.volume.OnBalanceVolumeIndicator(
            s["Close"], s["Volume"]
        ).on_balance_volume()

        s["Signal_Score"] = 0
        s.loc[s["RSI"] < 30,                "Signal_Score"] += 2
        s.loc[s["RSI"] > 70,                "Signal_Score"] -= 2
        s.loc[s["MACD"] > s["MACD_Signal"], "Signal_Score"] += 1
        s.loc[s["MACD"] < s["MACD_Signal"], "Signal_Score"] -= 1
        s.loc[s["Close"] > s["SMA_50"],     "Signal_Score"] += 1
        s.loc[s["Close"] < s["SMA_50"],     "Signal_Score"] -= 1
        s.loc[s["Close"] > s["SMA_200"],    "Signal_Score"] += 1
        s.loc[s["Close"] < s["SMA_200"],    "Signal_Score"] -= 1
        s.loc[s["Close"] < s["BB_Lower"],   "Signal_Score"] += 1
        s.loc[s["Close"] > s["BB_Upper"],   "Signal_Score"] -= 1

        s["Signal"] = "Neutral"
        s.loc[s["Signal_Score"] >=  3, "Signal"] = "Strong Buy"
        s.loc[s["Signal_Score"] ==  2, "Signal"] = "Buy"
        s.loc[s["Signal_Score"] ==  1, "Signal"] = "Weak Buy"
        s.loc[s["Signal_Score"] == -1, "Signal"] = "Weak Sell"
        s.loc[s["Signal_Score"] == -2, "Signal"] = "Sell"
        s.loc[s["Signal_Score"] <= -3, "Signal"] = "Strong Sell"

        s["RSI_Signal"] = "Neutral"
        s.loc[s["RSI"] < 30, "RSI_Signal"] = "Oversold"
        s.loc[s["RSI"] > 70, "RSI_Signal"] = "Overbought"

        tech_results.append(s)
        sig = s["Signal"].iloc[-1]
        rsi = round(float(s["RSI"].iloc[-1]), 1)
        print(f"  OK  [{i:02d}]  {ticker:<22}  signal: {sig:<12}  RSI: {rsi}")

    except Exception as e:
        tech_failed.append(ticker)
        print(f"  FAIL  {ticker}  {e}")

if not tech_results:
    print("CRITICAL: No technical results. Stopping.")
    sys.exit(1)

tech_df = pd.concat(tech_results, ignore_index=True)
save_csv(tech_df, "nifty50_technical_powerbi.csv")

latest_signals = tech_df.groupby("Ticker").last().reset_index()
save_csv(latest_signals, "latest_signals.csv")


# ════════════════════════════════════════
# STEP 3 — SENTIMENT ANALYSIS
# ════════════════════════════════════════
print(f"\n[STEP 3/4] Fetching news sentiment...")
print("-" * 60)

try:
    import feedparser
    from textblob import TextBlob

    sent_rows = []
    hl_rows   = []

    for i, (ticker, company) in enumerate(COMPANY_NAMES.items(), 1):
        try:
            query = company.replace(" ", "+") + "+NSE+stock+India"
            url   = (
                f"https://news.google.com/rss/search?"
                f"q={query}&hl=en-IN&gl=IN&ceid=IN:en"
            )
            feed      = feedparser.parse(url)
            headlines = []

            for entry in feed.entries[:8]:
                title = entry.title
                if " - " in title:
                    title = title.rsplit(" - ", 1)[0]
                title = title.strip()
                if 10 < len(title) < 300:
                    headlines.append(title)

            polarities    = []
            bullish = bearish = neutral_count = 0

            for h in headlines:
                try:
                    pol = float(TextBlob(h).sentiment.polarity)
                except Exception:
                    pol = 0.0
                polarities.append(pol)

                if pol > 0.05:
                    label   = "positive"
                    bullish += 1
                elif pol < -0.05:
                    label   = "negative"
                    bearish += 1
                else:
                    label         = "neutral"
                    neutral_count += 1

                hl_rows.append({
                    "Ticker":     ticker,
                    "Company":    company,
                    "Headline":   h,
                    "Label":      label,
                    "Confidence": round(min(abs(pol) + 0.5, 1.0), 4),
                    "Polarity":   round(pol, 4),
                    "Model":      "TextBlob"
                })

            avg_pol = round(
                sum(polarities) / len(polarities), 4
            ) if polarities else 0.0
            score   = round((avg_pol + 1) / 2 * 100, 1)

            if avg_pol >= 0.4:    lbl = "Very Positive"
            elif avg_pol >= 0.15: lbl = "Positive"
            elif avg_pol <= -0.4: lbl = "Very Negative"
            elif avg_pol <= -0.15:lbl = "Negative"
            else:                 lbl = "Neutral"

            sent_rows.append({
                "Ticker":          ticker,
                "Company":         company,
                "Avg_Polarity":    avg_pol,
                "Sentiment_Label": lbl,
                "Sentiment_Score": score,
                "Bullish_Count":   bullish,
                "Bearish_Count":   bearish,
                "Neutral_Count":   neutral_count,
                "Avg_Confidence":  round(min(abs(avg_pol) + 0.5, 1.0), 3),
                "Total_Articles":  len(headlines)
            })

            print(f"  OK  [{i:02d}/{len(COMPANY_NAMES)}]  {ticker:<22}  {lbl}")
            time.sleep(0.25)

        except Exception as e:
            print(f"  FAIL  {ticker}  {e}")
            sent_rows.append({
                "Ticker":ticker,"Company":company,
                "Avg_Polarity":0.0,"Sentiment_Label":"Neutral",
                "Sentiment_Score":50.0,"Bullish_Count":0,
                "Bearish_Count":0,"Neutral_Count":0,
                "Avg_Confidence":0.5,"Total_Articles":0
            })

    save_csv(pd.DataFrame(sent_rows), "nifty50_sentiment_powerbi.csv")
    save_csv(pd.DataFrame(hl_rows),   "nifty50_headlines_powerbi.csv")

except Exception as e:
    print(f"  Sentiment step failed: {e}")
    pd.DataFrame(columns=[
        "Ticker","Company","Avg_Polarity","Sentiment_Label",
        "Sentiment_Score","Bullish_Count","Bearish_Count",
        "Neutral_Count","Avg_Confidence","Total_Articles"
    ]).to_csv(
        os.path.join(OUTPUT_DIR, "nifty50_sentiment_powerbi.csv"),
        index=False
    )
    pd.DataFrame(columns=[
        "Ticker","Company","Headline","Label",
        "Confidence","Polarity","Model"
    ]).to_csv(
        os.path.join(OUTPUT_DIR, "nifty50_headlines_powerbi.csv"),
        index=False
    )


# ════════════════════════════════════════
# STEP 4 — RISK METRICS
# ════════════════════════════════════════
print(f"\n[STEP 4/4] Computing risk metrics...")
print("-" * 60)

try:
    returns_pivot  = tech_df.pivot_table(
        index="Date", columns="Ticker", values="Daily_Return"
    )
    market_returns = returns_pivot.mean(axis=1)
    market_var     = float(market_returns.var())
    rf             = 0.065
    td             = 252
    risk_rows      = []

    for ticker in returns_pivot.columns:
        try:
            r = returns_pivot[ticker].dropna()
            if len(r) < 30:
                continue

            ann_ret = round((1 + r.mean()) ** td - 1, 4)
            ann_vol = round(r.std() * np.sqrt(td), 4)
            sharpe  = round(
                (ann_ret - rf) / ann_vol, 3
            ) if ann_vol > 0 else 0.0

            cum    = (1 + r).cumprod()
            max_dd = round(
                float(((cum - cum.cummax()) / cum.cummax()).min()) * 100, 2
            )

            thresh  = float(np.percentile(r, 5))
            var_95  = round(thresh * 100, 3)
            tail    = r[r <= thresh]
            cvar_95 = round(float(tail.mean()) * 100, 3) \
                      if len(tail) > 0 else var_95

            mkt_a, r_a = market_returns.align(r, join="inner")
            cov_m      = np.cov(r_a.values, mkt_a.values)
            beta       = round(
                cov_m[0][1] / market_var, 3
            ) if market_var > 0 else 1.0

            prices = tech_df[tech_df["Ticker"] == ticker]["Close"]
            curr   = round(float(prices.iloc[-1]), 2)
            h52    = round(float(prices.tail(252).max()), 2)
            l52    = round(float(prices.tail(252).min()), 2)

            risk_rows.append({
                "Ticker":             ticker,
                "Ann_Return_Pct":     round(ann_ret * 100, 2),
                "Ann_Volatility_Pct": round(ann_vol * 100, 2),
                "Sharpe_Ratio":       sharpe,
                "Max_Drawdown_Pct":   max_dd,
                "VaR_95_Pct":         var_95,
                "CVaR_95_Pct":        cvar_95,
                "Beta":               beta,
                "Current_Price":      curr,
                "52W_High":           h52,
                "52W_Low":            l52,
                "From_52W_High_Pct":  round((curr - h52) / h52 * 100, 2)
            })
            print(
                f"  OK  {ticker:<22}  "
                f"Sharpe: {sharpe:>6.3f}  "
                f"Return: {ann_ret*100:>+7.2f}%"
            )
        except Exception as e:
            print(f"  FAIL  {ticker}  {e}")

    pd.DataFrame(risk_rows).sort_values(
        "Sharpe_Ratio", ascending=False
    ).to_csv(
        os.path.join(OUTPUT_DIR, "nifty50_risk_metrics_powerbi.csv"),
        index=False
    )
    print(f"  SAVED  nifty50_risk_metrics_powerbi.csv  {len(risk_rows)} stocks")

except Exception as e:
    print(f"  Risk step failed: {e}")
    traceback.print_exc()


# ════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════
end_time = datetime.now()
duration = (end_time - START_TIME).seconds

print("\n" + "=" * 60)
print(f"  REFRESH COMPLETE")
print(f"  Finished:  {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Duration:  {duration // 60}m {duration % 60}s")
print(f"  Data date: {latest_date.date()}")
print("=" * 60)

expected = [
    "nifty50_for_powerbi.csv",
    "nifty50_latest_day.csv",
    "nifty50_technical_powerbi.csv",
    "latest_signals.csv",
    "nifty50_sentiment_powerbi.csv",
    "nifty50_headlines_powerbi.csv",
    "nifty50_risk_metrics_powerbi.csv",
]

all_ok = True
print(f"\n  {'File':<47}  {'Rows':>6}  {'Size':>8}  Status")
print(f"  {'-'*70}")

for fname in expected:
    fpath = os.path.join(OUTPUT_DIR, fname)
    if os.path.exists(fpath):
        try:
            rows = len(pd.read_csv(fpath))
            size = os.path.getsize(fpath) / 1024
            ok   = rows > 0
            if not ok:
                all_ok = False
            print(
                f"  {fname:<47}  {rows:>6}  "
                f"{size:>7.1f}KB  {'OK' if ok else 'EMPTY'}"
            )
        except Exception as e:
            print(f"  {fname:<47}  ERROR: {e}")
            all_ok = False
    else:
        print(f"  {fname:<47}  MISSING")
        all_ok = False

print(f"\n  {'ALL FILES OK' if all_ok else 'SOME FILES HAVE ISSUES'}")
if failed:
    print(f"  Price fetch failures: {failed}")
print("=" * 60)

if not all_ok:
    sys.exit(1)
