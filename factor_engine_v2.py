import pandas as pd
import numpy as np
from typing import Dict, Any, List
import yfinance as yf

# --------------------------
# Helper Functions
# --------------------------

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

# --------------------------
# Stock Factor Computation
# --------------------------

def compute_momentum(prices: pd.Series, period: str = "5y", months: int = 12) -> float:
    """
    Period-aware momentum:
    - 1y period: 6-month momentum (current / 6mo ago)
    - Other periods: Standard 12-month momentum (current / 12mo ago)
    """
    prices = clean_prices(prices)

    if period.lower() == "1y":
        lookback_months = 6
    else:
        lookback_months = months  # Default 12

    n_days = 21 * lookback_months  # Trading days approximation

    if len(prices) < n_days:
        return np.nan

    # Standard: current price vs lookback period ago
    current_price = prices.iloc[-1]  # Latest available price
    past_price = prices.iloc[-n_days]  # Lookback period ago

    momentum_return = (current_price / past_price) - 1
    return float(momentum_return)


def compute_growth(info: Dict[str, Any]) -> float:
    """
    Fundamental Growth: 3-year EPS growth rate or Revenue growth rate
    Higher growth stocks get higher scores
    """
    # Try EPS growth first (most direct growth measure)
    if 'earningsQuarterlyGrowth' in info and info['earningsQuarterlyGrowth'] is not None:
        return info['earningsQuarterlyGrowth']

    # Fallback to Revenue growth
    if 'revenueGrowth' in info and info['revenueGrowth'] is not None:
        return info['revenueGrowth']

    # Fallback to quarterly revenue growth
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

# --------------------------
# ETF Quality: Weighted Avg of Top Holdings ≥70% AUM
# --------------------------

def compute_etf_quality(ticker: str) -> float:
    """
    Compute ETF Quality as weighted average of top holdings covering >=70% of ETF AUM
    """
    try:
        t = yf.Ticker(ticker)
        holdings = t.fund_holdings
        if holdings is None or holdings.empty:
            print(f"⚠️ No holdings data for {ticker}, ETF Quality set to NaN")
            return np.nan

        # Ensure weight is numeric
        holdings = holdings[holdings['Holding'] != "Total"]
        holdings['Weight'] = holdings['Weight'].str.rstrip('%').astype(float)
        holdings = holdings.sort_values('Weight', ascending=False)
        holdings['CumWeight'] = holdings['Weight'].cumsum()

        # Take top holdings covering >=70% AUM
        top_holdings = holdings[holdings['CumWeight'] <= 70]
        if top_holdings.empty:
            top_holdings = holdings.iloc[:1]  # fallback: largest holding

        quality_list = []
        weight_list = []

        for _, row in top_holdings.iterrows():
            stock_ticker = row['Symbol']
            stock_weight = row['Weight'] / 100  # convert percent to fraction
            stock_info = yf.Ticker(stock_ticker).info
            q = compute_quality(stock_info)
            if not np.isnan(q):
                quality_list.append(q)
                weight_list.append(stock_weight)

        if not quality_list:
            return np.nan

        return np.average(quality_list, weights=weight_list)

    except Exception as e:
        print(f"⚠️ Error computing ETF Quality for {ticker}: {e}")
        return np.nan


def compute_cost(info: Dict[str, Any]) -> float:
    """
    Cost factor: Lower expense ratio = higher score
    Try multiple fields in priority order
    """
    # Priority order for expense ratio fields
    expense_fields = [
        'netExpenseRatio',  # Most reliable for ETFs
        'expenseRatio',
        'managementExpenseRatio',
        'totalExpenseRatio'
    ]

    for field in expense_fields:
        expense_ratio = info.get(field)
        if expense_ratio is not None and not np.isnan(expense_ratio) and expense_ratio > 0:
            # Invert: lower expense ratio = higher score
            return 1.0 / (expense_ratio + 0.001)  # Small epsilon prevents div/0
    return np.nan
# --------------------------
# Main Factor Computation
# --------------------------

def compute_factors(etf_data: Dict[str, Dict[str, Any]], period: str = "5y") -> pd.DataFrame:
    factor_rows = []

    for ticker, data in etf_data.items():
        prices = data.get("prices", {}).get("Adj Close", pd.Series())
        info = data.get("info", {})
        quote_type = info.get("quoteType", "").lower()

        row = {
            "Ticker": ticker,
            "Momentum": safe_scalar(compute_momentum(prices, period=period)),  # 👈 Pass period
            "Value": safe_scalar(compute_value(info)),
            "Volatility": safe_scalar(compute_volatility(prices)),
            "Growth": safe_scalar(compute_growth(info)),
            "Size": safe_scalar(compute_size(info)),
            "Cost": safe_scalar(compute_cost(info)),
            "info": info
        }

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




# --------------------------
# Demo / CSV export
# --------------------------

if __name__ == "__main__":
    from etf_loader import load_etfs

    tickers = ["SPY", "QQQ", "EEM"]  # testing
    data = load_etfs(tickers, period="5y")
    factor_df = compute_factors(data)
    print("\n=== Factor Table ===")
    print(factor_df)
    factor_df.to_csv("factors.csv", index=False)
    print("\n✅ Saved factor table to 'factors.csv'")
