import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from performance_analyzer import analyze_tickers

st.title("📈 Performance Comparison")

col1, col2 = st.columns(2)
with col1:
    tickers_input = st.text_input("Tickers", "SPY, URTH, QQQ, EEM")
    tickers = [t.strip().upper() for t in tickers_input.split(",")]
with col2:
    benchmark_input = st.text_input("Benchmark", "SPY")
    benchmark = benchmark_input.strip().upper()

period = st.selectbox("History period", ["1y", "2y", "5y", "10y", "max"], index=2)
rf_input = st.text_input("Risk-Free Rate", "2.00%")

# Convert "2.00%" → 0.02
try:
    risk_free_rate = float(rf_input.replace("%", "")) / 100
except:
    st.error("Please enter a valid percentage, e.g., 2.00%")
    st.stop()

if st.button("Load Charts"):
    # Include benchmark in analysis
    all_tickers = list(set(tickers + [benchmark]))

    cum_df, metrics = analyze_tickers(all_tickers, period=period, risk_free_rate=risk_free_rate)

    # Chart with benchmark highlighted
    fig = go.Figure()

    # Regular tickers (solid lines)
    for t in tickers:
        if t in cum_df.columns:
            fig.add_trace(go.Scatter(
                x=cum_df.index,
                y=cum_df[t],
                mode="lines",
                name=t,
                line=dict(width=1.5)
            ))

    # Benchmark (dashed orange line)
    if benchmark in cum_df.columns:
        fig.add_trace(go.Scatter(
            x=cum_df.index,
            y=cum_df[benchmark],
            mode="lines",
            name=f"benchmark ({benchmark})",
            line=dict(width=1.5, dash="dash", color="#FFC39B")
        ))

    fig.update_yaxes(tickformat=".1%")
    fig.update_layout(height=500, template="plotly_white", title="Cumulative Performance")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Performance Metrics")
    df = pd.DataFrame(metrics).T

    # Convert % columns
    pct_cols = ["Total Return", "Annual Return", "Annual Volatility"]
    for col in pct_cols:
        if col in df.columns:
            df[col] = df[col] * 100

    # 👈 MOVE BENCHMARK TO BOTTOM
    if benchmark in df.index:
        benchmark_row = df.loc[benchmark].copy()
        main_df = df.drop(benchmark).copy()
        df = pd.concat([main_df, benchmark_row.to_frame().T])


    # Subtle peach highlight for benchmark
    def highlight_benchmark(row):
        if row.name == benchmark:
            return ['background-color: #FFC39B'] * len(row)
        return [''] * len(row)


    styled_df = df.style.format({
        "Total Return": "{:.1f}%",
        "Annual Return": "{:.1f}%",
        "Annual Volatility": "{:.1f}%",
        "Sharpe Ratio": "{:.2f}"
    }).apply(highlight_benchmark, axis=1)

    st.dataframe(styled_df, use_container_width=True)
