"""
scripts/quick_refresh.py

Fetches NIFTY 50 data with multiple fallback methods.
Method 1: curl_cffi session (bypasses Yahoo bot detection)
Method 2: Standard yfinance with headers
Method 3: Direct Yahoo Finance API with requests
"""

import pandas as pd
import numpy as np
import ta
import os
import sys
import time
import warnings
import traceback
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

OUTPUT_DIR = "streamlit_app/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

START_TIME = datetime.now()
print("=" * 60)
print(f"  NIFTY 50 QUICK REFRESH")
print(f"  Started: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# ── NIFTY 50 stock list ────────────────────────────────
NIFTY_50 = [
    "RELIANCE.NS",  "TCS.NS",        "HDFCBANK.NS",
    "INFY.NS",      "ICICIBANK.NS",  "HINDUNILVR.NS",
    "ITC.NS",       "SBIN.NS",       "BHARTIARTL.NS",
    "KOTAKBANK.NS", "LT.NS",         "AXISBANK.NS",
    "ASIANPAINT.NS","MARUTI.NS",     "SUNPHARMA.NS",
    "TITAN.NS",     "ULTRACEMCO.NS", "BAJFINANCE.NS",
    "WIPRO.NS",     "ONGC.NS",       "NTPC.NS",
    "POWERGRID.NS", "TECHM.NS",      "HCLTECH.NS",
    "JSWSTEEL.NS",  "TATASTEEL.NS",  "TATAMOTORS.NS",
    "NESTLEIND.NS", "DRREDDY.NS",    "DIVISLAB.NS",
    "CIPLA.NS",     "COALINDIA.NS",  "BPCL.NS",
    "GRASIM.NS",    "ADANIENT.NS",   "ADANIPORTS.NS",
    "BAJAJFINSV.NS","BAJAJ-AUTO.NS", "HEROMOTOCO.NS",
    "EICHERMOT.NS", "BRITANNIA.NS",  "HINDALCO.NS",
    "UPL.NS",       "SBILIFE.NS",    "HDFCLIFE.NS",
    "APOLLOHOSP.NS","TATACONSUM.NS", "INDUSINDBK.NS",
    "M&M.NS",       "LTF.NS"
]

SECTOR_MAP = {
    "RELIANCE.NS":"Energy",       "TCS.NS":"IT",
    "HDFCBANK.NS":"Banking",      "INFY.NS":"IT",
    "ICICIBANK.NS":"Banking",     "HINDUNILVR.NS":"FMCG",
    "ITC.NS":"FMCG",              "SBIN.NS":"Banking",
    "BHARTIARTL.NS":"Telecom",    "KOTAKBANK.NS":"Banking",
    "LT.NS":"Infrastructure",     "AXISBANK.NS":"Banking",
    "ASIANPAINT.NS":"Paints",     "MARUTI.NS":"Auto",
    "SUNPHARMA.NS":"Pharma",      "TITAN.NS":"Consumer",
    "ULTRACEMCO.NS":"Cement",     "BAJFINANCE.NS":"NBFC",
    "WIPRO.NS":"IT",              "ONGC.NS":"Energy",
    "NTPC.NS":"Power",            "POWERGRID.NS":"Power",
    "TECHM.NS":"IT",              "HCLTECH.NS":"IT",
    "JSWSTEEL.NS":"Steel",        "TATASTEEL.NS":"Steel",
    "TATAMOTORS.NS":"Auto",       "NESTLEIND.NS":"FMCG",
    "DRREDDY.NS":"Pharma",        "DIVISLAB.NS":"Pharma",
    "CIPLA.NS":"Pharma",          "COALINDIA.NS":"Mining",
    "BPCL.NS":"Energy",           "GRASIM.NS":"Cement",
    "ADANIENT.NS":"Conglomerate", "ADANIPORTS.NS":"Ports",
    "BAJAJFINSV.NS":"NBFC",       "BAJAJ-AUTO.NS":"Auto",
    "HEROMOTOCO.NS":"Auto",       "EICHERMOT.NS":"Auto",
    "BRITANNIA.NS":"FMCG",        "HINDALCO.NS":"Metals",
    "UPL.NS":"Agrochemicals",     "SBILIFE.NS":"Insurance",
    "HDFCLIFE.NS":"Insurance",    "APOLLOHOSP.NS":"Healthcare",
    "TATACONSUM.NS":"FMCG",       "INDUSINDBK.NS":"Banking",
    "M&M.NS":"Auto",              "LTF.NS":"NBFC"
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
    "DRREDDY.NS":"Dr Reddys",
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
    "TATACONSUM.NS":"Tata Consumer",
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


# ── METHOD 1: curl_cffi (best for bypassing bot detection) ─
def fetch_with_curl_cffi(ticker):
    try:
        from curl_cffi import requests as curl_requests
        import yfinance as yf
        session = curl_requests.Session(impersonate="chrome110")
        t   = yf.Ticker(ticker, session=session)
        df  = t.history(period="1y", auto_adjust=True)
        if not df.empty:
            return df
    except Exception:
        pass
    return None


# ── METHOD 2: Standard yfinance ────────────────────────────
def fetch_with_yfinance(ticker):
    try:
        import yfinance as yf
        t  = yf.Ticker(ticker)
        df = t.history(period="1y", auto_adjust=True)
        if not df.empty:
            return df
    except Exception:
        pass
    return None


# ── METHOD 3: Direct Yahoo Finance v8 API ──────────────────
def fetch_with_requests(ticker):
    try:
        import requests
        end   = int(datetime.now().timestamp())
        start = int((datetime.now() - timedelta(days=380)).timestamp())
        url   = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?period1={start}&period2={end}&interval=1d"
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept":          "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None

        data    = resp.json()
        result  = data["chart"]["result"][0]
        meta    = result["meta"]
        ts      = result["timestamp"]
        quotes  = result["indicators"]["quote"][0]
        adjclose = result["indicators"].get("adjclose", [{}])[0].get(
            "adjclose", quotes["close"]
        )

        dates  = pd.to_datetime(ts, unit="s")
        df = pd.DataFrame({
            "Open":   quotes["open"],
            "High":   quotes["high"],
            "Low":    quotes["low"],
            "Close":  adjclose,
            "Volume": quotes["volume"],
        }, index=dates)

        df = df.dropna()
        return df

    except Exception:
        return None


# ── METHOD 4: Yahoo Finance v7 API (alternate endpoint) ────
def fetch_with_requests_v7(ticker):
    try:
        import requests
        end   = int(datetime.now().timestamp())
        start = int((datetime.now() - timedelta(days=380)).timestamp())
        url   = (
            f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?period1={start}&period2={end}&interval=1d"
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None

        data    = resp.json()
        result  = data["chart"]["result"][0]
        ts      = result["timestamp"]
        quotes  = result["indicators"]["quote"][0]
        adjclose = result["indicators"].get("adjclose", [{}])[0].get(
            "adjclose", quotes["close"]
        )

        dates = pd.to_datetime(ts, unit="s")
        df = pd.DataFrame({
            "Open":   quotes["open"],
            "High":   quotes["high"],
            "Low":    quotes["low"],
            "Close":  adjclose,
            "Volume": quotes["volume"],
        }, index=dates)

        df = df.dropna()
        return df

    except Exception:
        return None


def fetch_ticker_all_methods(ticker):
    """
    Try all 4 methods in sequence.
    Returns the first successful result.
    """
    methods = [
        ("curl_cffi",      fetch_with_curl_cffi),
        ("yfinance",       fetch_with_yfinance),
        ("requests_v8",    fetch_with_requests),
        ("requests_v7",    fetch_with_requests_v7),
    ]

    for method_name, method_fn in methods:
        try:
            df = method_fn(ticker)
            if df is not None and not df.empty and len(df) > 10:
                return df, method_name
        except Exception:
            pass
        time.sleep(0.5)

    return None, "all_failed"


# ════════════════════════════════════════
# STEP 1 — FETCH PRICE DATA
# ════════════════════════════════════════
print(f"\n[STEP 1/4] Fetching 1-year price history...")
print(f"  Using 4 fallback methods to bypass bot detection")
print("-" * 60)

all_data     = []
failed       = []
method_counts = {}

for i, ticker in enumerate(NIFTY_50, 1):
    df, method_used = fetch_ticker_all_methods(ticker)

    if df is not None and not df.empty:
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df_clean = df.copy()
        df_clean["Ticker"] = ticker
        df_clean["Sector"] = SECTOR_MAP.get(ticker, "Unknown")
        df_clean.reset_index(inplace=True)
        df_clean.rename(columns={"index": "Date"}, inplace=True)
        if "Date" not in df_clean.columns and "Datetime" in df_clean.columns:
            df_clean.rename(columns={"Datetime": "Date"}, inplace=True)

        all_data.append(df_clean)
        method_counts[method_used] = method_counts.get(method_used, 0) + 1
        print(
            f"  OK  [{i:02d}/{len(NIFTY_50)}]  {ticker:<22}  "
            f"{len(df_clean)} rows  via {method_used}"
        )
    else:
        failed.append(ticker)
        print(f"  FAIL [{i:02d}/{len(NIFTY_50)}]  {ticker:<22}  all methods failed")

    time.sleep(0.3)

print(f"\n  Results: {len(all_data)} OK / {len(failed)} failed")
print(f"  Methods: {method_counts}")

if not all_data:
    print("CRITICAL: No data fetched at all. Stopping.")
    sys.exit(1)

if len(all_data) < 10:
    print(f"WARNING: Only {len(all_data)} stocks fetched. Data may be incomplete.")

# ── Clean and combine ──────────────────────────────────
raw_df = pd.concat(all_data, ignore_index=True)

if "Date" not in raw_df.columns:
    date_col = [c for c in raw_df.columns
                if "date" in c.lower() or "time" in c.lower()]
    if date_col:
        raw_df.rename(columns={date_col[0]: "Date"}, inplace=True)

raw_df["Date"] = pd.to_datetime(raw_df["Date"])
if hasattr(raw_df["Date"].dt, "tz") and raw_df["Date"].dt.tz is not None:
    raw_df["Date"] = raw_df["Date"].dt.tz_localize(None)

needed_cols = ["Date","Ticker","Sector","Open","High","Low","Close","Volume"]
available   = [c for c in needed_cols if c in raw_df.columns]
raw_df      = raw_df[available].copy()

raw_df.drop_duplicates(subset=["Date","Ticker"], inplace=True)
raw_df.dropna(subset=["Close"], inplace=True)
raw_df.sort_values(["Ticker","Date"], inplace=True)
raw_df["Daily_Return"] = (
    raw_df.groupby("Ticker")["Close"].pct_change().round(4)
)
if "Open" in raw_df.columns:
    raw_df["Price_Change"]     = (raw_df["Close"] - raw_df["Open"]).round(2)
    raw_df["Price_Change_Pct"] = (
        (raw_df["Price_Change"] / raw_df["Open"]) * 100
    ).round(2)
raw_df.reset_index(drop=True, inplace=True)

latest_date = raw_df["Date"].max()
print(f"\n  Latest date in fetched data: {latest_date.date()}")
print(f"  Total rows: {len(raw_df):,}")
print(f"  Unique stocks: {raw_df['Ticker'].nunique()}")

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
            print(f"  SKIP {ticker} — only {len(s)} rows")
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
        print(
            f"  OK  [{i:02d}]  {ticker:<22}  "
            f"signal: {s['Signal'].iloc[-1]:<12}  "
            f"RSI: {round(float(s['RSI'].iloc[-1]), 1)}"
        )

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
# STEP 3 — SENTIMENT
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
            query = company.replace(" ", "+") + "+NSE+stock"
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
            b = be = n   = 0

            for h in headlines:
                try:
                    pol = float(TextBlob(h).sentiment.polarity)
                except Exception:
                    pol = 0.0
                polarities.append(pol)
                if pol > 0.05:    b  += 1; label = "positive"
                elif pol < -0.05: be += 1; label = "negative"
                else:             n  += 1; label = "neutral"
                hl_rows.append({
                    "Ticker":"   "  + ticker,
                    "Company":   company,
                    "Headline":  h,
                    "Label":     label,
                    "Confidence":round(min(abs(pol)+0.5,1.0),4),
                    "Polarity":  round(pol,4),
                    "Model":     "TextBlob"
                })

            avg_pol = round(sum(polarities)/len(polarities),4) \
                      if polarities else 0.0
            score   = round((avg_pol+1)/2*100,1)
            if avg_pol >= 0.4:    lbl = "Very Positive"
            elif avg_pol >= 0.15: lbl = "Positive"
            elif avg_pol <= -0.4: lbl = "Very Negative"
            elif avg_pol <= -0.15:lbl = "Negative"
            else:                 lbl = "Neutral"

            sent_rows.append({
                "Ticker":ticker,"Company":company,
                "Avg_Polarity":avg_pol,"Sentiment_Label":lbl,
                "Sentiment_Score":score,"Bullish_Count":b,
                "Bearish_Count":be,"Neutral_Count":n,
                "Avg_Confidence":round(min(abs(avg_pol)+0.5,1.0),3),
                "Total_Articles":len(headlines)
            })
            print(f"  OK  [{i:02d}]  {ticker:<22}  {lbl}")
            time.sleep(0.2)

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
    print(f"  Sentiment failed entirely: {e}")
    for fname, cols in [
        ("nifty50_sentiment_powerbi.csv", [
            "Ticker","Company","Avg_Polarity","Sentiment_Label",
            "Sentiment_Score","Bullish_Count","Bearish_Count",
            "Neutral_Count","Avg_Confidence","Total_Articles"
        ]),
        ("nifty50_headlines_powerbi.csv", [
            "Ticker","Company","Headline",
            "Label","Confidence","Polarity","Model"
        ]),
    ]:
        pd.DataFrame(columns=cols).to_csv(
            os.path.join(OUTPUT_DIR, fname), index=False
        )


# ════════════════════════════════════════
# STEP 4 — RISK METRICS
# ════════════════════════════════════════
print(f"\n[STEP 4/4] Computing risk metrics...")
print("-" * 60)

try:
    returns_piv = tech_df.pivot_table(
        index="Date", columns="Ticker", values="Daily_Return"
    )
    mkt_ret   = returns_piv.mean(axis=1)
    mkt_var   = float(mkt_ret.var())
    rf        = 0.065
    td        = 252
    risk_rows = []

    for ticker in returns_piv.columns:
        try:
            r = returns_piv[ticker].dropna()
            if len(r) < 30:
                continue
            ann_ret = round((1 + r.mean()) ** td - 1, 4)
            ann_vol = round(r.std() * np.sqrt(td), 4)
            sharpe  = round(
                (ann_ret - rf) / ann_vol, 3
            ) if ann_vol > 0 else 0.0
            cum     = (1 + r).cumprod()
            max_dd  = round(
                float(((cum-cum.cummax())/cum.cummax()).min())*100, 2
            )
            thresh  = float(np.percentile(r, 5))
            var_95  = round(thresh * 100, 3)
            tail    = r[r <= thresh]
            cvar_95 = round(float(tail.mean())*100,3) \
                      if len(tail)>0 else var_95
            m_a, r_a = mkt_ret.align(r, join="inner")
            cov_m    = np.cov(r_a.values, m_a.values)
            beta     = round(cov_m[0][1]/mkt_var,3) \
                       if mkt_var>0 else 1.0
            prices   = tech_df[tech_df["Ticker"]==ticker]["Close"]
            curr     = round(float(prices.iloc[-1]),2)
            h52      = round(float(prices.tail(252).max()),2)
            l52      = round(float(prices.tail(252).min()),2)
            risk_rows.append({
                "Ticker":             ticker,
                "Ann_Return_Pct":     round(ann_ret*100,2),
                "Ann_Volatility_Pct": round(ann_vol*100,2),
                "Sharpe_Ratio":       sharpe,
                "Max_Drawdown_Pct":   max_dd,
                "VaR_95_Pct":         var_95,
                "CVaR_95_Pct":        cvar_95,
                "Beta":               beta,
                "Current_Price":      curr,
                "52W_High":           h52,
                "52W_Low":            l52,
                "From_52W_High_Pct":  round((curr-h52)/h52*100,2)
            })
            print(
                f"  OK  {ticker:<22}  "
                f"Sharpe:{sharpe:>6.3f}  "
                f"Ret:{ann_ret*100:>+7.2f}%"
            )
        except Exception as e:
            print(f"  FAIL  {ticker}  {e}")

    pd.DataFrame(risk_rows).sort_values(
        "Sharpe_Ratio", ascending=False
    ).to_csv(
        os.path.join(OUTPUT_DIR,"nifty50_risk_metrics_powerbi.csv"),
        index=False
    )
    print(f"  SAVED  nifty50_risk_metrics_powerbi.csv  {len(risk_rows)} rows")

except Exception as e:
    print(f"  Risk failed: {e}")
    traceback.print_exc()


# ════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════
end_time = datetime.now()
duration = (end_time - START_TIME).seconds

print("\n" + "=" * 60)
print(f"  REFRESH COMPLETE")
print(f"  Finished:  {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Duration:  {duration//60}m {duration%60}s")
print(f"  Data date: {latest_date.date()}")
print(f"  Stocks:    {len(all_data)}/{len(NIFTY_50)}")
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
print(f"\n  {'File':<47}  {'Rows':>6}  {'Size':>8}")
print(f"  {'-'*65}")

for fname in expected:
    fpath = os.path.join(OUTPUT_DIR, fname)
    if os.path.exists(fpath):
        try:
            rows = len(pd.read_csv(fpath))
            size = os.path.getsize(fpath)/1024
            ok   = rows > 0
            if not ok:
                all_ok = False
            status = "OK" if ok else "EMPTY"
            print(
                f"  {fname:<47}  {rows:>6}  "
                f"{size:>7.1f}KB  {status}"
            )
        except Exception as ex:
            print(f"  {fname:<47}  ERROR: {ex}")
            all_ok = False
    else:
        print(f"  {fname:<47}  MISSING")
        all_ok = False

if failed:
    print(f"\n  Failed tickers: {failed}")

print(f"\n  Status: {'ALL OK' if all_ok else 'SOME ISSUES'}")
print("=" * 60)

if not all_ok:
    sys.exit(1)
