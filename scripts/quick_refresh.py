"""
quick_refresh.py
Runs daily via GitHub Actions.
Fetches fresh NIFTY 50 data and saves CSVs to streamlit_app/data/
Does NOT run Prophet (too slow) — just price data, signals, sentiment
"""

import pandas as pd
import numpy as np
import yfinance as yf
import ta
import os
import warnings
import feedparser
import time
from datetime import datetime

warnings.filterwarnings("ignore")

# Output folder — where Streamlit reads data from
OUTPUT_DIR = "streamlit_app/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Starting quick refresh at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Output folder: {OUTPUT_DIR}\n")

# ── Stock list ──
NIFTY_50 = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
    "HINDUNILVR.NS","ITC.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS",
    "LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS",
    "TITAN.NS","ULTRACEMCO.NS","BAJFINANCE.NS","WIPRO.NS","ONGC.NS",
    "NTPC.NS","POWERGRID.NS","TECHM.NS","HCLTECH.NS","JSWSTEEL.NS",
    "TATASTEEL.NS","TATAMOTORS.NS","NESTLEIND.NS","DRREDDY.NS","DIVISLAB.NS",
    "CIPLA.NS","COALINDIA.NS","BPCL.NS","GRASIM.NS","ADANIENT.NS",
    "ADANIPORTS.NS","BAJAJFINSV.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS",
    "EICHERMOT.NS","BRITANNIA.NS","HINDALCO.NS","UPL.NS","SBILIFE.NS",
    "HDFCLIFE.NS","APOLLOHOSP.NS","TATACONSUM.NS","INDUSINDBK.NS",
    "M&M.NS","LTF.NS"
]

SECTOR_MAP = {
    "RELIANCE.NS":"Energy","TCS.NS":"IT","HDFCBANK.NS":"Banking",
    "INFY.NS":"IT","ICICIBANK.NS":"Banking","HINDUNILVR.NS":"FMCG",
    "ITC.NS":"FMCG","SBIN.NS":"Banking","BHARTIARTL.NS":"Telecom",
    "KOTAKBANK.NS":"Banking","LT.NS":"Infrastructure","AXISBANK.NS":"Banking",
    "ASIANPAINT.NS":"Paints","MARUTI.NS":"Auto","SUNPHARMA.NS":"Pharma",
    "TITAN.NS":"Consumer","ULTRACEMCO.NS":"Cement","BAJFINANCE.NS":"NBFC",
    "WIPRO.NS":"IT","ONGC.NS":"Energy","NTPC.NS":"Power",
    "POWERGRID.NS":"Power","TECHM.NS":"IT","HCLTECH.NS":"IT",
    "JSWSTEEL.NS":"Steel","TATASTEEL.NS":"Steel","TATAMOTORS.NS":"Auto",
    "NESTLEIND.NS":"FMCG","DRREDDY.NS":"Pharma","DIVISLAB.NS":"Pharma",
    "CIPLA.NS":"Pharma","COALINDIA.NS":"Mining","BPCL.NS":"Energy",
    "GRASIM.NS":"Cement","ADANIENT.NS":"Conglomerate","ADANIPORTS.NS":"Ports",
    "BAJAJFINSV.NS":"NBFC","BAJAJ-AUTO.NS":"Auto","HEROMOTOCO.NS":"Auto",
    "EICHERMOT.NS":"Auto","BRITANNIA.NS":"FMCG","HINDALCO.NS":"Metals",
    "UPL.NS":"Agrochemicals","SBILIFE.NS":"Insurance","HDFCLIFE.NS":"Insurance",
    "APOLLOHOSP.NS":"Healthcare","TATACONSUM.NS":"FMCG",
    "INDUSINDBK.NS":"Banking","M&M.NS":"Auto","LTF.NS":"NBFC"
}

