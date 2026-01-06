import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
from etf_loader import load_etfs
from factor_engine_v2 import compute_factors
from screener_engine_v2 import create_scorecard
from performance_analyzer import analyze_tickers

st.title("📊 Asset Scoring & Performance Comparison")

# **MAX 5 TICKERS LIMIT**
col1, col2 = st.columns(2)
with col1:
    tickers_input = st.text_input("Enter max 5 tickers (comma-separated)", "SPY, QQQ")
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    if len(tickers) > 5:
        st.error("❌ MAX 5 TICKERS! Too many = rate limit crash")
        st.stop()
with col2:
    benchmark = st.text_input("Benchmark", "SPY").strip().upper()

period = st.selectbox("History period", ["1y", "2y"], index=0)  # SHORT PERIODS ONLY
rf_input = st.text_input("Risk-Free Rate", "2.00%")

try:
    risk_free_rate = float(rf_input.replace("%", "")) / 100
except:
    st.error("Enter valid % (2.00%)")
    st.stop()


def highlight_benchmark(row):
    return ['background-color: #FFC39B'] * len(row) if row.name == benchmark else [''] * len(row)


if st.button("🚀 Analyze (Rate-Limit Safe)", type="primary"):
    all_tickers = list(set(tickers + [benchmark]))

    with st.spinner(f"Loading {len(all_tickers)} tickers safely..."):
        # **SINGLE CONTROLLED DATA LOAD - NO DUPLICATES**
        etf_data = {}
        for i, ticker in enumerate(all_tickers):
            st.info(f"⏳ {ticker} ({i + 1}/{len(all_tickers)})")
            time.sleep(1.5)  # CRITICAL RATE LIMIT DELAY

            try:
                single_data = load_etfs([ticker], period=period)
                etf_data[ticker] = single_data[ticker]
            except Exception as e:
                st.warning(f"❌ Failed {ticker}: {e}")

        if len(etf_data) == 0:
            st.error("No data loaded. Try SPY, QQQ")
            st.stop()

        # **FACTOR SCORING - NO EXTRA YFINANCE CALLS**
        factor_df = compute_factors(etf_data, period=period)
        scorecard = create_scorecard(factor_df)

        st.subheader("🏆 Asset Scorecard")
        numeric_cols = scorecard.select_dtypes(include=['number']).columns
        styled = scorecard.style.format({col: "{:.2f}" for col in numeric_cols}).apply(highlight_benchmark, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=False)

        # **PERFORMANCE - REUSE SAME DATA**
        cum_df, metrics = analyze_tickers(etf_data, risk_free_rate=risk_free_rate)

        st.subheader("📈 Cumulative Performance")
        fig = go.Figure()
        for t in tickers:
            if t in cum_df.columns:
                fig.add_trace(go.Scatter(x=cum_df.index, y=cum_df[t], name=t, line=dict(width=2)))
        if benchmark in cum_df.columns:
            fig.add_trace(go.Scatter(x=cum_df.index, y=cum_df[benchmark], name=f"Benchmark ({benchmark})",
                                     line=dict(width=2, dash="dash", color="#ff9900")))
        fig.update_yaxes(tickformat=".0%")
        fig.update_layout(height=500, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Performance Metrics")
        df = pd.DataFrame(metrics).T
        pct_cols = ["Total Return", "Annual Return", "Annual Volatility"]
        for col in pct_cols:
            if col in df.columns:
                df[col] = df[col] * 100

        styled_df = df.style.format({
            "Total Return": "{:.1f}%", "Annual Return": "{:.1f}%",
            "Annual Volatility": "{:.1f}%", "Sharpe Ratio": "{:.2f}"
        }).apply(highlight_benchmark, axis=1)
        st.dataframe(styled_df, use_container_width=True)

st.info("💡 Use max 5 tickers, 1y/2y periods. SPY, QQQ always work!")
