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

def safe_scalar