COMPANY_NAMES = {
    "RELIANCE.NS":"Reliance Industries","TCS.NS":"TCS Tata Consultancy",
    "HDFCBANK.NS":"HDFC Bank","INFY.NS":"Infosys",
    "ICICIBANK.NS":"ICICI Bank","HINDUNILVR.NS":"Hindustan Unilever",
    "ITC.NS":"ITC Limited","SBIN.NS":"State Bank India",
    "BHARTIARTL.NS":"Bharti Airtel","KOTAKBANK.NS":"Kotak Mahindra Bank",
    "LT.NS":"Larsen Toubro","AXISBANK.NS":"Axis Bank",
    "ASIANPAINT.NS":"Asian Paints","MARUTI.NS":"Maruti Suzuki",
    "SUNPHARMA.NS":"Sun Pharma","TITAN.NS":"Titan Company",
    "ULTRACEMCO.NS":"UltraTech Cement","BAJFINANCE.NS":"Bajaj Finance",
    "WIPRO.NS":"Wipro","ONGC.NS":"ONGC","NTPC.NS":"NTPC",
    "POWERGRID.NS":"Power Grid","TECHM.NS":"Tech Mahindra",
    "HCLTECH.NS":"HCL Technologies","JSWSTEEL.NS":"JSW Steel",
    "TATASTEEL.NS":"Tata Steel","TATAMOTORS.NS":"Tata Motors",
    "NESTLEIND.NS":"Nestle India","DRREDDY.NS":"Dr Reddys",
    "DIVISLAB.NS":"Divis Laboratories","CIPLA.NS":"Cipla",
    "COALINDIA.NS":"Coal India","BPCL.NS":"BPCL",
    "GRASIM.NS":"Grasim","ADANIENT.NS":"Adani Enterprises",
    "ADANIPORTS.NS":"Adani Ports","BAJAJFINSV.NS":"Bajaj Finserv",
    "BAJAJ-AUTO.NS":"Bajaj Auto","HEROMOTOCO.NS":"Hero MotoCorp",
    "EICHERMOT.NS":"Eicher Motors","BRITANNIA.NS":"Britannia",
    "HINDALCO.NS":"Hindalco","UPL.NS":"UPL",
    "SBILIFE.NS":"SBI Life","HDFCLIFE.NS":"HDFC Life",
    "APOLLOHOSP.NS":"Apollo Hospitals","TATACONSUM.NS":"Tata Consumer",
    "INDUSINDBK.NS":"IndusInd Bank","M&M.NS":"Mahindra",
    "LTF.NS":"L&T Finance"
}

# ════════════════════════════════════════
# STEP 1 — Fetch Price Data
# ════════════════════════════════════════
print("STEP 1: Fetching price data from Yahoo Finance...")

all_data = []
failed   = []

for i, ticker in enumerate(NIFTY_50, 1):
    try:
        df = yf.Ticker(ticker).history(period="1y")
        if df.empty:
            failed.append(ticker)
            print(f"  ⚠️  [{i:02d}] {ticker} — no data")
            continue
        df["Ticker"] = ticker
        df["Sector"] = SECTOR_MAP.get(ticker, "Unknown")
        df.reset_index(inplace=True)
        all_data.append(df)
        print(f"  ✅ [{i:02d}] {ticker} — {len(df)} rows")
    except Exception as e:
        failed.append(ticker)
        print(f"  ❌ [{i:02d}] {ticker} — {e}")

if not all_data:
    print("❌ No data fetched — stopping")
    exit(1)

raw_df = pd.concat(all_data, ignore_index=True)
raw_df["Date"] = pd.to_datetime(raw_df["Date"]).dt.tz_localize(None)
raw_df = raw_df[["Date","Ticker","Sector","Open","High","Low","Close","Volume"]]
raw_df.drop_duplicates(subset=["Date","Ticker"], inplace=True)
raw_df.dropna(subset=["Close"], inplace=True)
raw_df.sort_values(["Ticker","Date"], inplace=True)
raw_df["Daily_Return"]     = raw_df.groupby("Ticker")["Close"].pct_change().round(4)
raw_df["Price_Change"]     = (raw_df["Close"] - raw_df["Open"]).round(2)
raw_df["Price_Change_Pct"] = ((raw_df["Price_Change"]/raw_df["Open"])*100).round(2)
raw_df.reset_index(drop=True, inplace=True)

