import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
import streamlit as st
from functools import lru_cache
import time


# Global cache for yfinance data (persists across reruns)
@st.cache_data(ttl=86400*7, show_spinner=False, max_entries=500)  # 7 days + bigger cache
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


@st.cache_data(ttl=86400*30, max_entries=1000)  # 30 days
def load_etfs(tickers: List[str], period="max", interval="1d") -> Dict[str, Dict[str, Any]]:
    """EMERGENCY BULLETPROOF VERSION."""
    results = {}
    for ticker in tickers:
        try:
            # Triple retry with verbose logging
            for attempt in range(3):
                try:
                    df = yf.download(ticker, period=period, progress=False, threads=False)
                    info = yf.Ticker(ticker).info
                    if not df.empty and info:
                        results[ticker] = {"prices": df, "info": info}
                        st.sidebar.success(f"✅ {ticker}")
                        break
                    else:
                        raise ValueError("Empty data")
                except:
                    if attempt == 2:
                        results[ticker] = {"prices": pd.DataFrame(), "info": {}}
                        st.sidebar.error(f"❌ {ticker}")
                    time.sleep(1)
        except Exception as e:
            st.sidebar.error(f"💥 {ticker}: {e}")
            results[ticker] = {"prices": pd.DataFrame(), "info": {}}
    return results
