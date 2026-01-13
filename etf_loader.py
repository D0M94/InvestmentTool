etf_loader.py:
import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
import streamlit as st
from functools import lru_cache
import time


def load_price_data(ticker: str, period="max", interval="1d") -> pd.DataFrame:
    """Download OHLCV + Adj Close for a single ETF with rate limit protection."""
    time.sleep(0.1)  # Rate limiting
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False  # Single thread to avoid rate limits
    )
    return df


def load_info_data(ticker: str) -> Dict[str, Any]:
    """Download ETF metadata with caching."""
    time.sleep(0.1)  # Rate limiting
    return yf.Ticker(ticker).info


def load_etfs(tickers: List[str], period="max", interval="1d", max_retries=3) -> Dict[str, Dict[str, Any]]:
    """Bulletproof loader with retries + fallbacks."""
    results = {}

    for ticker in tickers:
        for attempt in range(max_retries):
            try:
                print(f"📥 [{attempt + 1}/{max_retries}] Downloading: {ticker}")

                # Price data with retry
                price_df = load_price_data(ticker, period, interval)
                if price_df.empty:
                    raise Exception("Empty price data")

                # Info data with retry
                info_dict = load_info_data(ticker)

                results[ticker] = {"prices": price_df, "info": info_dict}
                break  # Success!

            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed for {ticker}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                else:
                    # Fallback: empty but valid structure
                    print(f"❌ {ticker} FAILED - using fallback")
                    results[ticker] = {
                        "prices": pd.DataFrame(),
                        "info": {"quoteType": "unknown"}
                    }

    return results
