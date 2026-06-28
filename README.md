# Indian Stock Market Analysis System
Built this because I was tired of not understanding why my stocks were doing what they were doing.
What is this project?
I'm Pushkar Singh, a data enthusiast from India who got curious about the stock market and decided to build something actually useful instead of just reading about it.

This project is a complete end-to-end stock market analysis system for NIFTY 50 stocks. It automatically pulls live data from NSE every day, runs it through multiple layers of analysis — technical, fundamental, sentiment, forecasting and portfolio optimization — and visualizes everything in an interactive Power BI dashboard.

No paid APIs. No SQL databases. No complicated setup. Just Python, Google Colab, and Power BI doing the heavy lifting.

Why I built this

I wanted to answer questions like:

Which NIFTY 50 stocks are genuinely undervalued right now?
What does the RSI and MACD say about a stock before I invest?
What do the news headlines say about a company's sentiment?
If I had ₹1 lakh to invest, what is the mathematically optimal split?
Where will a stock likely be 30 days from now?

I couldn't find a single free tool that answered all of these together — so I built one.

 The 6 Notebooks

01 — Data Ingestion

Fetches live daily OHLCV data for all 50 NIFTY 50 stocks using yfinance. Saves everything as Parquet files to Google Drive — no database needed. Runs automatically after market close at 3:30 PM IST.

What it outputs:

nifty50_master.parquet — full historical data for all stocks
nifty50_for_powerbi.csv — ready for Power BI import

02 — Technical Analysis

Computes 15+ technical indicators for every stock individually. Then generates a buy/sell signal score from -5 to +5 based on a combination of indicators.

Indicators computed:


Trend: SMA 20/50/200, EMA 12/26, MACD, ADX
Momentum: RSI (14), Stochastic Oscillator, Williams %R
Volatility: Bollinger Bands, ATR
Volume: OBV, Volume SMA

Signal Logic:

Score +2  → RSI < 30 (Oversold)
Score +1  → Price above SMA 50
Score +1  → MACD above Signal line
Score +1  → Price below Bollinger Lower Band
Score -2  → RSI > 70 (Overbought)
... and more

Output: Strong Buy / Buy / Neutral / Sell / Strong Sell for every stock

03 — Fundamental Analysis

Pulls financial ratios using yfinance and scores each stock from 0 to 100 based on its financial health. Then assigns a grade from A to F.

Category        Metrics
Valuation       P/E Ratio, P/B Ratio, EV/EBITDA
Profitability   ROE, ROA, Net Margin, Operating Margin
Growth          Revenue Growth, Earnings Growth
Health          Debt/Equity, Current Ratio, Quick Ratio
Income          EPS, Dividend Yield, Book Value

Grading system:

Score 70–100  → Grade A  (Fundamentally excellent)
Score 55–69   → Grade B  (Strong)
Score 40–54   → Grade C  (Average)
Score 25–39   → Grade D  (Weak)
Score 0–24    → Grade F  (Avoid)

04 — Sentiment Analysis

Scrapes live financial news headlines from Google News RSS for each stock and scores the sentiment using TextBlob NLP with a custom financial keyword booster.

How it works:


Fetch top 10 headlines per stock from Google News
Run TextBlob polarity scoring on each headline
Apply financial keyword boost (+0.1 for bullish words, -0.1 for bearish)
Aggregate into a Sentiment Score from 0 to 100


Custom keyword dictionaries:


📈 26 bullish keywords (profit, growth, rally, record, beat...)
📉 26 bearish keywords (loss, decline, probe, default, fraud...)


Output: Sentiment score + label (Very Positive / Positive / Neutral / Negative / Very Negative) for every stock

05 — Forecasting

Builds two independent forecasting models for NIFTY 50 stocks and predicts prices 30 days into the future.

Model 1 — Facebook Prophet

Captures yearly and weekly seasonality
Added custom monthly seasonality for Indian market patterns
Outputs 30-day forecast with 80% confidence interval
Runs for all 50 stocks

Model 2 — LSTM Neural Network

2-layer LSTM with Dropout regularization
Trained on 60-day sequences
Reports RMSE on test set for accuracy validation
Runs for top 5 most watched stocks


06 — Portfolio Optimization

Uses Modern Portfolio Theory to find the mathematically optimal way to allocate capital across NIFTY 50 stocks.

Three portfolios computed:
Portfolio       Goal
Max Sharpe      Best risk-adjusted return
Min Volatility  Lowest possible risk
Max Return      Highest expected return

Risk metrics calculated for every stock:


Annualized Return and Volatility
Sharpe Ratio (using 6.5% India risk-free rate)
Maximum Drawdown
Value at Risk (VaR 95%)
Conditional VaR / Expected Shortfall
Beta vs NIFTY 50 equal-weight proxy


Monte Carlo Simulation: Simulates 5,000 random portfolios to map the full risk-return space and visually identify the efficient frontier.

Discrete Allocation: Given any investment amount in INR, outputs the exact number of shares to buy for each stock in the optimal portfolio.

 Power BI Dashboard

