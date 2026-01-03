import streamlit as st
import pandas as pd
from etf_loader import load_etfs
from factor_engine_v2 import compute_factors
from screener_engine_v2 import create_scorecard

st.title("📊 Factor Analytics")

tickers_input = st.text_input("Enter tickers (comma-separated)", "SPY, URTH, QQQ, EEM")
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

period = st.selectbox("History period", ["1y", "2y", "5y", "10y", "max"], index=2)

if st.button("Run Screener"):
    with st.spinner("Loading data..."):
        etf_data = load_etfs(tickers, period=period)  # 👈 Load data FIRST
        factor_df = compute_factors(etf_data, period=period)  # 👈 Pass data + period
        scorecard = create_scorecard(factor_df)

    st.subheader("Scorecard")
    st.dataframe(scorecard, use_container_width=True, hide_index=False)
