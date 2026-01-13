import pandas as pd
import numpy as np
from typing import Dict, Any, List
import streamlit as st

# -------------------------- Helper Functions -------------------------- (UNCHANGED)
def clean_prices(prices: pd.Series) -> pd.Series:
    if isinstance(prices, pd.DataFrame):
        prices = prices.squeeze()
    return prices.dropna()

def compute_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()

def safe_scalar(x):
    try:
        return float(x)
    except Exception:
        return np.nan

# -------------------------- Factor Functions (yfinance calls REMOVED) -------------------
def compute_momentum(prices: pd.Series, period: str = "5y", months: int = 12) -> float:
    prices = clean_prices(prices)
    if period.lower() == "1y":
        lookback_months = 6
    else:
        lookback_months = months
    n_days = 21 * lookback_months
    if len(prices) < n_days:
        return np.nan
    current_price = prices.iloc[-1]
    past_price = prices.iloc[-n_days]
    momentum_return = (current_price / past_price) - 1
    return float(momentum_return)

def compute_growth(info: Dict[str, Any]) -> float:
    if 'earningsQuarterlyGrowth' in info and info['earningsQuarterlyGrowth'] is not None:
        return info['earningsQuarterlyGrowth']
    if 'revenueGrowth' in info and info['revenueGrowth'] is not None:
        return info['revenueGrowth']
    if 'revenueGrowthQuarterlyYOY' in info and info['revenueGrowthQuarterlyYOY'] is not None:
        return info['revenueGrowthQuarterlyYOY']
    return np.nan

def compute_value(info: Dict[str, Any]) -> float:
    pb = info.get("priceToBook")
    pe = info.get("trailingPE")
    if pb:
        return 1 / pb
    elif pe:
        return 1 / pe
    return np.nan

def compute_quality(info: Dict[str, Any]) -> float:
    roe = info.get("returnOnEquity")
    roa = info.get("returnOnAssets")
    gm = info.get("grossMargins")
    for val in [roe, roa, gm]:
        if val is not None:
            return val
    return np.nan

def compute_size(info: Dict[str, Any]) -> float:
    market_cap = info.get("marketCap")
    return market_cap if market_cap is not None else np.nan

def compute_volatility(prices: pd.Series) -> float:
    prices = clean_prices(prices)
    returns = compute_returns(prices)
    return float(returns.std() * np.sqrt(252))

def compute_cost(info: Dict[str, Any]) -> float:
    expense_fields = [
        'netExpenseRatio', 'expenseRatio', 
        'managementExpenseRatio', 'totalExpenseRatio'
    ]
    for field in expense_fields:
        expense_ratio = info.get(field)
        if expense_ratio is not None and not np.isnan(expense_ratio) and expense_ratio > 0:
            return 1.0 / (expense_ratio + 0.001)
    return np.nan

# -------------------------- Main Factor Computation -------------------
def compute_factors(etf_data: Dict[str, Dict[str, Any]], period: str = "5y") -> pd.DataFrame:
    factor_rows = []
    for ticker, data in etf_data.items():
        prices = data.get("prices", pd.DataFrame()).get("Close", pd.Series())  # Use Close if Adj Close missing
        info = data.get("info", {})
        
        row = {
            "Ticker": ticker,
            "Momentum": safe_scalar(compute_momentum(prices, period=period)),
            "Value": safe_scalar(compute_value(info)),
            "Volatility": safe_scalar(compute_volatility(prices)),
            "Growth": safe_scalar(compute_growth(info)),
            "Size": safe_scalar(compute_size(info)),
            "Cost": safe_scalar(compute_cost(info)),
            "info": info
        }
        
        quote_type = info.get("quoteType", "").lower()
        if quote_type == "etf":
            row["Quality"] = np.nan
            row["Growth"] = np.nan
        else:
            row["Quality"] = safe_scalar(compute_quality(info))
            row["Cost"] = np.nan
            
        factor_rows.append(row)
    
    df = pd.DataFrame(factor_rows)
    df = df.sort_values("Ticker").reset_index(drop=True)
    return df
