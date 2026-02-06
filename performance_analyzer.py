import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict
from etf_loader import load_etfs

# -------------------------- Metrics Calculation -----------------------
def compute_metrics(prices: pd.Series, risk_free_rate: float = 0.03) -> dict:
    """Compute performance metrics for a single price series."""
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

# -------------------------- Cumulative Performance --------------------
def cumulative_performance(prices: pd.Series) -> pd.Series:
    """Return cumulative returns series from price series."""
    if isinstance(prices, pd.DataFrame):
        prices = prices.squeeze()
    prices = prices.dropna()
    returns = prices.pct_change().fillna(0)
    cum_returns = ((1 + returns).cumprod()) - 1
    return cum_returns

# -------------------------- Analyze multiple tickers -------------------
@st.cache_data(ttl=86400*7, show_spinner=False, max_entries=500)  # 7 days + bigger cache
def analyze_tickers(tickers: List[str], period: str = "5y", risk_free_rate: float = 0.0):
    """Cached analysis using shared etf_loader cache."""
    etf_data = load_etfs(tickers, period=period)  # Uses cached loader
    cum_df = pd.DataFrame()
    metrics = {}

    for ticker in tickers:
        try:
            prices = etf_data[ticker]["prices"]["Adj Close"]
        except KeyError:
            print(f"⚠️ {ticker} missing 'Adj Close', skipping")
            continue

        if isinstance(prices, pd.DataFrame):
            prices = prices.squeeze()

        cum_df[ticker] = cumulative_performance(prices)
        metrics[ticker] = compute_metrics(prices, risk_free_rate=risk_free_rate)

    return cum_df, metrics


# -------------------------- Correlation Matrix -----------------------
def compute_correlation_matrix(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the correlation matrix for a dataframe of prices.
    Uses daily returns to find how assets move together.
    """
    if prices_df.empty:
        return pd.DataFrame()

    # Calculate daily returns
    returns = prices_df.pct_change().dropna()

    # Compute Pearson correlation
    corr_matrix = returns.corr()

    return corr_matrix
