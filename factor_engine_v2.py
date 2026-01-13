import pandas as pd
import numpy as np
from typing import Dict, Any, List
import streamlit as st
import yfinance as yf
import time


# -------------------------- Helper Functions --------------------------
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


# -------------------------- Cached yfinance calls ---------------------
def get_cached_holdings(ticker: str) -> pd.DataFrame:
    """Cached ETF holdings - called ONCE per ticker lifetime."""
    time.sleep(0.2)  # Conservative rate limiting
    try:
        t = yf.Ticker(ticker)
        holdings = t.fund_holdings
        if holdings is None or holdings.empty:
            return pd.DataFrame()
        return holdings
    except:
        return pd.DataFrame()


def get_cached_stock_info(ticker: str) -> Dict[str, Any]:
    """Cached individual stock info."""
    time.sleep(0.1)
    try:
        return yf.Ticker(ticker).info
    except:
        return {}


# -------------------------- Stock Factor Computation -------------------
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


# -------------------------- FIXED ETF Quality (DISABLED BY DEFAULT) ------------------
def compute_etf_quality(ticker: str, _use_holdings=True) -> float:
    """DISABLED holdings analysis by default to avoid rate limits."""
    if _use_holdings:  # Only enable for small # tickers
        try:
            holdings = get_cached_holdings(ticker)
            if holdings.empty:
                return np.nan

            holdings = holdings[holdings['Holding'] != "Total"]
            holdings['Weight'] = holdings['Weight'].str.rstrip('%').astype(float)
            holdings = holdings.sort_values('Weight', ascending=False)
            holdings['CumWeight'] = holdings['Weight'].cumsum()

            top_holdings = holdings[holdings['CumWeight'] <= 70]
            if top_holdings.empty:
                top_holdings = holdings.iloc[:1]

            quality_list = []
            weight_list = []
            for _, row in top_holdings.iterrows():
                stock_ticker = row['Symbol']
                stock_weight = row['Weight'] / 100
                stock_info = get_cached_stock_info(stock_ticker)
                q = compute_quality(stock_info)
                if not np.isnan(q):
                    quality_list.append(q)
                    weight_list.append(stock_weight)

            if not quality_list:
                return np.nan
            return np.average(quality_list, weights=weight_list)
        except Exception as e:
            print(f"⚠️ ETF Quality skipped for {ticker}: {e}")
            return np.nan
    return np.nan  # Skip expensive holdings analysis


def compute_cost(info: Dict[str, Any]) -> float:
    expense_fields = [
        'netExpenseRatio',
        'expenseRatio',
        'managementExpenseRatio',
        'totalExpenseRatio'
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
        prices = data.get("prices", {}).get("Adj Close", pd.Series())
        info = data.get("info", {})
        quote_type = info.get("quoteType", "").lower()

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

        if quote_type == "etf":
            row["Quality"] = np.nan  # DISABLED - too expensive
            row["Growth"] = np.nan
        else:
            row["Quality"] = safe_scalar(compute_quality(info))
            row["Cost"] = np.nan

        factor_rows.append(row)

    df = pd.DataFrame(factor_rows)
    df = df.sort_values("Ticker").reset_index(drop=True)
    return df
