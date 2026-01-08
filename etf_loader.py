
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


def load_etfs(tickers: List[str], period="max", interval="1d") -> Dict[str, Dict[str, Any]]:
    """
    Scalable multi-ETF loader.
    Returns:
        {
            "VOO": {"prices": DataFrame, "info": dict},
            "SPY": {...}
        }
    """
    results = {}

    for ticker in tickers:
        print(f"Downloading: {ticker}")

        price_df = load_price_data(ticker, period, interval)
        info_dict = load_info_data(ticker)

        results[ticker] = {"prices": price_df, "info": info_dict}

    return results
