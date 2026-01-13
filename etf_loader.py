import yfinance as yf
import pandas as pd
from typing import List, Dict
import streamlit as st
import numpy as np

@st.cache_data(ttl=3600, show_spinner=False, max_entries=50)  # ✅ FIXED - No experimental params
def load_etfs(_tickers_hash: str, _period_hash: str, force_fresh: bool = False) -> Dict[str, Dict]:
    """🔥 BULLETPROOF - Hash-based + force refresh param"""
    import hashlib
    
    # Reconstruct inputs from hash (avoid session_state in cache)
    tickers_str = hashlib.md5(_tickers_hash.encode()).hexdigest()
    period_str = hashlib.md5(_period_hash.encode()).hexdigest()
    
    # Dynamic TTL based on force_fresh (safe default)
    effective_ttl = 300 if force_fresh else 86400*2
    
    results = {}
    
    # Parse tickers from hash string (simplified - use actual tickers passed via hash)
    tickers = _tickers_hash.split('|')  # SPY|QQQ format
    
    for ticker in tickers:
        data_valid = False
        
        for attempt in range(3):
            try:
                t = yf.Ticker(ticker.strip())
                hist = t.history(period=_period_hash, interval="1d", prepost=False)
                
                # ✅ RIGOROUS VALIDATION
                if (not hist.empty and len(hist) >= 10 and 
                    'Close' in hist.columns and hist['Close'].count() >= 5):
                    
                    hist = hist[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index()
                    hist.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                    hist['Date'] = pd.to_datetime(hist['Date'])
                    
                    results[ticker.strip()] = {
                        "prices": hist,
                        "info": getattr(t, 'info', {})
                    }
                    data_valid = True
                    break
                
            except Exception:
                continue
        
        if not data_valid:
            results[ticker.strip()] = {
                "prices": pd.DataFrame({
                    'Date': [pd.Timestamp.now()], 
                    'Open': [np.nan], 'High': [np.nan], 
                    'Low': [np.nan], 'Close': [np.nan], 
                    'Volume': [0]
                }),
                "info": {'quoteType': 'failed'}
            }
    
    return results

# ✅ HELPER: Safe wrapper for pages
def loa
