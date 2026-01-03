import pandas as pd
import numpy as np
from typing import Dict, Any


# --------------------------
# Helper Functions
# --------------------------

def clean_prices(prices: pd.Series) -> pd.Series:
    """
    Ensure prices are a Series and drop NaNs
    """
    if isinstance(prices, pd.DataFrame):
        prices = prices.squeeze()
    return prices.dropna()


def compute_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()


def compute_momentum(prices: pd.Series, months: int = 12) -> float:
    """
    Trailing momentum: return over past `months`, skipping last month
    """
    prices = clean_prices(prices)
    n_days = 21 * months  # approx trading days per month
    if len(prices) < n_days + 21:
        return np.nan
    start_price = prices.iloc[-(n_days + 21)]
    end_price = prices.iloc[-21]
    return (end_price / start_price) - 1


def compute_growth(prices: pd.Series) -> float:
    """
    Simple 1-year growth proxy: % price change
    """
    prices = clean_prices(prices)
    if len(prices) < 252:
        return np.nan
    return (prices.iloc[-1] / prices.iloc[-252]) - 1


def compute_value(info: Dict[str, Any]) -> float:
    """
    Value factor proxy: 1/PB or 1/PE if available
    """
    pb = info.get("priceToBook")
    pe = info.get("trailingPE")
    if pb:
        return 1 / pb
    elif pe:
        return 1 / pe
    else:
        return np.nan


def compute_volatility(prices: pd.Series) -> float:
    prices = clean_prices(prices)
    returns = compute_returns(prices)
    return float(returns.std() * np.sqrt(252))


def compute_max_drawdown(prices: pd.Series) -> float:
    prices = clean_prices(prices)
    cumulative = prices / prices.iloc[0]
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    return float(drawdown.min())



def compute_sentiment(info: Dict[str, Any]) -> float:
    """
    Placeholder for sentiment factor
    """
    return 0  # can add news/social sentiment later


# --------------------------
# Main Factor Computation
# --------------------------

def compute_factors(etf_data: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Compute all factors and prepare DataFrame for CSV/table export.
    Returns:
        DataFrame: one row per ETF, columns = factors + ticker
    """
    factor_rows = []

    for ticker, data in etf_data.items():
        try:
            prices = data["prices"]["Adj Close"]
        except KeyError:
            print(f"⚠️ Missing 'Adj Close' for {ticker}, skipping")
            continue

        row = {
            "Ticker": ticker,
            "Momentum": compute_momentum(prices),
            "Growth": compute_growth(prices),
            "Value": compute_value(data["info"]),
            "Volatility": compute_volatility(prices),  # only volatility
            "MaxDrawdown": compute_max_drawdown(prices),
            "Sentiment": compute_sentiment(data["info"])
        }

        factor_rows.append(row)

    df = pd.DataFrame(factor_rows)

    # Optional: sort by Ticker
    df = df.sort_values(by="Ticker").reset_index(drop=True)

    return df


# --------------------------
# Example CSV Export
# --------------------------

if __name__ == "__main__":
    # Example usage
    from etf_loader import load_etfs

    tickers = ["VOO", "SPY", "QQQ"]
    data = load_etfs(tickers, period="5y")

    factor_df = compute_factors(data)

    print("\n=== Factor Data ===")
    print(factor_df)

    # Export to CSV
    factor_df.to_csv("etf_factor_scores.csv", index=False)
    print("\n✅ Saved factor scores to 'etf_factor_scores.csv'")
