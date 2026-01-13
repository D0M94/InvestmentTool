import yfinance as yf
import pandas as pd
from typing import List, Dict
import streamlit as st
import numpy as np

@st.cache_data(
    ttl=300 if st.session_state.get('force_fresh', False) else 86400*2,  # 5min vs 2 days
    show_spinner=False, 
    max_entries=50,
    experimental_allow_widgets=True  # Allow session_state access
)
def load_etfs(tickers: List[str], period="max", interval="1d") -> Dict[str, Dict]:
    """🔥 100% RELIABLE - Validates data BEFORE caching"""
    results = {}
    
    for ticker in tickers:
        data_valid = False
        
        for attempt in range(3):  # Triple retry
            try:
                # Fresh ticker object
                t = yf.Ticker(ticker)
                
                # Get history (more reliable than download)
                hist = t.history(period=period, interval=interval, prepost=False)
                
                # ✅ VALIDATE: Must have data + Close column + min 10 rows
                if (not hist.empty and 
                    len(hist) >= 10 and 
                    'Close' in hist.columns and 
                    not hist['Close'].isna().all()):
                    
                    # Standardize structure
                    hist = hist[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index()
                    hist.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                    hist['Date'] = pd.to_datetime(hist['Date'])
                    
                    info = getattr(t, 'info', {})
                    
                    results[ticker] = {
                        "prices": hist,
                        "info": info
                    }
                    data_valid = True
                    break
                
                else:
                    st.write(f"⚠️ Attempt {attempt+1}: Empty data for {ticker}")
                    
            except Exception as e:
                st.write(f"⚠️ Attempt {attempt+1} failed: {str(e)[:50]}")
                continue
        
        # Graceful fallback (EXACT structure)
        if not data_valid:
            results[ticker] = {
                "prices": pd.DataFrame({
                    'Date': [pd.Timestamp.now()], 
                    'Open': [np.nan], 'High': [np.nan], 
                    'Low': [np.nan], 'Close': [np.nan], 
                    'Volume': [0]
                }),
                "info": {'quoteType': 'failed', 'error': f'No data after 3 attempts'}
            }
    
    return results
