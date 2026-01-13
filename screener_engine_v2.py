screener_engine_v2.py
import pandas as pd
import numpy as np

# --------------------------
# CONFIGURABLE WEIGHTS (Backend only - edit here)
# --------------------------
# All positive weights, sum to 1.0
STOCK_WEIGHTS = {
    "Momentum": 0.2,
    "Value": 0.20,
    "Volatility": 0.2,  # Positive weight, but inverted in z-score
    "Quality": 0.20,
    "Growth": 0.15,
    "Size": 0.05
}

ETF_WEIGHTS = {
    "Momentum": 0.25,
    "Value": 0.25,
    "Volatility": 0.25,  # Positive weight, inverted in z-score
    "Size": 0.125,
    "Cost": 0.125
}


# --------------------------
# Z-score Helper
# --------------------------
def zscore_series(series: pd.Series, higher_is_better=True) -> pd.Series:
    clean = series.dropna()
    mean = clean.mean()
    std = clean.std()
    if std == 0:
        z = pd.Series(0, index=series.index)
    else:
        z = (series - mean) / std
    if not higher_is_better:
        z = -z  # Invert for Volatility (lower = better)
    return z


# --------------------------
# Dynamic ETF/Stock Detection
# --------------------------
def detect_asset_type(info: dict) -> str:
    if not isinstance(info, dict):
        return "unknown"
    qt = info.get("quoteType", "")
    if isinstance(qt, str):
        quote_type = qt.strip().lower()
        if quote_type == "etf":
            return "etf"
    return "stock"


# --------------------------
# Weighted Composite Score
# --------------------------
def compute_weighted_score(row, weights_dict):
    """Compute weighted average using only available factors"""
    valid_scores = []
    total_weight = 0

    for factor, weight in weights_dict.items():
        if factor in row and not pd.isna(row[factor]):
            valid_scores.append(row[factor] * weight)
            total_weight += weight

    return np.sum(valid_scores) / total_weight if total_weight > 0 else np.nan


# --------------------------
# Scorecard Computation
# --------------------------
def create_scorecard(factor_df: pd.DataFrame) -> pd.DataFrame:
    df = factor_df.copy()

    print(f"DEBUG: Input columns: {df.columns.tolist()}")

    # Safe asset_type
    if "info" in df.columns:
        df["asset_type"] = df["info"].apply(detect_asset_type)
    else:
        df["asset_type"] = "stock"

    print(f"DEBUG: Asset types: {df['asset_type'].value_counts().to_dict()}")

    # Define factors (MOVED UP)
    stock_factors = list(STOCK_WEIGHTS.keys())
    etf_factors = list(ETF_WEIGHTS.keys())

    # Z-scores by asset type
    for asset_type in ["stock", "etf"]:
        mask = df["asset_type"] == asset_type
        if not mask.any():
            continue
        factors = stock_factors if asset_type == "stock" else etf_factors
        for col in factors:
            if col in df.columns:
                group_series = df.loc[mask, col]
                higher_better = (col != "Volatility")
                z_scores = zscore_series(group_series, higher_is_better=higher_better)
                df.loc[mask, col] = z_scores.values

    # ✅ CRITICAL: Compute CompositeScore BEFORE loop
    df["CompositeScore"] = df.apply(
        lambda row: compute_weighted_score(row, STOCK_WEIGHTS if row["asset_type"] == "stock" else ETF_WEIGHTS),
        axis=1
    )

    print(f"DEBUG: CompositeScore NaNs: {df['CompositeScore'].isna().sum()}")

    # Sort and rank
    df = df.sort_values("CompositeScore", ascending=False, na_position='last').reset_index(drop=True)
    df["Rank"] = df.index + 1

    # ✅ FIXED: Initialize display_rows
    display_rows = []
    for _, row in df.iterrows():
        row_dict = {
            "Ticker": row["Ticker"],
            "Asset type": "ETF" if row["asset_type"] == "etf" else "Stock",
            "Final Score": round(row["CompositeScore"], 2) if not pd.isna(row["CompositeScore"]) else np.nan
        }

        # Factors by type
        factors = etf_factors if row["asset_type"] == "etf" else stock_factors
        for factor in factors:
            if factor in row:
                row_dict[factor] = round(row[factor], 2) if not pd.isna(row[factor]) else ""

        display_rows.append(row_dict)

    scorecard = pd.DataFrame(display_rows)
    scorecard["Rank"] = range(1, len(scorecard) + 1)
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
