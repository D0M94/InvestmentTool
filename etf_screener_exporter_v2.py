# etf_screener_exporter_v2.py
import pandas as pd
import numpy as np

def zscore_series(series: pd.Series, invert=False):
    z = (series - series.mean()) / series.std()
    return -z if invert else z

def create_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        print("❌ No data for scorecard.")
        return df

    df = df.copy()

    df["Momentum_z"] = zscore_series(df["Momentum"])
    df["Growth_z"] = zscore_series(df["Growth"])
    df["Value_z"] = zscore_series(df["Value"])
    df["Volatility_z"] = zscore_series(df["Volatility"], invert=True)  # lower vol → better
    df["Drawdown_z"] = zscore_series(df["MaxDrawdown"], invert=True)   # smaller drawdown → better
    df["Sentiment_z"] = 0

    df["CompositeScore"] = df[
        ["Momentum_z", "Growth_z", "Value_z", "Volatility_z", "Drawdown_z"]
    ].mean(axis=1)

    df = df.sort_values("CompositeScore", ascending=False)
    return df

def pretty_table(df: pd.DataFrame):
    if df.empty:
        print("⚠️ Nothing to display — empty dataframe.")
        return

    print("\n=== ETF SCREENER RESULT ===")
    print(df.to_string(index=False))
