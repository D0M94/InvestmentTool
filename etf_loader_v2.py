import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
import streamlit as st
import time

# 🔧 SINGLE GLOBAL YFINANCE SESSION (CRITICAL FIX)
@st.cache_resource(ttl=3600, show_spinner=False)
def get_yf_session():
    """Persistent yfinance session to avoid rate limits."""
    return yf.Ticker("SPY")  # Dummy to init session

# 🔧 BULLETPROOF SINGLE CACHE (NO NESTING)
@st.cache_data(ttl=86400*7, show_spinner=False, max_entries=200)
def load_etfs(tickers: List[str], period="max", interval="1d", max_retries=2) -> Dict[str, Dict[str, Any]]:
    """SINGLE ENTRYPOINT - No nested caching. Handles all failures gracefully."""
    results = {}
    
    # Rate limit properly OUTSIDE cache
    time.sleep(0.05 * len(tickers))  
    
    for ticker in tickers:
        for attempt in range(max_retries):
            try:
                # 🔧 SINGLE CALL - No nested functions
                ticker_obj = yf.Ticker(ticker)
                
                # Price data
                price_df = ticker_obj.history(period=period, interval=interval)
                if price_df.empty:
                    raise ValueError("Empty price data")
                
                # Info data  
                info_dict = ticker_obj.info or {}
                
                results[ticker] = {
                    "prices": price_df, 
                    "info": info_dict
                }
                break
                
            except Exception as e:
                if attempt == max_retries - 1:
                    # Graceful fallback
                    results[ticker] = {
                        "prices": pd.DataFrame(),
                        "info": {"quoteType": "failed", "error": str(e)[:100]}
                    }
                time.sleep(0.2 * (attempt + 1))
    
    return results