raw_df.to_csv(f"{OUTPUT_DIR}/nifty50_for_powerbi.csv", index=False)
print(f"\n  💾 nifty50_for_powerbi.csv — {len(raw_df):,} rows")

latest_day = raw_df[raw_df["Date"]==raw_df["Date"].max()].copy()
latest_day.to_csv(f"{OUTPUT_DIR}/nifty50_latest_day.csv", index=False)
print(f"  💾 nifty50_latest_day.csv — {len(latest_day)} rows")

# ════════════════════════════════════════
# STEP 2 — Technical Analysis
# ════════════════════════════════════════
print("\nSTEP 2: Computing technical indicators...")

tech_results = []

for i, ticker in enumerate(raw_df["Ticker"].unique(), 1):
    try:
        s = raw_df[raw_df["Ticker"]==ticker].copy().sort_values("Date")

        s["SMA_20"]      = ta.trend.SMAIndicator(s["Close"],20).sma_indicator()
        s["SMA_50"]      = ta.trend.SMAIndicator(s["Close"],50).sma_indicator()
        s["SMA_200"]     = ta.trend.SMAIndicator(s["Close"],200).sma_indicator()
        s["EMA_20"]      = ta.trend.EMAIndicator(s["Close"],20).ema_indicator()
        s["EMA_26"]      = ta.trend.EMAIndicator(s["Close"],26).ema_indicator()
        macd             = ta.trend.MACD(s["Close"])
        s["MACD"]        = macd.macd()
        s["MACD_Signal"] = macd.macd_signal()
        s["MACD_Hist"]   = macd.macd_diff()
        s["ADX"]         = ta.trend.ADXIndicator(s["High"],s["Low"],s["Close"]).adx()
        s["RSI"]         = ta.momentum.RSIIndicator(s["Close"],14).rsi()
        stoch            = ta.momentum.StochasticOscillator(s["High"],s["Low"],s["Close"])
        s["Stoch_K"]     = stoch.stoch()
        s["Stoch_D"]     = stoch.stoch_signal()
        bb               = ta.volatility.BollingerBands(s["Close"])
        s["BB_Upper"]    = bb.bollinger_hband()
        s["BB_Middle"]   = bb.bollinger_mavg()
        s["BB_Lower"]    = bb.bollinger_lband()
        s["BB_Width"]    = bb.bollinger_wband()
        s["ATR"]         = ta.volatility.AverageTrueRange(s["High"],s["Low"],s["Close"]).average_true_range()
        s["OBV"]         = ta.volume.OnBalanceVolumeIndicator(s["Close"],s["Volume"]).on_balance_volume()

        # Signal scoring
        s["Signal_Score"] = 0
        s.loc[s["RSI"]<30,                        "Signal_Score"] += 2
        s.loc[s["RSI"]>70,                        "Signal_Score"] -= 2
        s.loc[s["MACD"]>s["MACD_Signal"],         "Signal_Score"] += 1
        s.loc[s["MACD"]<s["MACD_Signal"],         "Signal_Score"] -= 1
        s.loc[s["Close"]>s["SMA_50"],             "Signal_Score"] += 1
        s.loc[s["Close"]<s["SMA_50"],             "Signal_Score"] -= 1
        s.loc[s["Close"]>s["SMA_200"],            "Signal_Score"] += 1
        s.loc[s["Close"]<s["SMA_200"],            "Signal_Score"] -= 1
        s.loc[s["Close"]<s["BB_Lower"],           "Signal_Score"] += 1
        s.loc[s["Close"]>s["BB_Upper"],           "Signal_Score"] -= 1

        s["Signal"] = "Neutral"
        s.loc[s["Signal_Score"]>=3,  "Signal"] = "Strong Buy"
        s.loc[s["Signal_Score"]==2,  "Signal"] = "Buy"
        s.loc[s["Signal_Score"]==1,  "Signal"] = "Weak Buy"
        s.loc[s["Signal_Score"]==-1, "Signal"] = "Weak Sell"
        s.loc[s["Signal_Score"]==-2, "Signal"] = "Sell"
        s.loc[s["Signal_Score"]<=-3, "Signal"] = "Strong Sell"

        tech_results.append(s)
        print(f"  ✅ [{i:02d}] {ticker} — signal: {s['Signal'].iloc[-1]}")

    except Exception as e:
        print(f"  ❌ {ticker} — {e}")

