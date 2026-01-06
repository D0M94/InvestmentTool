import pandas as pd
import numpy as np
from typing import Dict, Any, List
import yfinance as yf
import time


def clean_prices(prices: pd.Series) -> pd.Series:
    if isinstance(prices, pd.DataFrame):
        prices = prices.squeeze()
    return prices.dropna()


def compute_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()


def safe_scalar(x):
    try:
        return float(x)
    except:
        return np.nan


def compute_momentum(prices: pd.Series, period: str = "5y", months: int = 12) -> float:
    prices = clean_prices(prices)
    if period.lower() == "1y":
        n_days = 21 * 6
    else:
        n_days = 21 * 12

    if len(prices) < n_days:
        return np.nan
    current = prices.iloc[-1]
    past = prices.iloc[-n_days]
    return (current / past) - 1


def compute_growth(info: Dict[str, Any]) -> float:
    growth_fields = ['earningsQuarterlyGrowth', 'revenueGrowth', 'revenueGrowthQuarterlyYOY']
    for field in growth_fields:
        val = info.get(field)
        if val is not None and not np.isnan(val):
            return float(val)
    return np.nan


def compute_value(info: Dict[str, Any]) -> float:
    pb = info.get("priceToBook")
    pe = info.get("trailingPE")
    return 1 / pb if pb else (1 / pe if pe else np.nan)


def compute_quality(info: Dict[str, Any]) -> float:
    quality_fields = ['returnOnEquity', 'returnOnAssets', 'grossMargins']
    for field in quality_fields:
        val = info.get(field)
        if val is not None and not np.isnan(val):
            return float(val)
    return np.nan


def compute_size(info: Dict[str, Any]) -> float:
    return info.get("marketCap")


def compute_volatility(prices: pd.Series) -> float:
    returns = compute_returns(clean_prices(prices))
    return float(returns.std() * np.sqrt(252))


# **DISABLED - WAS CAUSING 500+ RATE LIMIT CALLS**
def compute_etf_quality(ticker: str) -> float:
    return 0.5  # Neutral score


def compute_cost(info: Dict[str, Any]) -> float:
    expense_fields = ['netExpenseRatio', 'expenseRatio', 'managementExpenseRatio']
    for field in expense_fields:
        val = info.get(field)
        if val is not None and val > 0:
            return 1.0 / (val + 0.001)
    return np.nan


def compute_factors(etf_data: Dict[str, Dict[str, Any]], period: str = "5y") -> pd.DataFrame:
    factor_rows = []
    for ticker, data in etf_data.items():
        prices = data.get("prices", {}).get("Adj Close", pd.Series())
        info = data.get("info", {})

        row = {
            "Ticker": ticker,
            "Momentum": safe_scalar(compute_momentum(prices, period)),
            "Value": safe_scalar(compute_value(info)),
            "Volatility": safe_scalar(compute_volatility(prices)),
            "Growth": safe_scalar(compute_growth(info)),
            "Size": safe_scalar(compute_size(info)),
            "Cost": safe_scalar(compute_cost(info)),
            "info": info
        }
        factor_rows.append(row)

    return pd.DataFrame(factor_rows)
