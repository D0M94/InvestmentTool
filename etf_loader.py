import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
import streamlit as st
from functools import lru_cache
import time


# Global cache for yfinance data (persists across reruns)
@st.cache_data(ttl=3600, show_spinner=False)  # Cache 1 hour
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


@st.cache_data(ttl=3600, show_spinner=False)
def load_info_data(ticker: str) -> Dict[str, Any]:
    """Download ETF metadata with caching."""
    time.sleep(0.1)  # Rate limiting
    return yf.Ticker(ticker).info


@st.cache_data(ttl=3600, hash_funcs={pd.DataFrame: id})  # Cache entire batch
def load_etfs(tickers: List[str], period="max", interval="1d") -> Dict[str, Dict[str, Any]]:
    """Scalable multi-ETF loader with comprehensive caching."""
    results = {}

    # Batch process to minimize API calls
    for ticker in tickers:
        try:
            print(f"📥 Downloading: {ticker}")
            price_df = load_price_data(ticker, period, interval)
            info_dict = load_info_data(ticker)
            results[ticker] = {"prices": price_df, "info": info_dict}
        except Exception as e:
            print(f"⚠️ Failed {ticker}: {e}")
            results[ticker] = {"prices": pd.DataFrame(), "info": {}}

    return results
