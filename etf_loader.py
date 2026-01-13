import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
import time

def load_etfs(tickers: List[str], period="max", interval="1d", max_retries=3) -> Dict[str, Dict[str, Any]]:
    """Your original loader - NOW SEQUENTIAL (no rate limits)"""
    results = {}

    for i, ticker in enumerate(tickers):
        # 🔥 SEQUENTIAL: 200ms between tickers (Yahoo safe)
        if i > 0:
            time.sleep(0.2)
            
        for attempt in range(max_retries):
            try:
                print(f"📥 [{i+1}/{len(tickers)}] {ticker}")

                # Single sequential call per ticker
                price_df = yf.download(
                    ticker,
                    period=period,
                    interval=interval,
                    auto_adjust=False,
                    progress=False,
                    threads=False  # Single thread
                )
                if price_df.empty:
                    raise Exception("Empty price data")

                info_dict = yf.Ticker(ticker).info

                results[ticker] = {"prices": price_df, "info": info_dict}
                break

            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed for {ticker}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    results[ticker] = {
                        "prices": pd.DataFrame(),
                        "info": {"quoteType": "unknown"}
                    }

    return results
