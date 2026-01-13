import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
import time
import numpy as np

def load_etfs(tickers: List[str], period="max", interval="1d") -> Dict[str, Dict]:
    """YOUR ORIGINAL STRUCTURE - SEQUENTIAL REQUESTS (No cache, no rate limits)"""
    results = {}
    
    for i, ticker in enumerate(tickers):
        # 🔥 SEQUENTIAL: 250ms delay between requests (Yahoo safe)
        if i > 0:
            time.sleep(0.25)
            
        data_valid = False
        
        # Try 3 times with exponential backoff
        for attempt in range(3):
            try:
                print(f"📥 Loading {ticker} ({i+1}/{len(tickers)}) - attempt {attempt+1}")
                
                # Single sequential request per ticker
                t = yf.Ticker(ticker)
                hist = t.history(period=period, interval=interval, prepost=False)
                
                # Validate data quality
                if (not hist.empty and 
                    len(hist) >= 10 and 
                    'Close' in hist.columns and 
                    hist['Close'].count() >= 5):
                    
                    # Standardize format for your original scripts
                    hist = hist[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index()
                    hist.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                    hist['Date'] = pd.to_datetime(hist['Date'])
                    
                    results[ticker] = {
                        "prices": hist,
                        "info": getattr(t, 'info', {})
                    }
                    data_valid = True
                    break
                
            except Exception as e:
                print(f"⚠️ {ticker} attempt {attempt+1} failed: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
        
        # Fallback for failed tickers (your original scripts expect this)
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