The dashboard has 5 interactive pages. Every chart responds to the stock slicer and date range slicer in real time.

Page 1 — Market Overview

High-level view of the entire NIFTY 50 market in one glance.

4 KPI cards — stocks tracked, bullish count, bearish count, market sentiment score
Sector heatmap — color coded by returns and RSI
Top 10 gainers table with conditional color formatting
Market breadth gauge (bullish vs total stocks)


Page 2 — Stock Deep Dive

Full technical analysis for any individual stock.

Price chart with SMA 20/50/200 and EMA 20 overlaid
RSI chart with overbought/oversold reference lines
MACD chart with signal line
Volume bar chart with average volume reference
Bollinger Bands chart
All charts filter simultaneously by stock and date range slicer


Page 3 — Fundamental Analysis

Financial health comparison across all 50 stocks.

Fundamental score bar chart colored A to F
ROE vs P/E scatter plot with sector coloring and market cap bubble size
Sector average ROE comparison chart
Grade distribution donut chart
Full fundamental scorecard table with conditional cell formatting


Page 4 — Portfolio & Risk
Portfolio construction and risk analysis.

Optimal portfolio allocation pie chart (Max Sharpe weights)
Risk vs return scatter with Sharpe ratio as bubble size
Sharpe ratio bar chart with green/red conditional coloring
VaR vs CVaR comparison chart
Portfolio strategy comparison table (Max Sharpe vs Min Vol vs Max Return)
Maximum drawdown chart


Page 5 — Price Forecast

30-day forward looking price predictions.

Main forecast line chart with 80% confidence interval bands
Expected 30-day change bar chart (green = bullish, red = bearish)
Forecast summary table with all 50 stocks
Sentiment vs forecast scatter — identifies strongest buy candidates (top right quadrant)



How to Run This Project

Prerequisites


Google account (for Colab and Drive)
Power BI Desktop (free download from Microsoft)
Basic Python knowledge


Step 1 — Open Notebooks in Google Colab

Each notebook is self-contained.
Run them in order: 01 → 02 → 03 → 04 → 05 → 06
Each notebook mounts Google Drive and saves outputs automatically.

Step 2 — Run in Order

python# Each notebook starts with:
from google.colab import drive
drive.mount('/content/drive')

# And installs what it needs:
!pip install yfinance ta prophet pyportfolioopt -q

Step 3 — Download Output Files

After running all 6 notebooks, download these from Google Drive/indian_stock_analysis/data/output/:

nifty50_for_powerbi.csv
nifty50_technical_powerbi.csv
nifty50_fundamentals_powerbi.csv
nifty50_sentiment_powerbi.csv
nifty50_forecasts_powerbi.csv
nifty50_risk_metrics_powerbi.csv
portfolio_allocation_powerbi.csv
portfolio_performance_powerbi.csv
forecast_summary_powerbi.csv
latest_signals.csv

Step 4 — Open Power BI Dashboard


Open indian_stock_dashboard.pbix
Update data source paths to your local CSV folder
Click Refresh
All 5 pages populate with your data


Keeping Data Fresh

Right now data updates when you manually run Notebook 01 after market close (3:30 PM IST). Then click Refresh in Power BI to pull the new CSV.

The architecture is designed to upgrade to real-time data via broker APIs (Zerodha Kite / Upstox / Angel One) without changing anything in the analysis or dashboard layers.

Future plan:


 Schedule Notebook 01 via Google Cloud Scheduler
 Integrate Zerodha Kite API for real-time prices
 Add email alerts when Strong Buy signals fire
 Deploy dashboard to Power BI Service with daily scheduled refresh





 What I Learned Building This

Honestly this project taught me more than any course I've taken:


How to build a real data pipeline from scratch without a database
Why Parquet files are so much better than CSVs for analytical workloads
How Prophet handles seasonality vs how LSTM handles sequence patterns — and why they give different answers for the same stock
That portfolio optimization math is surprisingly simple once you understand what a covariance matrix actually represents
Why the w >= 0.02 constraint with 49 stocks is mathematically infeasible (49 × 0.02 = 0.98, leaving almost no room to optimize)
How to connect two completely separate data sources in Power BI through a shared Ticker key
That sentiment and price forecasts often disagree — and that disagreement itself is useful signal





⚠️ Disclaimer

This project is purely for educational and learning purposes. Nothing in this analysis constitutes financial advice. Stock markets are inherently unpredictable and past performance does not guarantee future results. Always do your own research before making any investment decisions.



About Me

Pushkar Singh
(BA Economic Hons)
I'm a data enthusiast passionate about applying data science to real-world financial problems. This project represents my attempt to combine Python programming, machine learning, NLP and business intelligence into a single coherent system.


📧 pushagss9876543210@gmail.com
💼 https://www.linkedin.com/in/pushkar-singh-319454323/


If you found this useful
Give the repo a star — it genuinely helps and means a lot.
If you have suggestions, found a bug, or want to collaborate on something, open an issue or reach out directly. Always happy to connect with fellow data and finance people.
