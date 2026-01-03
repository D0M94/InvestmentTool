"""
etf_exporter_v2.py
Handles exporting factor results into CSV, Excel, JSON, and pretty terminal tables.
"""

import pandas as pd
import os


# --------------------------
# CSV Export
# --------------------------

def export_to_csv(df: pd.DataFrame, path: str = "output/etf_factors.csv") -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return path


# --------------------------
# Excel Export
# --------------------------

def export_to_excel(df: pd.DataFrame, path: str = "output/etf_factors.xlsx") -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_excel(path, index=False)
    return path


# --------------------------
# JSON Export
# --------------------------

def export_to_json(df: pd.DataFrame, path: str = "output/etf_factors.json") -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_json(path, orient="records", indent=2)
    return path


# --------------------------
# Pretty Print
# --------------------------

def pretty_table(df: pd.DataFrame):
    """
    Print a clean terminal table with aligned columns.
    """
    if df.empty:
        print("No data to display")
        return

    # Format numeric columns nicely
    display_df = df.copy()
    for col in display_df.columns:
        if display_df[col].dtype == float:
            display_df[col] = display_df[col].map(lambda x: f"{x:,.4f}" if pd.notnull(x) else "NaN")

    print("\n=== ETF FACTOR TABLE ===\n")
    print(display_df.to_string(index=False))
    print("\n========================\n")


# --------------------------
# Master Export Function
# --------------------------

def export_all(df: pd.DataFrame, prefix: str = "output/etf_factors") -> dict:
    """
    Creates CSV, Excel, JSON and returns paths.
    """
    paths = {
        "csv": export_to_csv(df, f"{prefix}.csv"),
        "xlsx": export_to_excel(df, f"{prefix}.xlsx"),
        "json": export_to_json(df, f"{prefix}.json"),
    }
    return paths


# --------------------------
# Example usage
# --------------------------

if __name__ == "__main__":
    sample = pd.DataFrame({
        "Ticker": ["VOO", "QQQ"],
        "Momentum": [0.12, 0.09],
        "Growth": [0.15, 0.20],
        "Value": [0.03, 0.01],
        "Volatility": [0.18, 0.22],
        "MaxDrawdown": [-0.35, -0.42],
        "Sentiment": [0, 0]
    })

    pretty_table(sample)
    files = export_all(sample)
    print("Exported:", files)