tech_df = pd.concat(tech_results, ignore_index=True)
tech_df.to_csv(f"{OUTPUT_DIR}/nifty50_technical_powerbi.csv", index=False)
print(f"\n  💾 nifty50_technical_powerbi.csv — {len(tech_df):,} rows")

latest_signals = tech_df.groupby("Ticker").last().reset_index()
latest_signals.to_csv(f"{OUTPUT_DIR}/latest_signals.csv", index=False)
print(f"  💾 latest_signals.csv — {len(latest_signals)} rows")

# ════════════════════════════════════════
# STEP 3 — Basic Sentiment (TextBlob only)
# Note: FinBERT too heavy for GitHub Actions
# ════════════════════════════════════════
print("\nSTEP 3: Fetching sentiment from Google News...")

try:
    from textblob import TextBlob

    sentiment_rows = []
    headline_rows  = []

    for i, (ticker, company) in enumerate(COMPANY_NAMES.items(), 1):
        try:
            query    = company.replace(" ","+") + "+NSE+stock+India"
            url      = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
            feed     = feedparser.parse(url)
            headlines = []

            for entry in feed.entries[:8]:
                title = entry.title
                if " - " in title:
                    title = title.rsplit(" - ",1)[0]
                if 10 < len(title) < 300:
                    headlines.append(title)

            if not headlines:
                sentiment_rows.append({
                    "Ticker":ticker,"Company":company,
                    "Avg_Polarity":0,"Sentiment_Label":"Neutral",
                    "Sentiment_Score":50,"Bullish_Count":0,
                    "Bearish_Count":0,"Neutral_Count":0,
                    "Avg_Confidence":0.5,"Total_Articles":0
                })
                continue

            polarities = []
            bullish = bearish = neutral = 0

            for h in headlines:
                pol = TextBlob(h).sentiment.polarity
                polarities.append(pol)
                if pol > 0.05:   bullish  += 1
                elif pol < -0.05: bearish += 1
                else:             neutral += 1
                headline_rows.append({
                    "Ticker":ticker,"Company":company,
                    "Headline":h,"Label":"positive" if pol>0.05 else "negative" if pol<-0.05 else "neutral",
                    "Confidence":min(abs(pol)+0.5,1.0),"Polarity":round(pol,4),"Model":"TextBlob"
                })

            avg_pol = round(sum(polarities)/len(polarities),4)
            score   = round((avg_pol+1)/2*100,1)
            lbl     = ("Very Positive" if avg_pol>=0.4 else "Positive" if avg_pol>=0.15 else
                       "Very Negative" if avg_pol<=-0.4 else "Negative" if avg_pol<=-0.15 else "Neutral")

            sentiment_rows.append({
                "Ticker":ticker,"Company":company,
                "Avg_Polarity":avg_pol,"Sentiment_Label":lbl,
                "Sentiment_Score":score,"Bullish_Count":bullish,
                "Bearish_Count":bearish,"Neutral_Count":neutral,
                "Avg_Confidence":round(min(abs(avg_pol)+0.5,1.0),3),
                "Total_Articles":len(headlines)
            })

            print(f"  ✅ [{i:02d}] {ticker} — {lbl} ({score})")
            time.sleep(0.3)

        except Exception as e:
            print(f"  ❌ {ticker} — {e}")
            sentiment_rows.append({
                "Ticker":ticker,"Company":company,
                "Avg_Polarity":0,"Sentiment_Label":"Neutral",
                "Sentiment_Score":50,"Bullish_Count":0,
                "Bearish_Count":0,"Neutral_Count":0,
                "Avg_Confidence":0.5,"Total_Articles":0
            })

    pd.DataFrame(sentiment_rows).to_csv(
        f"{OUTPUT_DIR}/nifty50_sentiment_powerbi.csv", index=False
    )
    pd.DataFrame(headline_rows).to_csv(
        f"{OUTPUT_DIR}/nifty50_headlines_powerbi.csv", index=False
    )
    print(f"\n  💾 nifty50_sentiment_powerbi.csv — {len(sentiment_rows)} stocks")
    print(f"  💾 nifty50_headlines_powerbi.csv — {len(headline_rows)} headlines")

