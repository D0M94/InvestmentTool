import pandas as pd
import numpy as np


# --------------------------
# Helper Functions
# --------------------------

def zscore_series(series: pd.Series, higher_is_better=True) -> pd.Series:
    """
    Compute z-score normalization.
    If higher_is_better=False, invert the z-score (multiply by -1).
    """
    clean = series.dropna()
    mean = clean.mean()
    std = clean.std()

    if std == 0:
        z = pd.Series(0, index=series.index)
    else:
        z = (series - mean) / std

    if not higher_is_better:
        z = -z

    return z


# --------------------------
# Main Screener Function
# --------------------------

def create_scorecard(factor_df: pd.DataFrame, weights: dict = None) -> pd.DataFrame:
    """
    Generate ranked ETF scorecard using z-scores.

    factor_df: DataFrame from factor_engine.py
        Columns: Ticker, Momentum, Growth, Value, Sentiment, Volatility, MaxDrawdown

    weights: Optional dict of factor weights (sum=1)
        e.g. {'Momentum': 0.3, 'Growth': 0.2, 'Value': 0.2, 'Volatility': 0.2, 'Sentiment': 0.1}
    """
    # Default weights
    if weights is None:
        weights = {'Momentum': 0.3, 'Growth': 0.2, 'Value': 0.2, 'Volatility': 0.2, 'Sentiment': 0.1}

    df = factor_df.copy()

    # Compute z-scores
    df['Momentum_z'] = zscore_series(df['Momentum'], higher_is_better=True)
    df['Growth_z'] = zscore_series(df['Growth'], higher_is_better=True)
    df['Value_z'] = zscore_series(df['Value'], higher_is_better=True)
    df['Volatility_z'] = zscore_series(df['Volatility'], higher_is_better=False)  # lower vol better
    df['Sentiment_z'] = zscore_series(df['Sentiment'], higher_is_better=True)

    # Composite score
    df['CompositeScore'] = (
            df['Momentum_z'] * weights['Momentum'] +
            df['Growth_z'] * weights['Growth'] +
            df['Value_z'] * weights['Value'] +
            df['Volatility_z'] * weights['Volatility'] +
            df['Sentiment_z'] * weights['Sentiment']
    )

    # Rank ETFs
    df = df.sort_values(by='CompositeScore', ascending=False).reset_index(drop=True)
    df['Rank'] = df.index + 1

    # Reorder columns
    scorecard_cols = [
        'Rank', 'Ticker', 'CompositeScore',
        'Momentum_z', 'Growth_z', 'Value_z', 'Volatility_z', 'Sentiment_z', 'MaxDrawdown'
    ]
    df_scorecard = df[scorecard_cols]

    # Rename normalized columns for display
    df_scorecard.rename(columns={
        'Momentum_z': 'Momentum',
        'Growth_z': 'Growth',
        'Value_z': 'Value',
        'Volatility_z': 'Volatility',
        'Sentiment_z': 'Sentiment'
    }, inplace=True)

    return df_scorecard


# --------------------------
# Example usage
# --------------------------
if __name__ == "__main__":
    from factor_engine import compute_factors
    from etf_loader import load_etfs

    tickers = ["VOO", "SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "GLD"]

    # Load ETF data
    etf_data = load_etfs(tickers, period="5y")

    # Compute factors
    factor_df = compute_factors(etf_data)

    # Create scorecard
    scorecard = create_scorecard(factor_df)

    print("\n=== Ranked ETF Scorecard (Volatility as risk) ===")
    print(scorecard)

    # Save to CSV
    scorecard.to_csv("etf_scorecard_volatility.csv", index=False)
    print("\n✅ Scorecard saved to 'etf_scorecard_volatility.csv'")
