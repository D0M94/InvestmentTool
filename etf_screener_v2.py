import pandas as pd

# --------------------------
# Helper: Z-score normalization
# --------------------------
def zscore_series(series: pd.Series, higher_is_better=True) -> pd.Series:
    """
    Compute z-score normalization for a Pandas Series.
    If higher_is_better=False, the z-score is inverted (lower is better).
    """
    series_clean = pd.to_numeric(series, errors='coerce').dropna()
    mean = series_clean.mean()
    std = series_clean.std()

    if std == 0 or pd.isna(std):
        z = pd.Series(0, index=series.index)
    else:
        z = (series - mean) / std

    if not higher_is_better:
        z = -z

    return z

# --------------------------
# Main screener function
# --------------------------
def create_scorecard(factor_df: pd.DataFrame, weights: dict = None) -> pd.DataFrame:
    """
    Generate a ranked ETF scorecard using z-scores.

    Parameters:
        factor_df: DataFrame with columns:
            Ticker, Momentum, Growth, Value, Volatility, MaxDrawdown, Sentiment
        weights: Optional dictionary of factor weights (sum=1)
            Example: {'Momentum':0.3, 'Growth':0.2, 'Value':0.2, 'Volatility':0.2, 'Sentiment':0.1}

    Returns:
        DataFrame sorted by CompositeScore descending, with Rank column.
    """
    if weights is None:
        weights = {'Momentum': 0.3, 'Growth': 0.2, 'Value': 0.2, 'Volatility': 0.2, 'Sentiment': 0.1}

    df = factor_df.copy()

    # Compute z-scores for each factor
    df['Momentum_z'] = zscore_series(df['Momentum'], higher_is_better=True)
    df['Growth_z'] = zscore_series(df['Growth'], higher_is_better=True)
    df['Value_z'] = zscore_series(df['Value'], higher_is_better=True)
    df['Volatility_z'] = zscore_series(df['Volatility'], higher_is_better=False)  # lower vol better
    df['Sentiment_z'] = zscore_series(df['Sentiment'], higher_is_better=True)

    # Compute weighted composite score
    df['CompositeScore'] = (
        df['Momentum_z'] * weights['Momentum'] +
        df['Growth_z'] * weights['Growth'] +
        df['Value_z'] * weights['Value'] +
        df['Volatility_z'] * weights['Volatility'] +
        df['Sentiment_z'] * weights['Sentiment']
    )

    # Rank ETFs by composite score
    df = df.sort_values(by='CompositeScore', ascending=False).reset_index(drop=True)
    df['Rank'] = df.index + 1

    # Reorder columns for display
    display_cols = [
        'Rank', 'Ticker', 'CompositeScore',
        'Momentum_z', 'Growth_z', 'Value_z', 'Volatility_z', 'Sentiment_z', 'MaxDrawdown'
    ]
    df_scorecard = df[display_cols].copy()

    # Rename z-score columns back to clean names
    df_scorecard.rename(columns={
        'Momentum_z': 'Momentum',
        'Growth_z': 'Growth',
        'Value_z': 'Value',
        'Volatility_z': 'Volatility',
        'Sentiment_z': 'Sentiment'
    }, inplace=True)

    return df_scorecard

# --------------------------
# Example usage / test
# --------------------------
if __name__ == "__main__":
    from factor_engine_v2 import compute_factors
    from etf_loader_v2 import load_etfs

    tickers = ["VOO", "SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "GLD"]

    print("\n--- Loading ETF Data ---")
    etf_data = load_etfs(tickers, period="5y")

    print("\n--- Computing Factors ---")
    factor_df = compute_factors(etf_data)
    print(factor_df)

    print("\n--- Creating Scorecard ---")
    scorecard = create_scorecard(factor_df)
    print(scorecard)


