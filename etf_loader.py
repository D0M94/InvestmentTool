import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
import time
from functools import wraps


def retry_on_rate_limit(max_retries=5, base_delay=2):
    """
    Decorator for exponential backoff on yfinance rate limits.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    if "rate limit" in error_str or "too many requests" in error_str:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt) + np.random.uniform(0, 1)
                            print(f"Rate limited on attempt {attempt + 1}/{max_retries}. Waiting {delay:.1f}s...")
                            time.sleep(delay)
                            continue
                    raise e
            return pd.DataFrame()  # Empty on final failure

        return wrapper

    return decorator


@retry_on_rate_limit()
def load_price_data(ticker: str, period="max", interval="1d") -> pd.DataFrame:
    """
    Download OHLCV + Adj Close for a single ETF with rate limit handling.
    """
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,  # Disable threading to reduce burst requests
        prepost=False
    )
    if df.empty:
        raise ValueError(f"No data for {ticker}")
    return df


@retry_on_rate_limit()
def load_info_data(ticker: str) -> Dict[str, Any]:
    """
    Download ETF metadata with rate limit handling.
    """
    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.info
    if not info:
        raise ValueError(f"No info for {ticker}")
    return info


def load_etfs(tickers: List[str], period="max", interval="1d") -> Dict[str, Dict[str, Any]]:
    """
    Scalable multi-ETF loader with sequential processing and delays.
    Returns:
        {
            "VOO": {"prices": DataFrame, "info": dict},
            "SPY": {...}
        }
    """
    results = {}

    for i, ticker in enumerate(tickers):
        print(f"Downloading: {ticker} ({i + 1}/{len(tickers)})")

        try:
            # Small delay between tickers to respect rates
            if i > 0:
                time.sleep(0.5)

            price_df = load_price_data(ticker, period, interval)
            info_dict = load_info_data(ticker)

            results[ticker] = {"prices": price_df, "info": info_dict}

        except Exception as e:
            print(f"Failed to load {ticker}: {str(e)}")
            results[ticker] = {"prices": pd.DataFrame(), "info": {}}

    return results
