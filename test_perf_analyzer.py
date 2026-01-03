# test_perf_analyzer.py

from performance_analyzer import analyze_tickers
import pandas as pd

# ---------------------------
# 1. Define tickers to analyze
# ---------------------------
tickers = [
    "SPY",  # S&P 500
    "QQQ",  # Nasdaq 100
    "EEM",  # Emerging Markets
    "GLD"   # Gold ETF
    "URTH" #MSCI World
    ]

# ---------------------------
# 2. Run analysis
# ---------------------------
print("⬇️ Downloading price data and computing performance metrics ...")
cum_df, metrics = analyze_tickers(tickers, period="5y", risk_free_rate=0.015)

# ---------------------------
# 3. Inspect cumulative performance
# ---------------------------
print("\n=== CUMULATIVE PERFORMANCE (last 5 days) ===")
print(cum_df.tail())

# ---------------------------
# 4. Inspect calculated metrics
# ---------------------------
metrics_df = pd.DataFrame(metrics).T  # convert dict to DataFrame
metrics_df = metrics_df[["TotalReturn", "AnnualReturn", "AnnualVolatility", "SharpeRatio"]]
print("\n=== PERFORMANCE METRICS ===")
print(metrics_df)

# ---------------------------
# Optional: save results
# ---------------------------
cum_df.to_csv("cumulative_performance.csv")
metrics_df.to_csv("performance_metrics.csv")
print("\n✅ Saved cumulative performance and metrics to CSV files")
