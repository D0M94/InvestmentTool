# ---------------------------
# Test Script for ETF Pipeline
# ---------------------------

from etf_loader import load_etfs
from factor_engine import compute_factors
import pandas as pd

# ---------------------------
# 1. Define your ETF universe
# ---------------------------
tickers = [
    "VOO",  # S&P 500
    "SPY",  # S&P 500
    "QQQ",  # Nasdaq 100
    "IWM",  # Russell 2000
    "EFA",  # Developed ex-US
    "EEM",  # Emerging Markets
    "TLT",  # Long-term Treasuries
    "GLD"   # Gold ETF
]

# ---------------------------
# 2. Load ETF Data
# ---------------------------
print("⬇️  Downloading ETF data ...")
etf_data = load_etfs(tickers, period="5y")  # last 5 years

# ---------------------------
# 3. Compute Factors
# ---------------------------
print("\n⚡ Computing factor scores ...")
factor_df = compute_factors(etf_data)

# ---------------------------
# 4. Display Results
# ---------------------------
print("\n=== Factor Data ===")
print(factor_df)

# ---------------------------
# 5. Check summary stats
# ---------------------------
print("\n=== Factor Summary ===")
print(factor_df.describe())

# ---------------------------
# 6. Export to CSV for inspection
# ---------------------------
csv_file = "test_etf_factors.csv"
factor_df.to_csv(csv_file, index=False)
print(f"\n✅ Factor scores saved to '{csv_file}'")
