# Save as test_etf_info.py and run: python test_etf_info.py
import yfinance as yf
import pandas as pd
import numpy as np
from factor_engine_v2 import compute_cost  # Your cost function

tickers = ["EEM", "SPY", "QQQ"]

with open("etf_info_dump.txt", "w") as f:
    f.write("=== ETF INFO DUMP ===\n\n")

    for ticker in tickers:
        f.write(f"\n{'=' * 60}\n")
        f.write(f"ETFs: {ticker}\n")
        f.write(f"{'=' * 60}\n")

        # Get full info
        etf = yf.Ticker(ticker)
        info = etf.info

        # Raw info dump
        f.write(f"Total keys: {len(info)}\n\n")
        f.write("ALL KEYS AND VALUES:\n")
        for key, value in sorted(info.items()):
            f.write(f"{key}: {value} ({type(value)})\n")

        # Cost calculation debug
        f.write(f"\n=== COST CALCULATION DEBUG ===\n")
        cost_score = compute_cost(info)
        f.write(f"compute_cost() result: {cost_score}\n")

        # Check all expense fields
        expense_fields = [
            'annualReportExpenseRatio', 'expenseRatio',
            'managementExpenseRatio', 'totalExpenseRatio',
            'fees', 'annualHoldingsTurnover'
        ]
        f.write("Expense fields check:\n")
        for field in expense_fields:
            val = info.get(field)
            f.write(f"  {field}: {val} ({type(val)})\n")

        f.write(f"\nRaw factor row:\n")
        mock_row = {
            "Ticker": ticker,
            "info": info,
            "Cost": cost_score
        }
        f.write(f"Cost in mock row: {mock_row['Cost']}\n")

        print(f"✅ {ticker}: Cost = {cost_score}")

print("\n✅ FULL INFO DUMP SAVED to etf_info_dump.txt")
print("Check the file to see ALL available fields!")
