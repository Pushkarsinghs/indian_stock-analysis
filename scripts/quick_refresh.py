!pip install ta
!pip install feedparser
!pip install textblob

"""
scripts/quick_refresh.py

Fetches fresh NIFTY 50 data and saves CSV files to
streamlit_app/data/ for the Streamlit web app.

Runs automatically via GitHub Actions every weekday.
Can also be run manually on your PC or in Colab.

Generates:
  1. nifty50_for_powerbi.csv          - Full price history
  2. nifty50_latest_day.csv           - Today's prices only
  3. nifty50_technical_powerbi.csv    - All technical indicators
  4. latest_signals.csv               - Current buy/sell signals
  5. nifty50_sentiment_powerbi.csv    - News sentiment per stock
  6. nifty50_headlines_powerbi.csv    - Individual headlines
  7. nifty50_risk_metrics_powerbi.csv - Risk and return stats
"""

import pandas as pd
import numpy as np
import yfinance as yf
import ta
import os
import sys
import warnings
import feedparser
import time
import traceback
from datetime import datetime

warnings.filterwarnings("ignore")

# ────────────────────────────────────────
# CONFIGURATION
# ────────────────────────────────────────

OUTPUT_DIR = "streamlit_app/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

START_TIME = datetime.now()
print("=" * 60)
print(f"  NIFTY 50 QUICK REFRESH")
print(f"  Started: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Output:  {OUTPUT_DIR}")
print("=" * 60)

# ────────────────────────────────────────
# STOCK LISTS
# ────────────────────────────────────────

NIFTY_50 = [
    "RELIANCE.NS",  "TCS.NS",       "HDFCBANK.NS",  "INFY.NS",
    "ICICIBANK.NS", "HINDUNILVR.NS","ITC.NS",        "SBIN.NS",
    "BHARTIARTL.NS","KOTAKBANK.NS", "LT.NS",         "AXISBANK.NS",
    "ASIANPAINT.NS","MARUTI.NS",    "SUNPHARMA.NS",  "TITAN.NS",
    "ULTRACEMCO.NS","BAJFINANCE.NS","WIPRO.NS",       "ONGC.NS",
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
    "RELIANCE.NS":   "Reliance Industries",
    "TCS.NS":        "TCS Tata Consultancy",
    "HDFCBANK.NS":   "HDFC Bank",
    "INFY.NS":       "Infosys",
    "ICICIBANK.NS":  "ICICI Bank",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "ITC.NS":        "ITC Limited",
    "SBIN.NS":       "State Bank India SBI",
    "BHARTIARTL.NS": "Bharti Airtel",
    "KOTAKBANK.NS":  "Kotak Mahindra Bank",
    "LT.NS":         "Larsen Toubro",
    "AXISBANK.NS":   "Axis Bank",
    "ASIANPAINT.NS": "Asian Paints",
    "MARUTI.NS":     "Maruti Suzuki",
    "SUNPHARMA.NS":  "Sun Pharma",
    "TITAN.NS":      "Titan Company",
    "ULTRACEMCO.NS": "UltraTech Cement",
    "BAJFINANCE.NS": "Bajaj Finance",
    "WIPRO.NS":      "Wipro",
    "ONGC.NS":       "ONGC Oil Gas",
    "NTPC.NS":       "NTPC Power",
    "POWERGRID.NS":  "Power Grid India",
    "TECHM.NS":      "Tech Mahindra",
    "HCLTECH.NS":    "HCL Technologies",
    "JSWSTEEL.NS":   "JSW Steel",
    "TATASTEEL.NS":  "Tata Steel",
    "TATAMOTORS.NS": "Tata Motors",
    "NESTLEIND.NS":  "Nestle India",
    "DRREDDY.NS":    "Dr Reddys Laboratories",
    "DIVISLAB.NS":   "Divis Laboratories",
    "CIPLA.NS":      "Cipla Pharma",
    "COALINDIA.NS":  "Coal India",
    "BPCL.NS":       "BPCL Bharat Petroleum",
    "GRASIM.NS":     "Grasim Industries",
    "ADANIENT.NS":   "Adani Enterprises",
    "ADANIPORTS.NS": "Adani Ports",
    "BAJAJFINSV.NS": "Bajaj Finserv",
    "BAJAJ-AUTO.NS": "Bajaj Auto",
    "HEROMOTOCO.NS": "Hero MotoCorp",
    "EICHERMOT.NS":  "Eicher Motors",
    "BRITANNIA.NS":  "Britannia Industries",
    "HINDALCO.NS":   "Hindalco Aluminium",
    "UPL.NS":        "UPL Agrochemicals",
    "SBILIFE.NS":    "SBI Life Insurance",
    "HDFCLIFE.NS":   "HDFC Life Insurance",
    "APOLLOHOSP.NS": "Apollo Hospitals",
    "TATACONSUM.NS": "Tata Consumer Products",
    "INDUSINDBK.NS": "IndusInd Bank",
    "M&M.NS":        "Mahindra Mahindra",
    "LTF.NS":        "L&T Finance"
}


