2_Performance_and_scoring.py:
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from etf_loader import load_etfs
from factor_engine_v2 import compute_factors
from screener_engine_v2 import create_scorecard
from performance_analyzer import analyze_tickers

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
        # SINGLE CACHED LOAD for ALL analysis (CRITICAL FIX)
        etf_data = load_etfs(tickers + ([benchmark] if benchmark not in tickers else []), period=period)

        # Scoring (tickers only)
        factor_df = compute_factors({t: etf_data[t] for t in tickers if t in etf_data}, period=period)
        scorecard = create_scorecard(factor_df)
        numeric_cols = scorecard.select_dtypes(include=['number']).columns
        styled_scorecard = scorecard.style.format({col: "{:.2f}" for col in numeric_cols}).apply(highlight_benchmark,
                                                                                                 axis=1)

        st.subheader("Asset Scorecard")
        st.dataframe(styled_scorecard, use_container_width=True, hide_index=False)

        # Performance (all tickers + benchmark)
        all_tickers = list(set(tickers + [benchmark]))
        cum_df, metrics = analyze_tickers(all_tickers, period=period, risk_free_rate=risk_free_rate)

        st.subheader("Cumulative Performance")
        fig = go.Figure()
        for t in tickers:
            if t in cum_df.columns:
                fig.add_trace(go.Scatter(
                    x=cum_df.index, y=cum_df[t],
                    mode="lines", name=t,
                    line=dict(width=1.5)
                ))
        if benchmark in cum_df.columns:
            fig.add_trace(go.Scatter(
                x=cum_df.index, y=cum_df[benchmark],
                mode="lines", name=f"benchmark ({benchmark})",
                line=dict(width=1.5, dash="dash", color="#FFC39B")
            ))
        fig.update_yaxes(tickformat=".1%")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Performance Metrics")
        df = pd.DataFrame(metrics).T
        pct_cols = ["Total Return", "Annual Return", "Annual Volatility"]
        for col in pct_cols:
            if col in df.columns:
                df[col] = df[col] * 100

        if benchmark in df.index:
            benchmark_row = df.loc[benchmark].copy()
            main_df = df.drop(benchmark).copy()
            df = pd.concat([main_df, benchmark_row.to_frame().T])

        styled_df = df.style.format({
            "Total Return": "{:.1f}%",
            "Annual Return": "{:.1f}%",
            "Annual Volatility": "{:.1f}%",
            "Sharpe Ratio": "{:.2f}"
        }).apply(highlight_benchmark, axis=1)
        st.dataframe(styled_df, use_container_width=True)
