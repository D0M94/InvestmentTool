import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from etf_loader import load_etfs
from factor_engine_v2 import compute_factors
from screener_engine_v2 import create_scorecard
import numpy as np

st.title("📊 Asset Scoring & Performance Comparison")

col1, col2 = st.columns(2)
with col1:
    tickers_input = st.text_input("Enter tickers (comma-separated)", "SPY, URTH, QQQ, EEM")
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
with col2:
    benchmark_input = st.text_input("Benchmark", "SPY")
    benchmark = benchmark_input.strip().upper()

period = st.selectbox("History period", ["1y", "2y", "5y", "10y", "max"], index=2)
rf_input = st.text_input("Risk-Free Rate", "2.00%")

try:
    risk_free_rate = float(rf_input.replace("%", "")) / 100
except:
    st.error("Please enter a valid percentage, e.g., 2.00%")
    st.stop()

def highlight_benchmark(row):
    if row.name == benchmark:
        return ['background-color: #FFC39B'] * len(row)
    return [''] * len(row)

if st.button("Analyze"):
    with st.spinner("🔄 Computing scores & performance..."):
        # ✅ FIXED: Single cache call
        all_tickers = tickers + ([benchmark] if benchmark not in tickers else [])
        etf_data = load_etfs(all_tickers, period=period)
        
        # Filter for scoring only (tickers, not benchmark)
        scoring_data = {t: etf_data[t] for t in tickers if t in etf_data}
        factor_df = compute_factors(scoring_data, period=period)
        scorecard = create_scorecard(factor_df)
        
        numeric_cols = scorecard.select_dtypes(include=['number']).columns
        styled_scorecard = scorecard.style.format({col: "{:.2f}" for col in numeric_cols}).apply(highlight_benchmark, axis=1)

        st.subheader("Asset Scorecard")
        st.dataframe(styled_scorecard, use_container_width=True, hide_index=False)

        # Performance metrics (placeholder - add your performance_analyzer)
        st.subheader("Performance Metrics")
        st.info("📈 Performance analyzer integration needed")
        
        st.subheader("Cumulative Performance")
        st.info("📊 Add your performance charts here")
