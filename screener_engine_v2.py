import pandas as pd
import numpy as np

# -------------------------- CONFIGURABLE WEIGHTS -------------------------- (UNCHANGED)
STOCK_WEIGHTS = {
    "Momentum": 0.2, "Value": 0.20, "Volatility": 0.2,
    "Quality": 0.20, "Growth": 0.15, "Size": 0.05
}

ETF_WEIGHTS = {
    "Momentum": 0.25, "Value": 0.25, "Volatility": 0.25,
    "Size": 0.125, "Cost": 0.125
}

# -------------------------- Z-score Helper -------------------------- (UNCHANGED)
def zscore_series(series: pd.Series, higher_is_better=True) -> pd.Series:
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

# -------------------------- Dynamic ETF/Stock Detection -------------------------- (UNCHANGED)
def detect_asset_type(info: dict) -> str:
    if not isinstance(info, dict):
        return "unknown"
    qt = info.get("quoteType", "")
    if isinstance(qt, str):
        quote_type = qt.strip().lower()
        if quote_type == "etf":
            return "etf"
    return "stock"

# -------------------------- Weighted Composite Score -------------------------- (UNCHANGED)
def compute_weighted_score(row, weights_dict):
    valid_scores = []
    total_weight = 0
    for factor, weight in weights_dict.items():
        if factor in row and not pd.isna(row[factor]):
            valid_scores.append(row[factor] * weight)
            total_weight += weight
    return np.sum(valid_scores) / total_weight if total_weight > 0 else np.nan

# -------------------------- Scorecard Computation -------------------------- (UNCHANGED)
def create_scorecard(factor_df: pd.DataFrame) -> pd.DataFrame:
    df = factor_df.copy()
    
    if "info" in df.columns:
        df["asset_type"] = df["info"].apply(detect_asset_type)
    else:
        df["asset_type"] = "stock"

    stock_factors = list(STOCK_WEIGHTS.keys())
    etf_factors = list(ETF_WEIGHTS.keys())
    
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
    
    df["CompositeScore"] = df.apply(
        lambda row: compute_weighted_score(row, STOCK_WEIGHTS if row["asset_type"] == "stock" else ETF_WEIGHTS),
        axis=1
    )
    
    df = df.sort_values("CompositeScore", ascending=False, na_position='last').reset_index(drop=True)
    df["Rank"] = df.index + 1
    
    display_rows = []
    for _, row in df.iterrows():
        row_dict = {
            "Ticker": row["Ticker"],
            "Asset type": "ETF" if row["asset_type"] == "etf" else "Stock",
            "Final Score": round(row["CompositeScore"], 2) if not pd.isna(row["CompositeScore"]) else np.nan
        }
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
