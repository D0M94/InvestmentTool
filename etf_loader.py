import yfinance as yf
import pandas as pd
from typing import List, Dict, Any


def load_price_data(ticker: str, period="max", interval="1d") -> pd.DataFrame:
    """
    Download OHLCV + Adj Close for a single ETF.
    """
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False
    )
    return df


def load_info_data(ticker: str) -> Dict[str, Any]:
    """
    Download ETF metadata (full .info dictionary from yfinance).
    """
    return yf.Ticker(ticker).info


@st.cache_data(ttl=1800, max_entries=20)
def load_etfs(tickers: List[str], period: str = "5y") -> Dict[str, Dict[str, Any]]:
    """SINGLE TICKER DOWNLOAD WITH DELAYS"""
    results = {}

    for ticker in tickers:
        try:
            time.sleep(1.0)  # RATE LIMIT PROTECTION
            yf_ticker = yf.Ticker(ticker)
            results[ticker] = {
                "prices": yf_ticker.history(period=period),
                "info": yf_ticker.info
            }
        except:
            results[ticker] = {"prices": pd.DataFrame(), "info": {}}

    return results