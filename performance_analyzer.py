import pandas as pd
import numpy as np
from typing import List, Dict


def compute_metrics(prices: pd.Series, risk_free_rate: float = 0.03) -> dict:
    if isinstance(prices, pd.DataFrame):
        prices = prices.squeeze()
    prices = prices.dropna()
    returns = prices.pct_change().dropna()

    total_return = float(prices.iloc[-1] / prices.iloc[0] - 1)
    annual_return = float(returns.mean() * 252)
    annual_vol = float(returns.std() * np.sqrt(252))
    sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol != 0 else np.nan

    return {
        "Total Return": total_return,
        "Annual Return": annual_return,
        "Annual Volatility": annual_vol,
        "Sharpe Ratio": sharpe
    }


def cumulative_performance(prices: pd.Series) -> pd.Series:
    if isinstance(prices, pd.DataFrame):
        prices = prices.squeeze()
    prices = prices.dropna()
    returns = prices.pct_change().fillna(0)
    return ((1 + returns).cumprod()) - 1


# **CRITICAL FIX: Accept preloaded data, NO new downloads**
def analyze_tickers(etf_data: Dict, risk_free_rate: float = 0.0):
    cum_df = pd.DataFrame()
    metrics = {}

    for ticker, data in etf_data.items():
        try:
            prices = data["prices"]["Adj Close"]
            cum_df[ticker] = cumulative_performance(prices)
            metrics[ticker] = compute_metrics(prices, risk_free_rate)
        except:
            continue

    return cum_df, metrics
