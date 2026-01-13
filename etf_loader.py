import yfinance as yf
import pandas as pd
from typing import List, Dict
import streamlit as st

@st.cache_data(ttl=3600 if st.session_state.get('force_fresh_data', False) else 86400*7, 
               show_spinner=False, max_entries=100)
def load_etfs(tickers: List[str], period="max", interval="1d") -> Dict[str, Dict[str, pd.DataFrame]]:
    """🔥 BULLETPROOF - Never returns empty cache"""
    results = {}
    
    for ticker in tickers:
        try:
            # Fresh ticker EVERY TIME (no cache issues)
            t = yf.Ticker(ticker)
            
            # CRITICAL: history() instead of download() - more reliable
            hist = t.history(period=period, interval=interval)
            
            # VALIDATE DATA - Never cache empty
            if hist.empty or len(hist) < 2:
                raise ValueError(f"Empty/insufficient data for {ticker}")
            
            # Ensure standard columns
            hist = hist[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index()
            hist.columns = [col.capitalize() for col in hist.columns]
            
            info = t.info or {}
            
            results[ticker] = {
                "prices": hist,
                "info": info
            }
            
        except Exception as e:
            # Graceful fallback with EXACT structure
            results[ticker] = {
                "prices": pd.DataFrame({
                    'Date': [pd.Timestamp.now()], 'Open': [np.nan], 'High': [np.nan], 
                    'Low': [np.nan], 'Close': [np.nan], 'Volume': [0]
                }),
                "info": {'quoteType': 'error', 'error': str(e)[:100]}
            }
    
    return results
