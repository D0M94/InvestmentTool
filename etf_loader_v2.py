# etf_loader_v2.py
import yfinance as yf
import pandas as pd

EXPECTED_FIELDS = {"Open", "High", "Low", "Close", "Volume"}

def load_etf_price_history(ticker: str, period="2y", interval="1d"):
    """
    Loads ETF data using yfinance with auto_adjust=True,
    which ensures OHLC data is always present.
    """

    print(f"📥 Downloading {ticker} ...")

    df = yf.download(
        ticker,
        period=period,
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        print(f"❌ No data returned for {ticker}")
        return None

    # Ensure required fields exist
    missing = EXPECTED_FIELDS - set(df.columns)
    if missing:
        print(f"⚠️ {ticker} missing fields {missing}")
        # But data still usable if Close exists
        if "Close" not in df.columns:
            print(f"❌ Cannot use {ticker} — Close price missing.")
            return None

    df = df.dropna()
    return df
