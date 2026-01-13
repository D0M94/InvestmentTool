import yfinance as yf
import pandas as pd
from typing import List, Dict
import streamlit as st
import numpy as np

@st.cache_data(ttl=3600, show_spinner=False, max_entries=50)
def load_etfs(tickers: List[str], period="max", interval="1d") -> Dict[str, Dict]:
    """🔥 BULLETPROOF - Never returns empty cache"""
    results = {}
    
    for ticker in tickers:
        data_valid = False
        
        for attempt in range(3):
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period=period, interval=interval, prepost=False)
                
                if (not hist.empty and len(hist) >= 10 and 
                    'Close' in hist.columns and hist['Close'].count() >= 5):
                    
                    hist = hist[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index()
                    hist.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                    hist['Date'] = pd.to_datetime(hist['Date'])
                    
                    results[ticker] = {
                        "prices": hist,
                        "info": getattr(t, 'info', {})
                    }
                    data_valid = True
                    break
                
            except Exception:
                continue
        
        if not data_valid:
            results[ticker] = {
                "prices": pd.DataFrame({
                    'Date': [pd.Timestamp.now()], 
                    'Open': [np.nan], 'High': [np.nan], 
                    'Low': [np.nan], 'Close': [np.nan], 
                    'Volume': [0]
                }),
                "info": {'quoteType': 'failed'}
            }
    
    return results
