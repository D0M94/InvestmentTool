import pandas as pd
import numpy as np

# --------------------------
# CONFIGURABLE WEIGHTS
# --------------------------
STOCK_WEIGHTS = {
    "Momentum": 0.2,
    "Value": 0.20,
    "Volatility": 0.2,  # Lower is better (inverted in z-score)
    "Quality": 0.20,
    "Growth": 0.15,
    "Size": 0.05
}

ETF_WEIGHTS = {
    "Momentum": 0.25,
    "Value": 0.25,
    "Volatility": 0.25,  # Lower is better (inverted in z-score)
    "Size": 0.125,
    "Cost": 0.125  # Lower expense = better (inverted in z-score)
}


# --------------------------
# Z-score Helper (Now with Baseline Support)
# --------------------------
def zscore_series(series: pd.Series, baseline_value: float = None, higher_is_better=True) -> pd.Series:
    """
    Calculates Z-scores.
    If baseline_value is provided, the 'Mean' is anchored to that value (0.0).
    """
    clean = series.dropna()
    if clean.empty:
        return pd.Series(np.nan, index=series.index)

    # Use the benchmark as the center if provided, otherwise use group mean
    mean = clean.mean() if baseline_value is None else baseline_value
    std = clean.std()

    # Avoid division by zero
    if std == 0 or np.isnan(std):
        z = pd.Series(0.0, index=series.index)
    else:
        z = (series - mean) / std

    # Invert for factors where 'Lower is Better' (Volatility, Cost)
    if not higher_is_better:
        z = -z

    return z


# --------------------------
# Scorecard Engine
# --------------------------
def create_scorecard(factor_df: pd.DataFrame, is_etf: bool = True, benchmark_ticker: str = None) -> pd.DataFrame:
    """
    Computes a weighted factor scorecard.
    benchmark_ticker: If provided, Z-scores are calculated relative to this ticker.
    """
    weights = ETF_WEIGHTS if is_etf else STOCK_WEIGHTS

    scorecard = factor_df[["Ticker"]].copy()
    z_scores = pd.DataFrame(index=factor_df.index)

    # Calculate Z-scores for each factor
    for factor, weight in weights.items():
        if factor in factor_df.columns:
            # Determine if higher or lower is better
            higher_is_better = False if factor in ["Volatility", "Cost"] else True

            # Find the benchmark's raw value for this factor to use as the 'Zero' anchor
            baseline = None
            if benchmark_ticker and benchmark_ticker in factor_df["Ticker"].values:
                baseline = factor_df.loc[factor_df["Ticker"] == benchmark_ticker, factor].values[0]

            # Compute Z-score
            z = zscore_series(factor_df[factor], baseline_value=baseline, higher_is_better=higher_is_better)

            z_scores[factor] = z
            scorecard[factor] = z

    # Calculate Final Score (Weighted Sum of Z-scores)
    # Note: We only sum factors that exist in the weights dictionary
    available_factors = [f for f in weights.keys() if f in z_scores.columns]

    if available_factors:
        # Multiply each Z-score by its weight and sum them up
        weighted_z = z_scores[available_factors].mul(pd.Series(weights))
        scorecard["Final Score"] = weighted_z.sum(axis=1)
    else:
        scorecard["Final Score"] = 0.0

    # Ranking
    scorecard["Rank"] = scorecard["Final Score"].rank(ascending=False, method="min").astype(int)
    scorecard = scorecard.sort_values("Rank")

    # Cleanup for display
    scorecard.set_index("Rank", inplace=True)
    numeric_cols = scorecard.select_dtypes(include=[np.number]).columns
    scorecard[numeric_cols] = scorecard[numeric_cols].round(2)

    return scorecard


# --------------------------
# Demo / CSV export
# --------------------------
if __name__ == "__main__":
    from etf_loader import load_etfs
    from factor_engine_v2 import compute_factors

    tickers = ["SPY", "QQQ", "EEM", "VTI"]  # All ETFs for Cost testing
    data = load_etfs(tickers, period="5y")
    factor_df = compute_factors(data)

    # 👈 TEST 1: Check raw Cost values
    print("\n=== RAW COST VALUES ===")
    print(factor_df[['Ticker', 'Cost', 'info']].head())

    # 👈 TEST 2: Check if Cost column exists and has data
    print("\n=== COST COLUMN TEST ===")
    print(f"Cost column exists: {'Cost' in factor_df.columns}")
    print(f"Non-NaN Cost values: {factor_df['Cost'].notna().sum()}")
    print(f"Cost stats:\n{factor_df['Cost'].describe()}")

    # 👈 TEST 3: Check expenseRatio from info
    print("\n=== EXPENSE RATIO RAW DATA ===")
    for ticker in tickers:
        info = factor_df[factor_df['Ticker'] == ticker]['info'].iloc[0]
        expense = info.get('expenseRatio')
        print(f"{ticker}: expenseRatio = {expense}")

    scorecard = create_scorecard(factor_df)

    print("\n=== FINAL SCORECARD ===")
    print(scorecard)
    scorecard.to_csv("scorecard.csv")
    print("\n✅ Saved scorecard to 'scorecard.csv'")