def save_csv(df, filename, description):
    """Save DataFrame to CSV and print confirmation."""
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False)
    size = os.path.getsize(path) / 1024
    print(f"  SAVED  {filename:<45} {len(df):>6} rows  {size:>7.1f} KB")
    return path


# ════════════════════════════════════════
# STEP 1 — FETCH PRICE DATA
# ════════════════════════════════════════
print(f"\n[STEP 1/4] Fetching 1-year price history from Yahoo Finance...")
print("-" * 60)

all_data = []
failed   = []

for i, ticker in enumerate(NIFTY_50, 1):
    for attempt in range(3):           # retry up to 3 times
        try:
            df = yf.Ticker(ticker).history(period="1y", auto_adjust=True)
            if df.empty:
                raise ValueError("Empty dataframe returned")
            df["Ticker"] = ticker
            df["Sector"] = SECTOR_MAP.get(ticker, "Unknown")
            df.reset_index(inplace=True)
            all_data.append(df)
            print(f"  OK  [{i:02d}/{len(NIFTY_50)}]  {ticker:<22}  "
                  f"{len(df)} rows")
            break
        except Exception as e:
            if attempt < 2:
                print(f"  RETRY [{attempt+1}]  {ticker}  {e}")
                time.sleep(2)
            else:
                print(f"  FAIL  [{i:02d}/{len(NIFTY_50)}]  {ticker}  {e}")
                failed.append(ticker)
    time.sleep(0.3)

if not all_data:
    print("CRITICAL: No data fetched from Yahoo Finance. Stopping.")
    sys.exit(1)

# Combine and clean
raw_df = pd.concat(all_data, ignore_index=True)
raw_df["Date"] = pd.to_datetime(raw_df["Date"])
if raw_df["Date"].dt.tz is not None:
    raw_df["Date"] = raw_df["Date"].dt.tz_localize(None)

raw_df = raw_df[[
    "Date","Ticker","Sector","Open","High","Low","Close","Volume"
]].copy()
raw_df.drop_duplicates(subset=["Date","Ticker"], inplace=True)
raw_df.dropna(subset=["Close"], inplace=True)
raw_df.sort_values(["Ticker","Date"], inplace=True)

raw_df["Daily_Return"]     = (raw_df.groupby("Ticker")["Close"]
                               .pct_change().round(4))
raw_df["Price_Change"]     = (raw_df["Close"] - raw_df["Open"]).round(2)
raw_df["Price_Change_Pct"] = ((raw_df["Price_Change"] /
                                raw_df["Open"]) * 100).round(2)
raw_df.reset_index(drop=True, inplace=True)

print(f"\n  Total rows: {len(raw_df):,}")
print(f"  Stocks fetched: {raw_df['Ticker'].nunique()}")
print(f"  Date range: {raw_df['Date'].min().date()} to "
      f"{raw_df['Date'].max().date()}")

save_csv(raw_df, "nifty50_for_powerbi.csv", "Full price history")

latest_day = raw_df[raw_df["Date"] == raw_df["Date"].max()].copy()
save_csv(latest_day, "nifty50_latest_day.csv", "Today's prices")

if failed:
    print(f"\n  Tickers that failed: {failed}")


