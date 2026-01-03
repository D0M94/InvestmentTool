# ---------------------------
# Test Script: Screener Engine
# ---------------------------
import pandas as pd
from etf_loader import load_etfs
from factor_engine_v2 import compute_factors
from screener_engine import create_scorecard

# ---------------------------
# 1. Define ETF universe
# ---------------------------
tickers = [
    "SPY",  # S&P 500
    "QQQ",  # Nasdaq 100
    "EEM",  # Emerging Markets
    "GLD",   # Gold ETF
    "URTH" #MSCI World
]

# ---------------------------
# 2. Load ETF data
# ---------------------------
print("⬇️ Downloading ETF data ...")
etf_data = load_etfs(tickers, period="5y")  # last 5 years

# ---------------------------
# 3. Compute factor DataFrame
# ---------------------------
print("\n⚡ Computing factor scores ...")
factor_df = compute_factors(etf_data)

# ---------------------------
# 4. Run Screener Engine
# ---------------------------
print("\n🏁 Generating ranked ETF scorecard ...")
scorecard_df = create_scorecard(factor_df)

# ---------------------------
# 5. Inspect results
# ---------------------------
print("\n=== Ranked ETF Scorecard ===")
print(scorecard_df)

# Optional: save to CSV for inspection
csv_file = "test_etf_scorecard.csv"
scorecard_df.to_csv(csv_file, index=False)
print(f"\n✅ Scorecard saved to '{csv_file}'")