except Exception as e:
    print(f"  ⚠️  Sentiment skipped: {e}")

# ════════════════════════════════════════
# STEP 4 — Risk Metrics
# ════════════════════════════════════════
print("\nSTEP 4: Computing risk metrics...")

risk_rows = []
returns   = tech_df.pivot_table(index="Date",columns="Ticker",values="Daily_Return")
mkt_ret   = returns.mean(axis=1)
mkt_var   = float(mkt_ret.var())
trading_days = 252
risk_free    = 0.065

for ticker in returns.columns:
    try:
        r = returns[ticker].dropna()
        if len(r) < 30:
            continue
        ann_ret  = round((1+r.mean())**trading_days-1, 4)
        ann_vol  = round(r.std()*np.sqrt(trading_days), 4)
        sharpe   = round((ann_ret-risk_free)/ann_vol, 3) if ann_vol>0 else 0
        cum      = (1+r).cumprod()
        max_dd   = round(((cum-cum.cummax())/cum.cummax()).min()*100, 2)
        thresh   = np.percentile(r,5)
        var_95   = round(thresh*100, 3)
        tail     = r[r<=thresh]
        cvar_95  = round(tail.mean()*100, 3) if len(tail)>0 else var_95
        mkt, r2  = mkt_ret.align(r, join="inner")
        cov_m    = np.cov(r2.values, mkt.values)
        beta     = round(cov_m[0][1]/mkt_var, 3) if mkt_var>0 else 1.0
        curr     = float(tech_df[tech_df["Ticker"]==ticker]["Close"].iloc[-1])
        h52w     = float(tech_df[tech_df["Ticker"]==ticker]["Close"].tail(252).max())
        l52w     = float(tech_df[tech_df["Ticker"]==ticker]["Close"].tail(252).min())

        risk_rows.append({
            "Ticker":ticker,
            "Ann_Return_Pct":round(ann_ret*100,2),
            "Ann_Volatility_Pct":round(ann_vol*100,2),
            "Sharpe_Ratio":sharpe,
            "Max_Drawdown_Pct":max_dd,
            "VaR_95_Pct":var_95,
            "CVaR_95_Pct":cvar_95,
            "Beta":beta,
            "Current_Price":round(curr,2),
            "52W_High":round(h52w,2),
            "52W_Low":round(l52w,2),
            "From_52W_High_Pct":round((curr-h52w)/h52w*100,2)
        })
    except Exception as e:
        print(f"  ⚠️  {ticker} risk failed: {e}")

pd.DataFrame(risk_rows).sort_values("Sharpe_Ratio",ascending=False).to_csv(
    f"{OUTPUT_DIR}/nifty50_risk_metrics_powerbi.csv", index=False
)
print(f"  💾 nifty50_risk_metrics_powerbi.csv — {len(risk_rows)} stocks")

# ════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════
print("\n" + "="*55)
print(f"  QUICK REFRESH COMPLETE")
print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*55)

files_generated = [
    "nifty50_for_powerbi.csv",
    "nifty50_latest_day.csv",
    "nifty50_technical_powerbi.csv",
    "latest_signals.csv",
    "nifty50_sentiment_powerbi.csv",
    "nifty50_headlines_powerbi.csv",
    "nifty50_risk_metrics_powerbi.csv",
]

for fname in files_generated:
    path = f"{OUTPUT_DIR}/{fname}"
    if os.path.exists(path):
        rows = len(pd.read_csv(path))
        size = os.path.getsize(path)/1024
        print(f"  ✅ {fname:<45} {rows:>6} rows  {size:>7.1f} KB")
    else:
        print(f"  ❌ {fname} — MISSING")

if failed:
    print(f"\n  ⚠️  Skipped tickers: {failed}")