# ════════════════════════════════════════
# STEP 2 — TECHNICAL ANALYSIS
# ════════════════════════════════════════
print(f"\n[STEP 2/4] Computing 15+ technical indicators...")
print("-" * 60)

tech_results = []
tech_errors  = []

for i, ticker in enumerate(raw_df["Ticker"].unique(), 1):
    try:
        s = raw_df[raw_df["Ticker"] == ticker].copy().sort_values("Date")
        s = s.reset_index(drop=True)

        if len(s) < 30:
            print(f"  SKIP  {ticker}  (only {len(s)} rows)")
            continue

        # Trend indicators
        s["SMA_20"]      = (ta.trend.SMAIndicator(s["Close"], 20)
                            .sma_indicator())
        s["SMA_50"]      = (ta.trend.SMAIndicator(s["Close"], 50)
                            .sma_indicator())
        s["SMA_200"]     = (ta.trend.SMAIndicator(s["Close"], 200)
                            .sma_indicator())
        s["EMA_20"]      = (ta.trend.EMAIndicator(s["Close"], 20)
                            .ema_indicator())
        s["EMA_26"]      = (ta.trend.EMAIndicator(s["Close"], 26)
                            .ema_indicator())

        macd_obj         = ta.trend.MACD(s["Close"])
        s["MACD"]        = macd_obj.macd()
        s["MACD_Signal"] = macd_obj.macd_signal()
        s["MACD_Hist"]   = macd_obj.macd_diff()

        s["ADX"]         = (ta.trend.ADXIndicator(
                                s["High"], s["Low"], s["Close"])
                            .adx())

        # Momentum indicators
        s["RSI"]         = (ta.momentum.RSIIndicator(s["Close"], 14)
                            .rsi())
        stoch_obj        = ta.momentum.StochasticOscillator(
                               s["High"], s["Low"], s["Close"])
        s["Stoch_K"]     = stoch_obj.stoch()
        s["Stoch_D"]     = stoch_obj.stoch_signal()

        # Volatility indicators
        bb_obj           = ta.volatility.BollingerBands(s["Close"])
        s["BB_Upper"]    = bb_obj.bollinger_hband()
        s["BB_Middle"]   = bb_obj.bollinger_mavg()
        s["BB_Lower"]    = bb_obj.bollinger_lband()
        s["BB_Width"]    = bb_obj.bollinger_wband()

        s["ATR"]         = (ta.volatility.AverageTrueRange(
                                s["High"], s["Low"], s["Close"])
                            .average_true_range())

        # Volume indicator
        s["OBV"]         = (ta.volume.OnBalanceVolumeIndicator(
                                s["Close"], s["Volume"])
                            .on_balance_volume())

        # Signal scoring system (-5 to +5)
        s["Signal_Score"] = 0
        s.loc[s["RSI"] < 30,                       "Signal_Score"] += 2
        s.loc[s["RSI"] > 70,                       "Signal_Score"] -= 2
        s.loc[s["MACD"] > s["MACD_Signal"],        "Signal_Score"] += 1
        s.loc[s["MACD"] < s["MACD_Signal"],        "Signal_Score"] -= 1
        s.loc[s["Close"] > s["SMA_50"],            "Signal_Score"] += 1
        s.loc[s["Close"] < s["SMA_50"],            "Signal_Score"] -= 1
        s.loc[s["Close"] > s["SMA_200"],           "Signal_Score"] += 1
        s.loc[s["Close"] < s["SMA_200"],           "Signal_Score"] -= 1
        s.loc[s["Close"] < s["BB_Lower"],          "Signal_Score"] += 1
        s.loc[s["Close"] > s["BB_Upper"],          "Signal_Score"] -= 1

        # Signal labels
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

        latest_signal = s["Signal"].iloc[-1]
        print(f"  OK  [{i:02d}/{len(raw_df['Ticker'].unique())}]  "
              f"{ticker:<22}  signal: {latest_signal}")

    except Exception as e:
        tech_errors.append(ticker)
        print(f"  FAIL  {ticker}  {e}")
        traceback.print_exc()

if not tech_results:
    print("CRITICAL: No technical results generated. Stopping.")
    sys.exit(1)

tech_df = pd.concat(tech_results, ignore_index=True)
save_csv(tech_df, "nifty50_technical_powerbi.csv", "Technical indicators")

latest_signals = (tech_df.groupby("Ticker").last()
                  .reset_index())
save_csv(latest_signals, "latest_signals.csv", "Latest signals")

if tech_errors:
    print(f"\n  Technical failures: {tech_errors}")


# ════════════════════════════════════════
# STEP 3 — SENTIMENT ANALYSIS
# ════════════════════════════════════════
print(f"\n[STEP 3/4] Fetching news sentiment from Google News RSS...")
print("-" * 60)

try:
    from textblob import TextBlob

    sent_rows = []
    hl_rows   = []

    for i, (ticker, company) in enumerate(COMPANY_NAMES.items(), 1):
        try:
            query = company.replace(" ", "+") + "+NSE+stock+India"
            url   = (f"https://news.google.com/rss/search?"
                     f"q={query}&hl=en-IN&gl=IN&ceid=IN:en")
            feed  = feedparser.parse(url)

            headlines  = []
            for entry in feed.entries[:8]:
                title = entry.title
                if " - " in title:
                    title = title.rsplit(" - ", 1)[0]
                title = title.strip()
                if 10 < len(title) < 300:
                    headlines.append(title)

            polarities = []
            bullish = bearish = neutral_count = 0

            for h in headlines:
                try:
                    pol = TextBlob(h).sentiment.polarity
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

                conf = round(min(abs(pol) + 0.5, 1.0), 4)
                hl_rows.append({
                    "Ticker":     ticker,
                    "Company":    company,
                    "Headline":   h,
                    "Label":      label,
                    "Confidence": conf,
                    "Polarity":   round(pol, 4),
                    "Model":      "TextBlob"
                })

            if polarities:
                avg_pol = round(sum(polarities) / len(polarities), 4)
            else:
                avg_pol = 0.0

            score = round((avg_pol + 1) / 2 * 100, 1)

            if avg_pol >= 0.4:
                lbl = "Very Positive"
            elif avg_pol >= 0.15:
                lbl = "Positive"
            elif avg_pol <= -0.4:
                lbl = "Very Negative"
            elif avg_pol <= -0.15:
                lbl = "Negative"
            else:
                lbl = "Neutral"

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

            print(f"  OK  [{i:02d}/{len(COMPANY_NAMES)}]  "
                  f"{ticker:<22}  {lbl}  (score: {score})")
            time.sleep(0.25)

        except Exception as e:
            print(f"  FAIL  {ticker}  {e}")
            sent_rows.append({
                "Ticker":          ticker,
                "Company":         company,
                "Avg_Polarity":    0.0,
                "Sentiment_Label": "Neutral",
                "Sentiment_Score": 50.0,
                "Bullish_Count":   0,
                "Bearish_Count":   0,
                "Neutral_Count":   0,
                "Avg_Confidence":  0.5,
                "Total_Articles":  0
            })

    save_csv(pd.DataFrame(sent_rows),
             "nifty50_sentiment_powerbi.csv",
             "Sentiment by stock")
    save_csv(pd.DataFrame(hl_rows),
             "nifty50_headlines_powerbi.csv",
             "Individual headlines")

except Exception as e:
    print(f"  Sentiment step failed entirely: {e}")
    # Save empty files so the app doesn't crash
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
    print("  Empty sentiment files saved as fallback")


# ════════════════════════════════════════
# STEP 4 — RISK METRICS
# ════════════════════════════════════════
print(f"\n[STEP 4/4] Computing risk and return metrics...")
print("-" * 60)

try:
    returns_pivot = tech_df.pivot_table(
        index="Date",
        columns="Ticker",
        values="Daily_Return"
    )
    market_returns = returns_pivot.mean(axis=1)
    market_var     = float(market_returns.var())
    risk_free_rate = 0.065
    trading_days   = 252

    risk_rows = []

    for ticker in returns_pivot.columns:
        try:
            r = returns_pivot[ticker].dropna()
            if len(r) < 30:
                continue

            # Annualised return and volatility
            ann_ret = round((1 + r.mean()) ** trading_days - 1, 4)
            ann_vol = round(r.std() * np.sqrt(trading_days), 4)

            # Sharpe ratio
            sharpe = round(
                (ann_ret - risk_free_rate) / ann_vol, 3
            ) if ann_vol > 0 else 0.0

            # Maximum drawdown
            cum_returns = (1 + r).cumprod()
            rolling_max = cum_returns.cummax()
            drawdowns   = (cum_returns - rolling_max) / rolling_max
            max_dd      = round(float(drawdowns.min()) * 100, 2)

            # Value at Risk and CVaR (95% confidence)
            threshold = float(np.percentile(r, 5))
            var_95    = round(threshold * 100, 3)
            tail      = r[r <= threshold]
            cvar_95   = round(float(tail.mean()) * 100, 3) \
                        if len(tail) > 0 else var_95

            # Beta vs NIFTY 50
            mkt_aligned, r_aligned = market_returns.align(r, join="inner")
            cov_matrix = np.cov(
                r_aligned.values, mkt_aligned.values
            )
            beta = round(
                cov_matrix[0][1] / market_var, 3
            ) if market_var > 0 else 1.0

            # Price levels
            stock_prices = tech_df[
                tech_df["Ticker"] == ticker
            ]["Close"]
            curr_price = round(float(stock_prices.iloc[-1]), 2)
            high_52w   = round(float(stock_prices.tail(252).max()), 2)
            low_52w    = round(float(stock_prices.tail(252).min()), 2)
            from_high  = round(
                (curr_price - high_52w) / high_52w * 100, 2
            )

            risk_rows.append({
                "Ticker":             ticker,
                "Ann_Return_Pct":     round(ann_ret * 100, 2),
                "Ann_Volatility_Pct": round(ann_vol * 100, 2),
                "Sharpe_Ratio":       sharpe,
                "Max_Drawdown_Pct":   max_dd,
                "VaR_95_Pct":         var_95,
                "CVaR_95_Pct":        cvar_95,
                "Beta":               beta,
                "Current_Price":      curr_price,
                "52W_High":           high_52w,
                "52W_Low":            low_52w,
                "From_52W_High_Pct":  from_high
            })

            print(f"  OK  {ticker:<22}  "
                  f"Sharpe: {sharpe:>6.3f}  "
                  f"Return: {ann_ret*100:>+7.2f}%")

        except Exception as e:
            print(f"  FAIL  {ticker}  {e}")

    risk_df = pd.DataFrame(risk_rows).sort_values(
        "Sharpe_Ratio", ascending=False
    )
    save_csv(risk_df, "nifty50_risk_metrics_powerbi.csv",
             "Risk metrics")

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
print(f"  Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Duration: {duration // 60}m {duration % 60}s")
print("=" * 60)

expected_files = [
    "nifty50_for_powerbi.csv",
    "nifty50_latest_day.csv",
    "nifty50_technical_powerbi.csv",
    "latest_signals.csv",
    "nifty50_sentiment_powerbi.csv",
    "nifty50_headlines_powerbi.csv",
    "nifty50_risk_metrics_powerbi.csv",
]

all_ok = True
print(f"\n  {'File':<45} {'Rows':>6}  {'Size':>8}")
print(f"  {'-'*65}")

for fname in expected_files:
    fpath = os.path.join(OUTPUT_DIR, fname)
    if os.path.exists(fpath):
        try:
            rows = len(pd.read_csv(fpath))
            size = os.path.getsize(fpath) / 1024
            status = "OK" if rows > 0 else "EMPTY"
            if rows == 0:
                all_ok = False
            print(f"  {fname:<45} {rows:>6}  {size:>7.1f}KB  {status}")
        except Exception as e:
            print(f"  {fname:<45} ERROR reading: {e}")
            all_ok = False
    else:
        print(f"  {fname:<45} MISSING")
        all_ok = False

print(f"\n  {'ALL FILES OK' if all_ok else 'SOME FILES MISSING OR EMPTY'}")

if failed:
    print(f"\n  Price fetch failed for: {failed}")
if tech_errors:
    print(f"  Technical calc failed for: {tech_errors}")

print("=" * 60)

# Exit with error code if critical files missing
if not all_ok:
    sys.exit(1)
